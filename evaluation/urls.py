from django.urls import path

from evaluation import views

urlpatterns = [
    path('binary-classification', views.binary_classification, name='index'),
]