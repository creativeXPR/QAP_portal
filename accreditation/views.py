from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AccreditationComponent,
    AccreditationCycle,
    AccreditationMetric,
    CorrectiveAction,
    EarlyWarningAlert,
    Evidence,
    MetricSubmission,
)
from .permissions import AccreditationPermission
from .serializers import (
    AccreditationComponentSerializer,
    AccreditationCycleSerializer,
    AccreditationMetricSerializer,
    BulkSubmissionSerializer,
    CorrectiveActionProgressSerializer,
    CorrectiveActionSerializer,
    EarlyWarningAlertSerializer,
    EvidenceSerializer,
    MetricSubmissionSerializer,
    ReviewerCommentSerializer,
)
from .services import calculate_component_scores, calculate_pari, ensure_default_components_and_metrics


class ApiResponseMixin:
    success_message = "Request completed successfully."

    def success(self, data=None, message=None, status_code=status.HTTP_200_OK):
        return Response({"success": True, "message": message or self.success_message, "data": data or {}}, status=status_code)

    def error(self, errors, message="Validation failed.", status_code=status.HTTP_400_BAD_REQUEST):
        return Response({"success": False, "message": message, "errors": errors}, status=status_code)


class AccreditationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class WrappedModelViewSet(ApiResponseMixin, viewsets.ModelViewSet):
    permission_classes = [AccreditationPermission]
    pagination_class = AccreditationPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginator = self.paginator
            return Response(
                {
                    "success": True,
                    "message": self.success_message,
                    "data": serializer.data,
                    "pagination": {
                        "count": paginator.page.paginator.count,
                        "next": paginator.get_next_link(),
                        "previous": paginator.get_previous_link(),
                    },
                }
            )
        serializer = self.get_serializer(queryset, many=True)
        return self.success(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return self.success(self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error(serializer.errors)
        self.perform_create(serializer)
        return self.success(serializer.data, "Created successfully.", status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=partial)
        if not serializer.is_valid():
            return self.error(serializer.errors)
        self.perform_update(serializer)
        return self.success(serializer.data, "Updated successfully.")

    def destroy(self, request, *args, **kwargs):
        self.perform_destroy(self.get_object())
        return self.success({}, "Deleted successfully.")


def apply_common_filters(queryset, request):
    filters = {
        "cycle": "cycle_id",
        "programme": "programme",
        "faculty": "cycle__faculty",
        "department": "cycle__department",
        "status": "status",
        "component": "component__code",
        "reporting_period": "reporting_period",
        "risk_classification": "classification",
    }
    for query_param, lookup in filters.items():
        value = request.query_params.get(query_param)
        if value:
            queryset = queryset.filter(**{lookup: value})
    date_from = request.query_params.get("date_from")
    date_to = request.query_params.get("date_to")
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)
    return queryset


class AccreditationCycleViewSet(WrappedModelViewSet):
    queryset = AccreditationCycle.objects.all()
    serializer_class = AccreditationCycleSerializer

    def get_queryset(self):
        return apply_common_filters(super().get_queryset(), self.request)

    @action(detail=True, methods=["patch"])
    def close(self, request, pk=None):
        cycle = self.get_object()
        cycle.close()
        return self.success(self.get_serializer(cycle).data, "Accreditation cycle closed.")


class AccreditationComponentViewSet(WrappedModelViewSet):
    serializer_class = AccreditationComponentSerializer

    def get_queryset(self):
        ensure_default_components_and_metrics()
        queryset = AccreditationComponent.objects.all()
        value = self.request.query_params.get("is_active")
        if value in {"true", "false"}:
            queryset = queryset.filter(is_active=value == "true")
        return queryset


class AccreditationMetricViewSet(WrappedModelViewSet):
    serializer_class = AccreditationMetricSerializer

    def get_queryset(self):
        ensure_default_components_and_metrics()
        queryset = AccreditationMetric.objects.select_related("component")
        component = self.request.query_params.get("component")
        if component:
            queryset = queryset.filter(component__code=component)
        return queryset


class MetricSubmissionViewSet(WrappedModelViewSet):
    serializer_class = MetricSubmissionSerializer

    def get_queryset(self):
        return apply_common_filters(MetricSubmission.objects.select_related("cycle", "component", "metric"), self.request)

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)


class BulkSubmissionView(ApiResponseMixin, APIView):
    permission_classes = [AccreditationPermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        serializer = BulkSubmissionSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return self.error(serializer.errors)
        submissions = serializer.save()
        data = MetricSubmissionSerializer(submissions, many=True, context={"request": request}).data
        return self.success(data, "Submission saved successfully.", status.HTTP_201_CREATED)


class EvidenceViewSet(WrappedModelViewSet):
    serializer_class = EvidenceSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        return apply_common_filters(Evidence.objects.select_related("cycle", "component", "metric", "submission"), self.request)

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=["patch"])
    def verify(self, request, pk=None):
        evidence = self.get_object()
        serializer = ReviewerCommentSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error(serializer.errors)
        evidence = serializer.apply_evidence_status(evidence, "verified")
        return self.success(self.get_serializer(evidence).data, "Evidence verified.")

    @action(detail=True, methods=["patch"])
    def reject(self, request, pk=None):
        evidence = self.get_object()
        serializer = ReviewerCommentSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error(serializer.errors)
        evidence = serializer.apply_evidence_status(evidence, "rejected")
        return self.success(self.get_serializer(evidence).data, "Evidence rejected.")


class CalculateComponentScoresView(ApiResponseMixin, APIView):
    permission_classes = [AccreditationPermission]

    def post(self, request, cycle_id, programme_id):
        try:
            cycle = AccreditationCycle.objects.get(pk=cycle_id)
        except AccreditationCycle.DoesNotExist:
            return self.error({"cycle": ["Cycle does not exist."]}, status_code=status.HTTP_404_NOT_FOUND)
        scores = calculate_component_scores(cycle, programme_id, user=request.user)
        return self.success({"programme": str(programme_id), "cycle": cycle.id, "scores": scores}, "Component scores calculated.")


class CalculatePARIView(ApiResponseMixin, APIView):
    permission_classes = [AccreditationPermission]

    def post(self, request, cycle_id, programme_id):
        try:
            cycle = AccreditationCycle.objects.get(pk=cycle_id)
        except AccreditationCycle.DoesNotExist:
            return self.error({"cycle": ["Cycle does not exist."]}, status_code=status.HTTP_404_NOT_FOUND)
        return self.success(calculate_pari(cycle, programme_id, user=request.user), "PARI calculated.")


class EarlyWarningAlertViewSet(WrappedModelViewSet):
    serializer_class = EarlyWarningAlertSerializer

    def get_queryset(self):
        return apply_common_filters(EarlyWarningAlert.objects.select_related("cycle", "component"), self.request)

    def _set_status(self, request, status_value, message):
        alert = self.get_object()
        alert.status = status_value
        if status_value == "resolved":
            alert.resolved_at = timezone.now()
        alert.save()
        return self.success(self.get_serializer(alert).data, message)

    @action(detail=True, methods=["patch"])
    def acknowledge(self, request, pk=None):
        return self._set_status(request, "acknowledged", "Alert acknowledged.")

    @action(detail=True, methods=["patch"])
    def resolve(self, request, pk=None):
        return self._set_status(request, "resolved", "Alert resolved.")

    @action(detail=True, methods=["patch"])
    def escalate(self, request, pk=None):
        return self._set_status(request, "escalated", "Alert escalated.")


class CorrectiveActionViewSet(WrappedModelViewSet):
    serializer_class = CorrectiveActionSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        return apply_common_filters(CorrectiveAction.objects.select_related("cycle", "component", "alert"), self.request)

    @action(detail=True, methods=["patch"])
    def progress(self, request, pk=None):
        action_obj = self.get_object()
        serializer = CorrectiveActionProgressSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error(serializer.errors)
        action_obj.progress_percentage = serializer.validated_data["progress_percentage"]
        if serializer.validated_data.get("reviewer_comment"):
            action_obj.reviewer_comment = serializer.validated_data["reviewer_comment"]
        action_obj.status = "in_progress"
        action_obj.save()
        return self.success(self.get_serializer(action_obj).data, "Corrective action progress updated.")

    def _status_action(self, request, status_value, message):
        action_obj = self.get_object()
        serializer = ReviewerCommentSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error(serializer.errors)
        action_obj = serializer.apply_action_status(action_obj, status_value, user=request.user)
        return self.success(self.get_serializer(action_obj).data, message)

    @action(detail=True, methods=["patch"])
    def submit(self, request, pk=None):
        return self._status_action(request, "submitted_for_validation", "Corrective action submitted.")

    @action(detail=True, methods=["patch"])
    def verify(self, request, pk=None):
        return self._status_action(request, "verified", "Corrective action verified.")

    @action(detail=True, methods=["patch"])
    def reject(self, request, pk=None):
        return self._status_action(request, "rejected", "Corrective action rejected.")

    @action(detail=True, methods=["patch"])
    def close(self, request, pk=None):
        return self._status_action(request, "closed", "Corrective action closed.")
