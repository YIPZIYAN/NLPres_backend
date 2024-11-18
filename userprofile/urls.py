from django.urls import path
from userprofile.views import change_password, update_profile

urlpatterns = [
    path('change-password', change_password, name='change_password'),
    path('update', update_profile, name='update_profile'),
]