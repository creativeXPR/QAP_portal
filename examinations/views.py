from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import ExamSession, ExamQualityReport
from .serializers import ExamSessionSerializer, ExamQualityReportSerializer


class ExamSessionViewSet(viewsets.ModelViewSet):
    queryset = ExamSession.objects.select_related("department", "department__faculty").all()
    serializer_class = ExamSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["course_code_title", "venue"]


class ExamQualityReportViewSet(viewsets.ModelViewSet):
    queryset = ExamQualityReport.objects.select_related(
        "exam_session", "exam_session__department", "student"
    ).all()
    serializer_class = ExamQualityReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["exam_session", "observed_misconduct"]
    search_fields = ["exam_session__course_code_title"]