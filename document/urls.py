from django.urls import path
from document import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create', views.create, name='create'),
    path('<int:document_id>',views.document_details,name='document_details'),
]