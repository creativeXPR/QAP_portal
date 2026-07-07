from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AccreditationComponentViewSet,
    AccreditationCycleViewSet,
    AccreditationMetricViewSet,
    BulkSubmissionView,
    CalculateComponentScoresView,
    CalculatePARIView,
    CorrectiveActionViewSet,
    EarlyWarningAlertViewSet,
    EvidenceViewSet,
    MetricSubmissionViewSet,
)

router = DefaultRouter()
router.register("cycles", AccreditationCycleViewSet, basename="accreditation-cycle")
router.register("components", AccreditationComponentViewSet, basename="accreditation-component")
router.register("metrics", AccreditationMetricViewSet, basename="accreditation-metric")
router.register("submissions", MetricSubmissionViewSet, basename="accreditation-submission")
router.register("evidence", EvidenceViewSet, basename="accreditation-evidence")
router.register("alerts", EarlyWarningAlertViewSet, basename="accreditation-alert")
router.register("actions", CorrectiveActionViewSet, basename="accreditation-action")

urlpatterns = [
    path("submissions/bulk/", BulkSubmissionView.as_view(), name="accreditation-bulk-submission"),
    path(
        "cycles/<int:cycle_id>/programmes/<str:programme_id>/calculate-component-scores/",
        CalculateComponentScoresView.as_view(),
        name="calculate-component-scores",
    ),
    path(
        "cycles/<int:cycle_id>/programmes/<str:programme_id>/calculate-pari/",
        CalculatePARIView.as_view(),
        name="calculate-pari",
    ),
] + router.urls
