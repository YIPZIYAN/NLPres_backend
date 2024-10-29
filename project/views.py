from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from project.models import Project
from project.serializers import ProjectSerializer


@api_view(['GET'])
def index(request):
    return Response(ProjectSerializer(Project.objects.filter(collaborator__user=request.user), many=True).data)

@api_view(['POST'])
def create(request):
    serializer = ProjectSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)