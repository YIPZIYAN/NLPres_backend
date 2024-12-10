from django.urls import path

from annotation import views

urlpatterns = [
    path('', views.create, name='create'),
    path('update/<int:pk>', views.update, name='update'),
]
