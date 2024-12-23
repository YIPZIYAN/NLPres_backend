"""
URL configuration for NLPres_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from dj_rest_auth.registration.views import VerifyEmailView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

import userprofile.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/register/', include('dj_rest_auth.registration.urls')),
    path('api/auth/registration/account-confirm-email/', VerifyEmailView.as_view(),name='account_email_verification_sent'),

    path('api/profile/', include('userprofile.urls')),

    path('api/project/', include('project.urls')),

    path('api/project/<int:project_id>/label/',include('label.urls')),

    path('api/project/<int:project_id>/document/', include('document.urls')),

    path('api/annotate/', include('annotation.urls')),

    path('api/project/<int:project_id>/evaluate/', include('evaluation.urls')),

    path('api/converter/', include('converter.urls')),

    path('api/project/<int:project_id>/comparison/', include('comparison.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

