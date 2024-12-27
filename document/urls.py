from django.urls import path
from document import views

urlpatterns = [
    path('', views.index, name='index'),
    path('pagination', views.pagination, name='pagination'),
    path('progress', views.progress, name='progress'),
    path('create', views.create, name='create'),
    path('<int:document_id>',views.document_details,name='document_details'),
    path('export', views.export, name='export')
]