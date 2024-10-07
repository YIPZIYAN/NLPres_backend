from django.db import models

from document.models import Document
from label.models import Label


class Annotation(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    label = models.ForeignKey(Label, on_delete=models.CASCADE)
    start = models.IntegerField(null=True)
    end = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'annotations'