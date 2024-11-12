from django.urls import path

from document.views import import_dataset

urlpatterns = [
    path('', import_dataset, name='import_dataset')
]