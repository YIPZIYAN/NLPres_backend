from rest_framework import serializers

from project.models import Project, Collaborator
from userprofile.serializers import UserSerializer


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(required=True, max_length=100)
    description = serializers.CharField(required=True, max_length=255)
    category = serializers.CharField(required=True, max_length=100)
    collaborators = UserSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Project
        fields = '__all__'

    def create(self, validated_data):
        collaborators_data = validated_data.pop('collaborators')
        project = Project.objects.create(**validated_data)

        for collaborator_data in collaborators_data:
            Collaborator.objects.create(project=project, **collaborator_data)

        return project
