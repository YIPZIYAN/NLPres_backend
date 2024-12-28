from django.urls import path

from evaluation import views

urlpatterns = [
    path('', views.calculate_kappa, name='cohen_kappa'),
]