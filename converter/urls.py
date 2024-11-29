from django.urls import path

from converter import views

urlpatterns = [
    path('convert/', views.convert_file, name='convert_file'),
]