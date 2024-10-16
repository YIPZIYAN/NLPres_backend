from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='userprofile', on_delete=models.CASCADE)
    category = models.CharField(max_length=100, null=True)
    avatar = models.ImageField(upload_to='avatars', null=True)
