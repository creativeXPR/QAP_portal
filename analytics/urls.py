from django.urls import path

from .views import (
    AccreditationOverviewView,
    ComponentPerformanceView,
    DepartmentSummaryView,
    EarlyWarningAnalyticsView,
    FacultySummaryView,
    ProgrammesByRiskView,
    TimelineView,
)

urlpatterns = [
    path("accreditation/overview/", AccreditationOverviewView.as_view(), name="analytics-accreditation-overview"),
    path("accreditation/programmes-by-risk/", ProgrammesByRiskView.as_view(), name="analytics-programmes-by-risk"),
    path("accreditation/component-performance/", ComponentPerformanceView.as_view(), name="analytics-component-performance"),
    path("accreditation/early-warning/", EarlyWarningAnalyticsView.as_view(), name="analytics-early-warning"),
    path("accreditation/faculty-summary/", FacultySummaryView.as_view(), name="analytics-faculty-summary"),
    path("accreditation/department-summary/", DepartmentSummaryView.as_view(), name="analytics-department-summary"),
    path("accreditation/timeline/", TimelineView.as_view(), name="analytics-timeline"),
]
