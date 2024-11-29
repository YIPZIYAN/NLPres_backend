from django.urls import path

from label import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create', views.create, name='create'),
    path('<int:label_id>', views.label_detail, name='label_detail'),

]
