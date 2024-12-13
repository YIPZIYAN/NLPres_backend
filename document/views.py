from lib2to3.fixes.fix_input import context

from conllu.serializer import serialize
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from document.models import Document
from document.serializers import DocumentSerializer, ImportDocumentSerializer, ExportDocumentSerializer
from project.models import Project


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def index(request, project_id):
    documents = Document.objects.filter(project_id=project_id)
    return Response(DocumentSerializer(documents, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create(request, project_id):
    serializer = ImportDocumentSerializer(data=request.data, context={'project_id': project_id})
    if serializer.is_valid():
        response_data = serializer.save()
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export(request, project_id):
    serializer = ExportDocumentSerializer(data=request.data, context={'project_id': project_id, 'request': request})
    if serializer.is_valid():
        data, content_type = serializer.save()
        response = HttpResponse(data, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="export_data"'
        return response

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def document_details(request, project_id, document_id):
    project = get_object_or_404(Project, pk=project_id)
    document = get_object_or_404(Document, project=project, pk=document_id)

    if request.method == 'GET':
        return Response(DocumentSerializer(document).data)

    elif request.method == 'PUT':
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
