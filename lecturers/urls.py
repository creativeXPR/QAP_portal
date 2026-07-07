from rest_framework.routers import DefaultRouter
from .views import LecturerProfileViewSet, AssessmentReportViewSet

router = DefaultRouter()
router.register("lecturer-profiles", LecturerProfileViewSet, basename="lecturer-profile")
router.register("assessment-reports", AssessmentReportViewSet, basename="assessment-report")

urlpatterns = router.urls