from django.contrib.auth.models import User, AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars', null=True)

    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return self.email



