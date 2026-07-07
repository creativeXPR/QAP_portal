from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, LectureSessionViewSet

router = DefaultRouter()
router.register("courses", CourseViewSet, basename="course")
router.register("lecture-sessions", LectureSessionViewSet, basename="lecture-session")

urlpatterns = router.urls