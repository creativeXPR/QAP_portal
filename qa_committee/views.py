from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    CommitteeMeeting,
    CommitteeMeetingAttendance,
    QAActionEvidence,
    QAActionPlan,
    QAAuditCycle,
    QAAuditFinding,
    QACommittee,
    QACommitteeDataReview,
    QACommitteeMember,
    QACommitteeReport,
    QARecommendation,
)
from .permissions import EvidenceVerificationPermission, QACommitteePermission
from .serializers import (
    AttendanceBulkSerializer,
    CommitteeMeetingAttendanceSerializer,
    CommitteeMeetingSerializer,
    QAActionEvidenceSerializer,
    QAActionPlanSerializer,
    QAAuditCycleSerializer,
    QAAuditFindingSerializer,
    QACommitteeDataReviewSerializer,
    QACommitteeMemberSerializer,
    QACommitteeReportSerializer,
    QACommitteeSerializer,
    QARecommendationSerializer,
    WorkflowCommentSerializer,
    mark_report_submitted,
)
from .services import (
    get_action_plan_completion_rate,
    get_activity_feed,
    get_committee_dashboard,
    get_committee_effectiveness_score,
    get_committee_summary,
    get_open_findings,
    get_overdue_recommendations,
    get_risk_summary_by_department,
    get_risk_summary_by_faculty,
)


class QACommitteeViewSet(viewsets.ModelViewSet):
    queryset = QACommittee.objects.select_related("faculty", "department", "created_by").prefetch_related("members")
    serializer_class = QACommitteeSerializer
    permission_classes = [QACommitteePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["scope_type", "faculty", "department", "programme", "status"]
    search_fields = ["name", "description", "programme", "faculty__name", "department__name"]
    ordering_fields = ["name", "date_constituted", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["get", "post"])
    def members(self, request, pk=None):
        committee = self.get_object()
        if request.method == "GET":
            serializer = QACommitteeMemberSerializer(committee.members.select_related("user", "committee"), many=True)
            return Response(serializer.data)
        serializer = QACommitteeMemberSerializer(data={**request.data, "committee": committee.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def dashboard(self, request, pk=None):
        return Response(get_committee_dashboard(self.get_object()))


class QACommitteeMemberViewSet(viewsets.ModelViewSet):
    queryset = QACommitteeMember.objects.select_related("committee", "user")
    serializer_class = QACommitteeMemberSerializer
    permission_classes = [QACommitteePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["committee", "role", "is_active"]
    search_fields = ["user__username", "user__email", "designation", "committee__name"]


class CommitteeMeetingViewSet(viewsets.ModelViewSet):
    queryset = CommitteeMeeting.objects.select_related("committee", "created_by").prefetch_related("attendance")
    serializer_class = CommitteeMeetingSerializer
    permission_classes = [QACommitteePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["committee", "meeting_type", "status"]
    search_fields = ["title", "agenda", "minutes", "committee__name"]
    ordering_fields = ["scheduled_date", "held_date", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark-held")
    def mark_held(self, request, pk=None):
        serializer = WorkflowCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meeting = self.get_object()
        meeting.mark_held(serializer.validated_data.get("held_date"))
        return Response(self.get_serializer(meeting).data)

    @action(detail=True, methods=["post"])
    def attendance(self, request, pk=None):
        meeting = self.get_object()
        serializer = AttendanceBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        records = serializer.save(meeting)
        return Response(CommitteeMeetingAttendanceSerializer(records, many=True).data)


class CommitteeMeetingAttendanceViewSet(viewsets.ModelViewSet):
    queryset = CommitteeMeetingAttendance.objects.select_related("meeting", "member", "member__user")
    serializer_class = CommitteeMeetingAttendanceSerializer
    permission_classes = [QACommitteePermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["meeting", "member", "attendance_status"]


class QAAuditCycleViewSet(viewsets.ModelViewSet):
    queryset = QAAuditCycle.objects.select_related("committee", "target_faculty", "target_department", "created_by")
    serializer_class = QAAuditCycleSerializer
    permission_classes = [QACommitteePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["committee", "audit_type", "target_faculty", "target_department", "target_programme", "status"]
    search_fields = ["title", "target_programme", "committee__name"]
    ordering_fields = ["review_period_start", "review_period_end", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        cycle = self.get_object()
        cycle.status = QAAuditCycle.Status.SUBMITTED
        cycle.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(cycle).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        cycle = self.get_object()
        cycle.status = QAAuditCycle.Status.CLOSED
        cycle.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(cycle).data)


class QAAuditFindingViewSet(viewsets.ModelViewSet):
    queryset = QAAuditFinding.objects.select_related("audit_cycle", "created_by", "audit_cycle__committee")
    serializer_class = QAAuditFindingSerializer
    permission_classes = [QACommitteePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["audit_cycle", "source_module", "category", "severity", "risk_level", "status"]
    search_fields = ["finding_code", "title", "description", "source_record_type", "source_record_id"]
    ordering_fields = ["created_at", "severity", "risk_level"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        finding = self.get_object()
        finding.status = QAAuditFinding.Status.RESOLVED
        finding.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(finding).data)

    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        finding = self.get_object()
        finding.status = QAAuditFinding.Status.DISMISSED
        finding.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(finding).data)


class QARecommendationViewSet(viewsets.ModelViewSet):
    queryset = QARecommendation.objects.select_related("finding", "audit_cycle", "responsible_faculty", "responsible_department", "assigned_to", "created_by")
    serializer_class = QARecommendationSerializer
    permission_classes = [QACommitteePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["audit_cycle", "finding", "priority", "status", "responsible_faculty", "responsible_department", "assigned_to"]
    search_fields = ["title", "recommendation_text"]
    ordering_fields = ["due_date", "priority", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def _set_status(self, status_value):
        recommendation = self.get_object()
        recommendation.status = status_value
        recommendation.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(recommendation).data)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        return self._set_status(QARecommendation.Status.ACCEPTED)

    @action(detail=True, methods=["post"], url_path="mark-in-progress")
    def mark_in_progress(self, request, pk=None):
        return self._set_status(QARecommendation.Status.IN_PROGRESS)

    @action(detail=True, methods=["post"], url_path="mark-implemented")
    def mark_implemented(self, request, pk=None):
        return self._set_status(QARecommendation.Status.IMPLEMENTED)

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        return self._set_status(QARecommendation.Status.VERIFIED)


class QAActionPlanViewSet(viewsets.ModelViewSet):
    queryset = QAActionPlan.objects.select_related("recommendation", "owner")
    serializer_class = QAActionPlanSerializer
    permission_classes = [QACommitteePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["recommendation", "owner", "status"]
    search_fields = ["action_description", "implementation_notes", "recommendation__title"]
    ordering_fields = ["expected_completion_date", "progress_percentage", "created_at"]

    @action(detail=True, methods=["post"], url_path="submit-evidence")
    def submit_evidence(self, request, pk=None):
        action_plan = self.get_object()
        data = request.data.copy()
        data["action_plan"] = action_plan.id
        serializer = QAActionEvidenceSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(uploaded_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QAActionEvidenceViewSet(viewsets.ModelViewSet):
    queryset = QAActionEvidence.objects.select_related("action_plan", "uploaded_by", "verified_by")
    serializer_class = QAActionEvidenceSerializer
    permission_classes = [QACommitteePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["action_plan", "verification_status", "uploaded_by"]
    search_fields = ["title", "description", "external_url"]
    ordering_fields = ["created_at", "verification_status"]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[EvidenceVerificationPermission])
    def verify(self, request, pk=None):
        evidence = self.get_object()
        evidence.verification_status = QAActionEvidence.VerificationStatus.ACCEPTED
        evidence.verified_by = request.user
        evidence.verification_comment = request.data.get("verification_comment", "")
        evidence.save(update_fields=["verification_status", "verified_by", "verification_comment", "updated_at"])
        return Response(self.get_serializer(evidence).data)

    @action(detail=True, methods=["post"], permission_classes=[EvidenceVerificationPermission])
    def reject(self, request, pk=None):
        evidence = self.get_object()
        evidence.verification_status = QAActionEvidence.VerificationStatus.REJECTED
        evidence.verified_by = request.user
        evidence.verification_comment = request.data.get("verification_comment", "")
        evidence.save(update_fields=["verification_status", "verified_by", "verification_comment", "updated_at"])
        return Response(self.get_serializer(evidence).data)


class QACommitteeReportViewSet(viewsets.ModelViewSet):
    queryset = QACommitteeReport.objects.select_related("committee", "audit_cycle", "submitted_by", "reviewed_by")
    serializer_class = QACommitteeReportSerializer
    permission_classes = [QACommitteePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["committee", "audit_cycle", "report_type", "status"]
    search_fields = ["summary", "key_findings", "recommendations_summary", "action_plan_summary"]
    ordering_fields = ["reporting_period_start", "reporting_period_end", "created_at"]

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        report = mark_report_submitted(self.get_object(), request.user)
        report.qacei_score = get_committee_effectiveness_score(report.committee, report.reporting_period_start, report.reporting_period_end)
        report.save(update_fields=["qacei_score", "updated_at"])
        return Response(self.get_serializer(report).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        report = self.get_object()
        report.status = QACommitteeReport.Status.APPROVED
        report.reviewed_by = request.user
        report.reviewed_at = timezone.now()
        report.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])
        return Response(self.get_serializer(report).data)


class QACommitteeDataReviewViewSet(viewsets.ModelViewSet):
    queryset = QACommitteeDataReview.objects.select_related("committee", "target_faculty", "target_department", "reviewer")
    serializer_class = QACommitteeDataReviewSerializer
    permission_classes = [QACommitteePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["committee", "source_module", "target_faculty", "target_department", "validation_status"]
    search_fields = ["review_title", "source_module", "source_endpoint_or_model", "reviewer_comment"]
    ordering_fields = ["review_period_start", "review_period_end", "created_at"]

    @action(detail=True, methods=["post"])
    def validate(self, request, pk=None):
        review = self.get_object()
        review.validation_status = QACommitteeDataReview.ValidationStatus.VALID
        review.reviewer = request.user
        review.reviewer_comment = request.data.get("reviewer_comment", "")
        review.save(update_fields=["validation_status", "reviewer", "reviewer_comment", "updated_at"])
        return Response(self.get_serializer(review).data)

    @action(detail=True, methods=["post"])
    def flag(self, request, pk=None):
        review = self.get_object()
        review.validation_status = QACommitteeDataReview.ValidationStatus.QUESTIONABLE
        review.reviewer = request.user
        review.reviewer_comment = request.data.get("reviewer_comment", "")
        review.save(update_fields=["validation_status", "reviewer", "reviewer_comment", "updated_at"])
        return Response(self.get_serializer(review).data)


class SummaryView(APIView):
    permission_classes = [QACommitteePermission]

    def get(self, request):
        return Response(get_committee_summary())


class EffectivenessView(APIView):
    permission_classes = [QACommitteePermission]

    def get(self, request):
        data = [
            {"committee": committee.name, "committee_id": committee.id, "qacei_score": get_committee_effectiveness_score(committee)}
            for committee in QACommittee.objects.all()
        ]
        return Response(data)


class OverdueActionsView(APIView):
    permission_classes = [QACommitteePermission]

    def get(self, request):
        return Response(QARecommendationSerializer(get_overdue_recommendations(), many=True).data)


class RiskSummaryView(APIView):
    permission_classes = [QACommitteePermission]

    def get(self, request):
        return Response({"by_department": get_risk_summary_by_department(), "by_faculty": get_risk_summary_by_faculty()})


class ActivityFeedView(APIView):
    permission_classes = [QACommitteePermission]

    def get(self, request):
        limit = request.query_params.get("limit", 20)
        try:
            limit = min(max(int(limit), 1), 100)
        except (TypeError, ValueError):
            limit = 20
        return Response(get_activity_feed(limit))
