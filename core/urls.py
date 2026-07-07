from rest_framework.routers import DefaultRouter

from .views import DepartmentViewSet, FacultyViewSet

router = DefaultRouter()
router.register("faculties", FacultyViewSet, basename="faculty")
router.register("departments", DepartmentViewSet, basename="department")

urlpatterns = router.urls
