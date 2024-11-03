import os

from django.contrib.auth.models import User, AbstractUser
from django.db import models


def get_upload_path(instance, filename):
    return os.path.join('images', filename)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to=get_upload_path, null=True)

    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return self.email
