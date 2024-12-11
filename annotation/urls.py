from django.urls import path

from annotation import views

urlpatterns = [
    path('', views.create, name='create'),
    path('<int:pk>', views.annotation_detail, name='annotation_detail'),
]
