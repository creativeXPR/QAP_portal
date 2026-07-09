"""
URL configuration for qap_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from authentication.views import FlexibleLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', FlexibleLoginView.as_view(), name='flexible_login'),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/google/', include('authentication.urls')), # Points to our app
    path("api/core/", include("core.urls")),
    path("api/courses/", include("courses.urls")),
    path("api/lecturers/", include("lecturers.urls")),
    path("api/examinations/", include("examinations.urls")),
    path('api/accreditation/', include('accreditation.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/dashboards/', include('dashboards.urls')),
    path('api/qa-committee/', include('qa_committee.urls')),
    path('api/institutional-documents/', include('documents.urls')),

    # Student Feedback
    path('api/students/', include('students.urls')),
    
    # Update App
    path('api/updates/', include('update.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
