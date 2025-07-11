from lib2to3.fixes.fix_input import context

from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from NLPres_backend.permissions.IsProjectCollaborator import IsProjectCollaborator
from NLPres_backend.permissions.IsProjectOwnerOrReadOnly import IsProjectOwnerOrReadOnly
from label.models import Label
from label.serializers import LabelSerializer, ImportLabelSerializer, ExportLabelSerializer
from project.models import Project


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def index(request, project_id):
    labels = Label.objects.filter(project_id=project_id)
    serializer = LabelSerializer(labels, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProjectOwnerOrReadOnly])
def create(request, project_id):
    serializer = LabelSerializer(data=request.data, context={'project_id': project_id})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProjectOwnerOrReadOnly])
def import_file(request, project_id):
    serializer = ImportLabelSerializer(data=request.data, context={'project_id': project_id})
    if serializer.is_valid():
        response_data = serializer.save()
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def export(request, project_id):
    serializer = ExportLabelSerializer(data=request.data, context={'project_id': project_id})
    if serializer.is_valid():
        data, content_type = serializer.save()
        response = HttpResponse(data, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="label_config"'
        return response


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsProjectOwnerOrReadOnly])
def label_detail(request, project_id, label_id):
    try:
        project = Project.objects.get(pk=project_id)
        label = Label.objects.get(project=project, pk=label_id)
    except Project.DoesNotExist or Label.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(LabelSerializer(label).data)

    elif request.method == 'PUT':
        serializer = LabelSerializer(label, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        label.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
