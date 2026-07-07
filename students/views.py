from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from .models import Student, StudentFeedback
from .permissions import MANAGER_ROLES, StudentFeedbackPermission, StudentRecordPermission, role_for
from .serializers import StudentFeedbackSerializer, StudentSerializer


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
    filterset_fields = ["category", "status", "urgency", "submitted_by"]
    search_fields = ["student_name", "feedback_text", "submitted_by__username"]
    ordering_fields = ["submitted_at", "urgency", "status"]
    ordering = ["-submitted_at"]

    def get_queryset(self):
        queryset = StudentFeedback.objects.select_related("submitted_by").all()
        if role_for(self.request.user) in MANAGER_ROLES:
            return queryset
        return queryset.filter(submitted_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)
