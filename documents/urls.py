from rest_framework.routers import DefaultRouter

from .views import AccessLogViewSet, CategoryViewSet, DocumentViewSet, VersionViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="institutional-document-category")
router.register("documents", DocumentViewSet, basename="institutional-document")
router.register("versions", VersionViewSet, basename="institutional-document-version")
router.register("access-logs", AccessLogViewSet, basename="institutional-document-access-log")

urlpatterns = router.urls
