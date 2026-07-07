from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import LecturerProfile, AssessmentReport
from .serializers import LecturerProfileSerializer, AssessmentReportSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg


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
            avg_expr = {f: Avg(f) for f in indicator_fields}
            per_indicator = reports.aggregate(**avg_expr)
            overall = sum(per_indicator.values()) / len(per_indicator)
            summary["overall_average"] = round(overall, 2)
            summary["by_course"] = list(
                reports.values("course__code")
                .annotate(avg=Avg("teaches_class_regularly"))  # placeholder — needs proper per-course rollup
            )
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