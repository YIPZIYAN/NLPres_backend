from django.urls import path
from userprofile.views import change_password, update_profile, search_user

urlpatterns = [
    path('profile/change-password', change_password, name='change_password'),
    path('profile/update', update_profile, name='update_profile'),
    path('search', search_user, name='search_user'),
]
