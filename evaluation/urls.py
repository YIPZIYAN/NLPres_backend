from django.urls import path

from evaluation import views

urlpatterns = [
    path('cohen-kappa', views.cohen_kappa, name='cohen_kappa'),
    path('fleiss-kappa', views.fleiss_kappa, name='fleiss_kappa'),
]