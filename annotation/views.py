from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from NLPres_backend.permissions.IsProjectCollaborator import IsProjectCollaborator
from annotation.serializers import AnnotationSerializer
from document.models import Annotation


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def create(request, project_id):
    def process_data(data, many):
        serializer = AnnotationSerializer(data=data, many=many, context={'request': request})
        if serializer.is_valid():
            annotations = serializer.save()
            return Response(
                AnnotationSerializer(annotations, many=many).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(request.data, list):
        return process_data(request.data, many=True)
    return process_data(request.data, many=False)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def annotation_detail(request, project_id, pk):
    annotation = get_object_or_404(Annotation, pk=pk)

    if request.method == 'GET':
        return Response(AnnotationSerializer(annotation).data)

    elif request.method == 'PUT':
        serializer = AnnotationSerializer(annotation, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        annotation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
