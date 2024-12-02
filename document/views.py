from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from document.models import Document
from document.serializers import DocumentSerializer, ImportDocumentSerializer


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


