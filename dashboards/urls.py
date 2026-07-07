from django.urls import path

from .views import (
    AccreditationDashboardView,
    ActivityFeedView,
    DashboardSummaryView,
    DocumentsDashboardView,
    EarlyWarningDashboardView,
    ExaminationDashboardView,
    InfrastructureLabsDashboardView,
    QACommitteeDashboardView,
    ResearchDashboardView,
    StudentExperienceDashboardView,
    TeachingLearningDashboardView,
    UniversityOverviewDashboardView,
)


urlpatterns = [
    path("summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("university-overview/", UniversityOverviewDashboardView.as_view(), name="dashboard-university-overview"),
    path("accreditation/", AccreditationDashboardView.as_view(), name="dashboard-accreditation"),
    path("qa-committee/", QACommitteeDashboardView.as_view(), name="dashboard-qa-committee"),
    path("teaching-learning/", TeachingLearningDashboardView.as_view(), name="dashboard-teaching-learning"),
    path("examinations/", ExaminationDashboardView.as_view(), name="dashboard-examinations"),
    path("documents/", DocumentsDashboardView.as_view(), name="dashboard-documents"),
    path("student-experience/", StudentExperienceDashboardView.as_view(), name="dashboard-student-experience"),
    path("infrastructure-labs/", InfrastructureLabsDashboardView.as_view(), name="dashboard-infrastructure-labs"),
    path("research/", ResearchDashboardView.as_view(), name="dashboard-research"),
    path("early-warning/", EarlyWarningDashboardView.as_view(), name="dashboard-early-warning"),
    path("activity-feed/", ActivityFeedView.as_view(), name="dashboard-activity-feed"),
]
