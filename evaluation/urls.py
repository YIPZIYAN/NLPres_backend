from django.urls import path

from evaluation import views

urlpatterns = [
    path('cohen-kappa', views.cohen_kappa, name='cohen_kappa'),
]