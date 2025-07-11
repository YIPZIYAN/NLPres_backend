from django.urls import path

from label import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create', views.create, name='create'),
    path('<int:label_id>', views.label_detail, name='label_detail'),
    path('import', views.import_file, name='import'),
    path('export', views.export, name='export')
]
