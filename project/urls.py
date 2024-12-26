from django.urls import path

from project import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:project_id>', views.project_details, name='project_details'),
    path('create', views.create, name='create'),
    path('<int:project_id>/completed-collaborators',views.completed_collaborators, name='completed_collaborators'),
    path('<int:project_id>/collaborators/create',views.collaborator_create, name='collaborator_create'),
]
