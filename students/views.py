from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Student, StudentFeedback, StudentFeedbackUpdate, StudentNotification
from .permissions import MANAGER_ROLES, StudentFeedbackPermission, StudentRecordPermission, role_for
from .serializers import StudentFeedbackSerializer, StudentNotificationSerializer, StudentSerializer


def complaint_update_message(complaint, changed_fields):
    status_label = complaint.get_status_display()
    if complaint.status == StudentFeedback.Status.RESOLVED:
        return "Your complaint has been resolved."
    if complaint.status == StudentFeedback.Status.CLOSED:
        return "Your complaint has been closed."
    if "admin_comment" in changed_fields and "status" not in changed_fields:
        return "The administrator has responded to your complaint."
    if "assigned_to" in changed_fields and "status" not in changed_fields:
        return "Your complaint has been reassigned for review."
    return f"Your complaint is now {status_label}."


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [StudentRecordPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["faculty", "department", "level", "status", "courses"]
    search_fields = [
        "matric_number",
        "first_name",
        "last_name",
        "email",
        "programme",
        "faculty__name",
        "department__name",
        "courses__code",
        "courses__title",
    ]
    ordering_fields = ["matric_number", "first_name", "last_name", "level", "created_at"]
    ordering = ["matric_number"]

    def get_queryset(self):
        queryset = (
            Student.objects.select_related("user", "faculty", "department")
            .prefetch_related("courses")
            .all()
        )
        if role_for(self.request.user) in MANAGER_ROLES:
            return queryset
        return queryset.filter(user=self.request.user)


class StudentFeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = StudentFeedbackSerializer
    permission_classes = [StudentFeedbackPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "classification", "status", "urgency", "submitted_by", "assigned_to"]
    search_fields = ["student_name", "feedback_text", "admin_comment", "submitted_by__username", "assigned_to__username"]
    ordering_fields = ["submitted_at", "updated_at", "urgency", "status"]
    ordering = ["-submitted_at"]

    def get_queryset(self):
        queryset = (
            StudentFeedback.objects.select_related("submitted_by", "assigned_to", "updated_by")
            .prefetch_related("updates", "notifications")
            .all()
        )
        if role_for(self.request.user) in MANAGER_ROLES:
            return queryset
        return queryset.filter(submitted_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user, status=StudentFeedback.Status.PENDING)

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
            StudentFeedbackUpdate.objects.create(
                complaint=updated,
                previous_status=previous_status,
                new_status=updated.status,
                admin_comment=updated.admin_comment if "admin_comment" in changed_fields else "",
                assigned_to=updated.assigned_to if "assigned_to" in changed_fields else None,
                updated_by=self.request.user,
            )
            StudentNotification.objects.create(
                user=updated.submitted_by,
                complaint=updated,
                title="Complaint Updated",
                message=complaint_update_message(updated, changed_fields),
                notification_type=StudentNotification.NotificationType.COMPLAINT_UPDATE,
            )


class StudentNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StudentNotificationSerializer
    permission_classes = [StudentFeedbackPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["notification_type", "is_read", "complaint"]
    search_fields = ["title", "message", "complaint__student_name", "complaint__feedback_text"]
    ordering_fields = ["created_at", "is_read"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = StudentNotification.objects.select_related("user", "complaint").all()
        if role_for(self.request.user) in MANAGER_ROLES:
            return queryset
        return queryset.filter(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(self.get_serializer(notification).data, status=status.HTTP_200_OK)
