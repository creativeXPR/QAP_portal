from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ActivityFeedView,
    CommitteeMeetingAttendanceViewSet,
    CommitteeMeetingViewSet,
    EffectivenessView,
    OverdueActionsView,
    QAActionEvidenceViewSet,
    QAActionPlanViewSet,
    QAAuditCycleViewSet,
    QAAuditFindingViewSet,
    QACommitteeDataReviewViewSet,
    QACommitteeMemberViewSet,
    QACommitteeReportViewSet,
    QACommitteeViewSet,
    QARecommendationViewSet,
    RiskSummaryView,
    SummaryView,
)


router = DefaultRouter()
router.register("committees", QACommitteeViewSet, basename="qa-committee")
router.register("members", QACommitteeMemberViewSet, basename="qa-committee-member")
router.register("meetings", CommitteeMeetingViewSet, basename="qa-committee-meeting")
router.register("attendance", CommitteeMeetingAttendanceViewSet, basename="qa-committee-attendance")
router.register("audit-cycles", QAAuditCycleViewSet, basename="qa-audit-cycle")
router.register("findings", QAAuditFindingViewSet, basename="qa-audit-finding")
router.register("recommendations", QARecommendationViewSet, basename="qa-recommendation")
router.register("action-plans", QAActionPlanViewSet, basename="qa-action-plan")
router.register("evidence", QAActionEvidenceViewSet, basename="qa-action-evidence")
router.register("reports", QACommitteeReportViewSet, basename="qa-committee-report")
router.register("data-reviews", QACommitteeDataReviewViewSet, basename="qa-committee-data-review")

urlpatterns = [
    path("summary/", SummaryView.as_view(), name="qa-committee-summary"),
    path("effectiveness/", EffectivenessView.as_view(), name="qa-committee-effectiveness"),
    path("overdue-actions/", OverdueActionsView.as_view(), name="qa-committee-overdue-actions"),
    path("risk-summary/", RiskSummaryView.as_view(), name="qa-committee-risk-summary"),
    path("activity-feed/", ActivityFeedView.as_view(), name="qa-committee-activity-feed"),
] + router.urls
