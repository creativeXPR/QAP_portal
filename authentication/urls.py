# authentication/urls.py
from django.urls import path
from .views import AdminUserListView, ProfileStatusOptionsView, RegistrationView, complete_profile, google_login

urlpatterns = [
    path('', google_login, name='google_login'),
    path('complete-profile/', complete_profile, name='complete_profile'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('status-options/', ProfileStatusOptionsView.as_view(), name='status_options'),
    path('cred/all/', AdminUserListView.as_view(), name='admin_user_list'),
]