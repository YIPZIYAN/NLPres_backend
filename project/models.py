import uuid

from django.contrib.auth.models import User
from django.db import models

from NLPres_backend import settings
from enums.ProjectCategory import ProjectCategory


class Project(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=100, choices=ProjectCategory.choices())
    collaborators = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Collaborator")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_category(self, category: ProjectCategory) -> bool:
        return self.category == category.value

    class Meta:
        db_table = 'projects'


class Collaborator(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'collaborators'
        unique_together = ('user', 'project')
