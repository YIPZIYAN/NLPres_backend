from django.urls import path

from comparison import views

urlpatterns = [
    path('compare', views.compare, name='compare'),
]