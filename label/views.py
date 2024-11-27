from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from label.models import Label
from label.serializers import LabelSerializer


@api_view(['GET'])
def index(request, project_id):
    labels = Label.objects.filter(project_id=project_id)
    if not labels.exists():
        return Response({"detail": "No labels found for this project."}, status=status.HTTP_404_NOT_FOUND)

    serializer = LabelSerializer(labels, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def create(request, project_id):
    serializer = LabelSerializer(data=request.data, context={'project_id': project_id})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)