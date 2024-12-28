from django.db import models

from project.models import Project


class Comparison(models.Model):
    name = models.CharField(max_length=100)
    result = models.CharField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comparison'
