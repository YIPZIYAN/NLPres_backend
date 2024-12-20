from django.urls import path

from annotation import views

urlpatterns = [
    path('create', views.create, name='create'),
    path('<int:pk>', views.annotation_detail, name='annotation_detail'),
]
