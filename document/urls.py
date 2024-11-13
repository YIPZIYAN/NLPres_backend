from django.urls import path
from document import views

urlpatterns = [
    path('project/<int:project_id>/documents', views.index, name='index'),
    path('import/', views.import_document, name='import_document')
]