from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Staff, StaffFeedback, StaffFeedbackUpdate, StaffNotification
from .permissions import MANAGER_ROLES, StaffFeedbackPermission, StaffRecordPermission, role_for
from .serializers import StaffFeedbackSerializer, StaffNotificationSerializer, StaffSerializer


def complaint_update_message(complaint, changed_fields):
    status_label = complaint.get_status_display()
    if complaint.status == StaffFeedback.Status.RESOLVED:
        return "Your complaint has been resolved."
    if complaint.status == StaffFeedback.Status.UNDER_REVIEW:
        return "Your complaint has been closed."
    if "admin_comment" in changed_fields and "status" not in changed_fields:
        return "The administrator has responded to your complaint."
    if "assigned_to" in changed_fields and "status" not in changed_fields:
        return "Your complaint has been reassigned for review."
    return f"Your complaint is now {status_label}."


class StaffViewSet(viewsets.ModelViewSet):
    serializer_class = StaffSerializer
    permission_classes = [StaffRecordPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["faculty", "department", "role", "status", "courses"]
    search_fields = [
        "staff_id",
        "first_name",
        "last_name",
        "email",
        "role",
        "faculty__name",
        "department__name",
        "courses__code",
        "courses__title",
    ]
    ordering_fields = ["staff_id", "first_name", "last_name", "role", "created_at"]
    ordering = ["staff_id"]

    def get_queryset(self):
        queryset = (
            Staff.objects.select_related("user", "faculty", "department")
            .prefetch_related("courses")
            .all()
        )
        if role_for(self.request.user) in MANAGER_ROLES:
            return queryset
        return queryset.filter(user=self.request.user)


class StaffFeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = StaffFeedbackSerializer
    permission_classes = [StaffFeedbackPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "classification", "status", "urgency", "submitted_by", "assigned_to"]
    search_fields = ["staff_name", "feedback_text", "admin_comment", "submitted_by__username", "assigned_to__username"]
    ordering_fields = ["submitted_at", "updated_at", "urgency", "status"]
    ordering = ["-submitted_at"]

    def get_queryset(self):
        queryset = (
            StaffFeedback.objects.select_related("submitted_by", "assigned_to", "updated_by")
            .prefetch_related("updates", "notifications")
            .all()
        )
        if role_for(self.request.user) in MANAGER_ROLES:
            return queryset
        return queryset.filter(submitted_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user, status=StaffFeedback.Status.PENDING)

    def perform_update(self, serializer):
        complaint = self.get_object()
        previous_status = complaint.status
        previous_comment = complaint.admin_comment
        previous_assigned_to_id = complaint.assigned_to_id

        updated = serializer.save(updated_by=self.request.user)
        changed_fields = set()
        if previous_status != updated.status:
            changed_fields.add("status")
        if previous_comment != updated.admin_comment and updated.admin_comment:
            changed_fields.add("admin_comment")
        if previous_assigned_to_id != updated.assigned_to_id:
            changed_fields.add("assigned_to")

        if changed_fields and updated.submitted_by_id:
            StaffFeedbackUpdate.objects.create(
                complaint=updated,
                previous_status=previous_status,
                new_status=updated.status,
                admin_comment=updated.admin_comment if "admin_comment" in changed_fields else "",
                assigned_to=updated.assigned_to if "assigned_to" in changed_fields else None,
                updated_by=self.request.user,
            )
            StaffNotification.objects.create(
                user=updated.submitted_by,
                complaint=updated,
                title="Complaint Updated",
                message=complaint_update_message(updated, changed_fields),
                notification_type=StaffNotification.NotificationType.COMPLAINT_UPDATE,
            )


class StaffNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StaffNotificationSerializer
    permission_classes = [StaffFeedbackPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["notification_type", "is_read", "complaint"]
    search_fields = ["title", "message", "complaint__staff_name", "complaint__feedback_text"]
    ordering_fields = ["created_at", "is_read"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = StaffNotification.objects.select_related("user", "complaint").all()
        if role_for(self.request.user) in MANAGER_ROLES:
            return queryset
        return queryset.filter(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(self.get_serializer(notification).data, status=status.HTTP_200_OK)
