from rest_framework.routers import DefaultRouter
from .views import ExamSessionViewSet, ExamQualityReportViewSet

router = DefaultRouter()
router.register("exam-sessions", ExamSessionViewSet, basename="exam-session")
router.register("quality-reports", ExamQualityReportViewSet, basename="quality-report")

urlpatterns = router.urls