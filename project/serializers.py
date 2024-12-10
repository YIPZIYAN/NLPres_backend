from rest_framework import serializers

from enums.Role import Role
from project.models import Project, Collaborator
from userprofile.serializers import UserSerializer


class CollaboratorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Collaborator
        fields = ['user', 'role']


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(required=True, max_length=100)
    description = serializers.CharField(required=True, max_length=255)
    category = serializers.CharField(required=True, max_length=100)
    created_at = serializers.DateTimeField(read_only=True)
    collaborators = CollaboratorSerializer(many=True, source='collaborator_set',read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Project
        fields = '__all__'

    def create(self, validated_data):
        project = Project.objects.create(**validated_data)

        Collaborator.objects.create(project=project,
                                    user=self.context['request'].user,
                                    role=Role.OWNER.value)

        return project
