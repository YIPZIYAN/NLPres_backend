from django.contrib.auth.models import User, AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, related_name='userprofile', on_delete=models.CASCADE)
    category = models.CharField(max_length=100, null=True)
    avatar = models.ImageField(upload_to='avatars', null=True)
