from collections import defaultdict

from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AssessmentReport, LecturerProfile
from .serializers import AssessmentReportSerializer, LecturerProfileSerializer


class LecturerProfileViewSet(viewsets.ModelViewSet):
    queryset = LecturerProfile.objects.select_related("user", "department", "department__faculty").all()
    serializer_class = LecturerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__username", "staff_id"]

    @action(detail=True, methods=["get"])
    def assessment_summary(self, request, pk=None):
        lecturer = self.get_object()
        reports = lecturer.assessment_reports.all()
        summary = {
            "total_assessments": reports.count(),
            "overall_average": None,
            "by_course": [],
        }
        if reports.exists():
            indicator_fields = reports.model.INDICATOR_FIELDS
            avg_expr = {field: Avg(field) for field in indicator_fields}
            per_indicator = reports.aggregate(**avg_expr)
            overall = sum(per_indicator.values()) / len(per_indicator)
            summary["overall_average"] = round(overall, 2)

            course_scores = defaultdict(list)
            for report in reports.select_related("course"):
                course_scores[report.course.code].append(report.average_rating)
            summary["by_course"] = [
                {"course__code": course_code, "avg": round(sum(scores) / len(scores), 2)}
                for course_code, scores in sorted(course_scores.items())
            ]
        return Response(summary)


class AssessmentReportViewSet(viewsets.ModelViewSet):
    queryset = AssessmentReport.objects.select_related(
        "lecturer", "lecturer__user", "course", "student"
    ).all()
    serializer_class = AssessmentReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["lecturer", "course", "academic_session", "semester", "included_in_dossier"]
    search_fields = ["lecturer__user__username", "course__code"]
