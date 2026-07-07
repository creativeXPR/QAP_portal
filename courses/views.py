from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course, LectureSession
from .serializers import CourseSerializer, LectureSessionSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.select_related("department").all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["code", "title"]


class LectureSessionViewSet(viewsets.ModelViewSet):
    queryset = LectureSession.objects.select_related(
        "course", "course__department", "course__department__faculty", "respondent"
    ).all()
    serializer_class = LectureSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["held", "mode", "level", "course", "monitored_at"]
    search_fields = ["course__code", "venue"]