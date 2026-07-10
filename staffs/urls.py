from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import StaffFeedbackViewSet, StaffNotificationViewSet, StaffViewSet


router = DefaultRouter()
router.register(r"feedback", StaffFeedbackViewSet, basename="staff-feedback")
router.register(r"notifications", StaffNotificationViewSet, basename="staff-notification")

staff_list = StaffViewSet.as_view({"get": "list", "post": "create"})
staff_detail = StaffViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    path("", staff_list, name="staff-list"),
    path("<int:pk>/", staff_detail, name="staff-detail"),
    path("feedback-tracking/", StaffFeedbackViewSet.as_view({"get": "list", "post": "create"}), name="staff-feedback-tracking"),
] + router.urls
