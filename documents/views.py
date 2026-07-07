from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import (
    InstitutionalDocument,
    InstitutionalDocumentAccessLog,
    InstitutionalDocumentCategory,
    InstitutionalDocumentVersion,
)
from .permissions import InstitutionalDocumentPermission, can_review, can_view_document
from .serializers import (
    CategorySerializer,
    DocumentAccessLogSerializer,
    DocumentSerializer,
    NewVersionSerializer,
    ReviewActionSerializer,
    VersionSerializer,
)
from .services import (
    access_response,
    approve_document,
    archive_document,
    ensure_default_categories,
    publish_document,
    reject_document,
    submit_for_review,
)


class DocumentPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ApiResponseMixin:
    def success(self, data=None, message="Request completed successfully.", status_code=status.HTTP_200_OK):
        return Response({"success": True, "message": message, "data": data or {}}, status=status_code)

    def error(self, errors, message="Validation failed.", status_code=status.HTTP_400_BAD_REQUEST):
        return Response({"success": False, "message": message, "errors": errors}, status=status_code)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset) if hasattr(self, "paginate_queryset") else None
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginator = self.paginator
            return Response(
                {
                    "success": True,
                    "message": "Request completed successfully.",
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


class CategoryViewSet(ApiResponseMixin, viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [InstitutionalDocumentPermission]
    pagination_class = DocumentPagination

    def get_queryset(self):
        ensure_default_categories()
        queryset = InstitutionalDocumentCategory.objects.all()
        is_active = self.request.query_params.get("is_active")
        if is_active in {"true", "false"}:
            queryset = queryset.filter(is_active=is_active == "true")
        return queryset

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        category.is_active = False
        category.save(update_fields=["is_active", "updated_at"])
        return self.success(self.get_serializer(category).data, "Category deactivated.")


class DocumentViewSet(ApiResponseMixin, viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [InstitutionalDocumentPermission]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    pagination_class = DocumentPagination

    def get_queryset(self):
        ensure_default_categories()
        queryset = InstitutionalDocument.objects.select_related("category", "current_version").prefetch_related("tags")
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status="published", visibility_level="public")
        else:
            queryset = [document for document in queryset if can_view_document(self.request.user, document)]
            ids = [document.id for document in queryset]
            queryset = InstitutionalDocument.objects.filter(id__in=ids).select_related("category", "current_version").prefetch_related("tags")
        return self.apply_filters(queryset)

    def apply_filters(self, queryset):
        params = self.request.query_params
        search = params.get("search")
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search) | Q(tags__name__icontains=search)).distinct()
        mappings = {
            "category": "category_id",
            "document_type": "document_type",
            "related_module": "related_module",
            "visibility_level": "visibility_level",
            "status": "status",
            "is_latest": "is_latest",
            "uploaded_by": "uploaded_by_id",
            "approved_by": "approved_by_id",
        }
        for query_param, lookup in mappings.items():
            value = params.get(query_param)
            if value:
                if query_param == "is_latest":
                    value = value.lower() == "true"
                queryset = queryset.filter(**{lookup: value})
        ranges = [
            ("effective_date_from", "effective_date__gte"),
            ("effective_date_to", "effective_date__lte"),
            ("review_date_from", "review_date__gte"),
            ("review_date_to", "review_date__lte"),
            ("created_at_from", "created_at__date__gte"),
            ("created_at_to", "created_at__date__lte"),
        ]
        for query_param, lookup in ranges:
            value = params.get(query_param)
            if value:
                queryset = queryset.filter(**{lookup: value})
        return queryset

    def destroy(self, request, *args, **kwargs):
        document = archive_document(self.get_object())
        return self.success(self.get_serializer(document).data, "Document archived.")

    def _workflow(self, func, message, request):
        document = self.get_object()
        serializer = ReviewActionSerializer(data=request.data)
        if not serializer.is_valid():
            return self.error(serializer.errors)
        try:
            document = func(document, request.user, serializer.validated_data.get("comment", ""))
        except ValidationError as exc:
            return self.error({"detail": [str(exc)]})
        return self.success(self.get_serializer(document).data, message)

    @action(detail=True, methods=["post"], url_path="submit-for-review")
    def submit_for_review(self, request, pk=None):
        try:
            document = submit_for_review(self.get_object())
        except ValidationError as exc:
            return self.error({"detail": [str(exc)]})
        return self.success(self.get_serializer(document).data, "Document submitted for review.")

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._workflow(approve_document, "Document approved.", request)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._workflow(reject_document, "Document rejected.", request)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        document = self.get_object()
        try:
            document = publish_document(document, request.user)
        except ValidationError as exc:
            return self.error({"detail": [str(exc)]})
        return self.success(self.get_serializer(document).data, "Document published.")

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        document = archive_document(self.get_object())
        return self.success(self.get_serializer(document).data, "Document archived.")

    @action(detail=True, methods=["post"], url_path="new-version")
    def new_version(self, request, pk=None):
        document = self.get_object()
        serializer = NewVersionSerializer(data=request.data, context={"request": request, "document": document})
        if not serializer.is_valid():
            return self.error(serializer.errors)
        version = serializer.save()
        return self.success(VersionSerializer(version).data, "New version uploaded.", status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        try:
            return access_response(request, self.get_object(), "previewed")
        except ValidationError as exc:
            return self.error({"detail": [str(exc)]})

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        try:
            return access_response(request, self.get_object(), "downloaded")
        except ValidationError as exc:
            return self.error({"detail": [str(exc)]})

    @action(detail=True, methods=["get"])
    def versions(self, request, pk=None):
        versions = self.get_object().versions.all()
        return self.success(VersionSerializer(versions, many=True).data)


class VersionViewSet(ApiResponseMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = VersionSerializer
    permission_classes = [InstitutionalDocumentPermission]
    pagination_class = DocumentPagination

    def get_queryset(self):
        queryset = InstitutionalDocumentVersion.objects.select_related("document")
        visible_ids = [
            version.id
            for version in queryset
            if can_view_document(self.request.user, version.document)
        ]
        return InstitutionalDocumentVersion.objects.filter(id__in=visible_ids).select_related("document")


class AccessLogViewSet(ApiResponseMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = DocumentAccessLogSerializer
    permission_classes = [InstitutionalDocumentPermission]
    pagination_class = DocumentPagination

    def get_queryset(self):
        queryset = InstitutionalDocumentAccessLog.objects.select_related("document", "version", "user")
        if can_review(self.request.user):
            return queryset
        if getattr(self.request.user, "is_authenticated", False):
            return queryset.filter(user=self.request.user)
        return queryset.none()
