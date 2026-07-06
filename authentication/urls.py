# authentication/urls.py
from django.urls import path
from .views import google_login, complete_profile, RegistrationView

urlpatterns = [
    path('', google_login, name='google_login'),
    path('complete-profile/', complete_profile, name='complete_profile'),
    path('register/', RegistrationView.as_view(), name='register'),
]