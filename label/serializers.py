from django.shortcuts import get_object_or_404
from rest_framework import serializers

from label.models import Label
from project.models import Project
from project.serializers import ProjectSerializer


class LabelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=True, max_length=100)
    color = serializers.CharField(required=True, max_length=100)

    class Meta:
        model = Label
        fields = ['id', 'name', 'color']

    def create(self, validated_data):
        # Get the project_id from the context
        project_id = self.context.get('project_id')
        if not project_id:
            raise serializers.ValidationError({"project_id": "This field is required."})

        # Fetch the Project instance or raise a 404 if not found
        project = get_object_or_404(Project, id=project_id)

        # Create the Label instance
        return Label.objects.create(project=project, **validated_data)