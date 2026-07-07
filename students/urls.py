# authentication/urls.py
from django.urls import path
from .views import StudentFeedbackViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'feedback', StudentFeedbackViewSet, basename='feedback')
urlpatterns = [
    path('feedback-tracking/', StudentFeedbackViewSet.as_view({'get': 'list', 'post': 'create'}), name='feedback-tracking'),
] + router.urls