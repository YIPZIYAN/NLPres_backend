import uuid
from random import choices

from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import serializers

from enums.Role import Role
from project.models import Project, Collaborator
from userprofile.serializers import UserSerializer


class CollaboratorSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user = UserSerializer(read_only=True)
    role = serializers.CharField(required=True)
    user_id = serializers.IntegerField(write_only=True)
    joined_at = serializers.DateTimeField(required=False)

    class Meta:
        model = Collaborator
        fields = ['id','user','role','user_id', 'joined_at']

    def create(self, validated_data):
        project_id = self.context.get('project_id')
        if not project_id:
            raise serializers.ValidationError({"project_id": "This field is required."})

        project = get_object_or_404(Project, id=project_id)
        collaborator = Collaborator.objects.create(project=project, **validated_data)

        send_mail(
            subject='You are invited to collaborate on a project',
            message=f'Click the link to view the invitation: http://10.123.51.100/project',
            from_email='noreply@nlpres.com',
            recipient_list=[collaborator.user.username]
        )

        return collaborator

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_serializer = UserSerializer(instance.user, context=self.context)
        representation['user'] = user_serializer.data

        return representation


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(required=True, max_length=100)
    description = serializers.CharField(required=True, max_length=255)
    category = serializers.CharField(required=True, max_length=100)
    created_at = serializers.DateTimeField(read_only=True)
    collaborators = serializers.SerializerMethodField()
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Project
        fields = '__all__'

    def create(self, validated_data):
        project = Project.objects.create(**validated_data)

        Collaborator.objects.create(project=project,
                                    user=self.context['request'].user,
                                    role=Role.OWNER.value,
                                    joined_at=project.created_at)

        return project

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.category = validated_data.get('category', instance.category)
        instance.save()
        return instance

    def get_collaborators(self, obj):
        collaborators = obj.collaborator_set.all()
        serializer = CollaboratorSerializer(collaborators, many=True, context=self.context)
        return serializer.data

