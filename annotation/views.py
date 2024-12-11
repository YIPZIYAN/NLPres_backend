from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from annotation.serializers import AnnotationSerializer
from document.models import Annotation


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create(request):
    serializer = AnnotationSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        annotation = serializer.save()  # `create` method is called here
        return Response(AnnotationSerializer(annotation).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET','PUT','DELETE'])
@permission_classes([IsAuthenticated])
def annotation_detail(request, pk):
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