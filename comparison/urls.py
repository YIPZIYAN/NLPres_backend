from django.urls import path

from comparison import views

urlpatterns = [
    path('', views.index, name='index'),
    path('compare', views.compare, name='compare'),
    path('<int:comparison_id>', views.comparison_detail, name='comparison_detail')
]