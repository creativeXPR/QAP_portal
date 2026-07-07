# authentication/urls.py
from django.urls import path
from .views import google_login, complete_profile, RegistrationView

urlpatterns = [
    path('records/', google_login, name='google_login'),
    path('complaint-submission/', complete_profile, name='complete_profile'),
    path('feedback-tracking/', RegistrationView.as_view(), name='register'),
]