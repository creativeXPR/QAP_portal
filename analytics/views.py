from django.db import models
from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accreditation.models import (
    ComponentScore,
    CorrectiveAction,
    EarlyWarningAlert,
    Evidence,
    MetricSubmission,
    PARIResult,
)
from accreditation.permissions import AccreditationPermission
from accreditation.services import average_component_scores, evidence_completion_rate
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import KPI
from .serializers import KPISerializer
from .permissions import KPIPermission


class KPIViewSet(viewsets.ModelViewSet):
    queryset = KPI.objects.all()
    serializer_class = KPISerializer
    permission_classes = [IsAuthenticated, KPIPermission]


class AnalyticsResponseMixin:
    permission_classes = [AccreditationPermission]

    def success(self, data, message="Analytics fetched successfully."):
        return Response({"success": True, "message": message, "data": data})


def _base_pari_queryset(request):
    queryset = PARIResult.objects.select_related("cycle")
    cycle = request.query_params.get("cycle")
    faculty = request.query_params.get("faculty")
    department = request.query_params.get("department")
    programme = request.query_params.get("programme")
    classification = request.query_params.get("risk_classification")
    if cycle:
        queryset = queryset.filter(cycle_id=cycle)
    if faculty:
        queryset = queryset.filter(cycle__faculty=faculty)
    if department:
        queryset = queryset.filter(cycle__department=department)
    if programme:
        queryset = queryset.filter(programme=programme)
    if classification:
        queryset = queryset.filter(classification=classification)
    return queryset


class AccreditationOverviewView(AnalyticsResponseMixin, APIView):
    def get(self, request):
        pari = _base_pari_queryset(request)
        programme_count = pari.values("programme").distinct().count()
        submissions = MetricSubmission.objects.all()
        timely_submission_rate = 0
        submitted_count = submissions.count()
        if submitted_count:
            timely_count = submissions.filter(cycle__submission_deadline__isnull=False, created_at__date__lte=models.F("cycle__submission_deadline")).count()
            timely_submission_rate = round((timely_count / submitted_count) * 100, 2)
        data = {
            "total_programmes_monitored": programme_count,
            "accreditation_ready_count": pari.filter(classification="accreditation_ready").count(),
            "moderate_risk_count": pari.filter(classification="moderate_risk").count(),
            "high_risk_count": pari.filter(classification="high_risk").count(),
            "average_pari_score": pari.aggregate(value=Avg("pari_score"))["value"] or 0,
            "open_alerts": EarlyWarningAlert.objects.exclude(status="resolved").count(),
            "overdue_actions": CorrectiveAction.objects.filter(deadline__lt=timezone.now().date()).exclude(status__in=["verified", "closed"]).count(),
            "evidence_completion_rate": evidence_completion_rate(),
            "timely_submission_rate": timely_submission_rate,
        }
        return self.success(data)


class ProgrammesByRiskView(AnalyticsResponseMixin, APIView):
    def get(self, request):
        pari = _base_pari_queryset(request)
        data = {
            "accreditation_ready": list(pari.filter(classification="accreditation_ready").values("programme", "pari_score")),
            "moderate_risk": list(pari.filter(classification="moderate_risk").values("programme", "pari_score")),
            "high_risk": list(pari.filter(classification="high_risk").values("programme", "pari_score")),
        }
        return self.success(data)


class ComponentPerformanceView(AnalyticsResponseMixin, APIView):
    def get(self, request):
        scores = average_component_scores()
        items = [
            {
                "component": item["component__code"],
                "name": item["component__name"],
                "average_score": round(float(item["average_score"] or 0), 2),
            }
            for item in scores
        ]
        data = {
            "components": items,
            "weak_components": [item for item in items if item["average_score"] < 60],
            "strongest_components": sorted(items, key=lambda item: item["average_score"], reverse=True)[:5],
        }
        return self.success(data)


class EarlyWarningAnalyticsView(AnalyticsResponseMixin, APIView):
    def get(self, request):
        alerts = EarlyWarningAlert.objects.select_related("cycle", "component")
        data = {
            "open_alerts": alerts.exclude(status="resolved").count(),
            "critical_alerts": alerts.filter(severity="critical").exclude(status="resolved").count(),
            "alerts_by_component": list(alerts.values("component__code").annotate(count=Count("id")).order_by("component__code")),
            "alerts_by_faculty": list(alerts.values("cycle__faculty").annotate(count=Count("id")).order_by("cycle__faculty")),
            "alerts_by_department": list(alerts.values("cycle__department").annotate(count=Count("id")).order_by("cycle__department")),
        }
        return self.success(data)


class FacultySummaryView(AnalyticsResponseMixin, APIView):
    def get(self, request):
        data = list(
            PARIResult.objects.values("cycle__faculty")
            .annotate(programmes=Count("programme", distinct=True), average_pari_score=Avg("pari_score"))
            .order_by("cycle__faculty")
        )
        return self.success(data)


class DepartmentSummaryView(AnalyticsResponseMixin, APIView):
    def get(self, request):
        data = list(
            PARIResult.objects.values("cycle__department")
            .annotate(programmes=Count("programme", distinct=True), average_pari_score=Avg("pari_score"))
            .order_by("cycle__department")
        )
        return self.success(data)


class TimelineView(AnalyticsResponseMixin, APIView):
    def get(self, request):
        data = {
            "pari": list(PARIResult.objects.values("programme", "pari_score", "classification", "calculated_at").order_by("calculated_at")),
            "alerts": list(EarlyWarningAlert.objects.values("programme", "trigger_type", "severity", "status", "created_at").order_by("created_at")),
            "evidence": list(Evidence.objects.values("programme", "verification_status", "upload_date").order_by("upload_date")),
        }
        return self.success(data)
