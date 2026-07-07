from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import StudentFeedbackViewSet, StudentViewSet


router = DefaultRouter()
router.register(r"feedback", StudentFeedbackViewSet, basename="feedback")

student_list = StudentViewSet.as_view({"get": "list", "post": "create"})
student_detail = StudentViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    path("", student_list, name="student-list"),
    path("<int:pk>/", student_detail, name="student-detail"),
    path("feedback-tracking/", StudentFeedbackViewSet.as_view({"get": "list", "post": "create"}), name="feedback-tracking"),
] + router.urls
