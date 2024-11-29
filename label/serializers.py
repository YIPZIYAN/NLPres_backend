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
        project_id = self.context.get('project_id')
        if not project_id:
            raise serializers.ValidationError({"project_id": "This field is required."})

        project = get_object_or_404(Project, id=project_id)
        return Label.objects.create(project=project, **validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.color = validated_data.get('color', instance.color)
        instance.save()
        return instance