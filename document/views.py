from lib2to3.fixes.fix_input import context

from conllu.serializer import serialize
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from NLPres_backend.permissions.IsProjectCollaborator import IsProjectCollaborator
from NLPres_backend.permissions.IsProjectOwnerOrReadOnly import IsProjectOwnerOrReadOnly
from NLPres_backend.util import calculate_progress
from document.models import Document, Annotation
from document.serializers import DocumentSerializer, ImportDocumentSerializer, ExportDocumentSerializer
from enums.ProjectCategory import ProjectCategory
from project.models import Project


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def index(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    documents = Document.objects.filter(project=project)

    serialized_data = DocumentSerializer(documents, many=True, context={'request': request}).data

    return Response(serialized_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def pagination(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    documents = Document.objects.filter(project=project)

    paginator = PageNumberPagination()
    paginator.page_size = 1
    paginated_documents = paginator.paginate_queryset(documents, request)

    serialized_data = DocumentSerializer(
        paginated_documents, many=True, context={'request': request}
    ).data

    return paginator.get_paginated_response(serialized_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def progress(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    progress_data = calculate_progress(request.user, project)
    return Response(progress_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProjectOwnerOrReadOnly])
def create(request, project_id):
    serializer = ImportDocumentSerializer(data=request.data, context={'project_id': project_id})
    if serializer.is_valid():
        response_data = serializer.save()
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def export(request, project_id):
    serializer = ExportDocumentSerializer(data=request.data, context={'project_id': project_id, 'request': request})
    if serializer.is_valid():
        data, content_type = serializer.save()
        response = HttpResponse(data, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="export_data"'
        return response

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsProjectOwnerOrReadOnly])
def document_details(request, project_id, document_id):
    project = get_object_or_404(Project, pk=project_id)
    document = get_object_or_404(Document, project=project, pk=document_id)

    if request.method == 'GET':
        return Response(DocumentSerializer(document, context={'request': request}).data)

    elif request.method == 'PUT':
        serializer = DocumentSerializer(document, data=request.data)
        if serializer.is_valid():
            serializer.save(project_id=project_id)
            if project.category == ProjectCategory.SEQUENTIAL.value:
                document.annotation_set.filter(user=request.user).delete()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def clear_label(request, project_id, document_id):
    project = get_object_or_404(Project, pk=project_id)
    document = get_object_or_404(Document, pk=document_id, project=project)
    document.annotation_set.filter(user=request.user).delete()

    return Response(status=status.HTTP_204_NO_CONTENT)
