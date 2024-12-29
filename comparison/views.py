from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from NLPres_backend.permissions.IsProjectCollaborator import IsProjectCollaborator
from comparison.models import Comparison
from comparison.serializers import CompareSerializer, ComparisonSerializer
from project.models import Project


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def index(request, project_id):
    comparisons = Comparison.objects.filter(project_id=project_id)
    serializer = ComparisonSerializer(comparisons, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def compare(request, project_id):
    serializer = CompareSerializer(data=request.data, context={'project_id': project_id})
    if serializer.is_valid():
        response_data = serializer.save()
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def comparison_detail(request, project_id, comparison_id):
    try:
        project = Project.objects.get(pk=project_id)
        comparison = Comparison.objects.get(project=project, pk=comparison_id)
    except Project.DoesNotExist or Comparison.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(ComparisonSerializer(comparison).data)

    elif request.method == 'PUT':
        serializer = ComparisonSerializer(comparison, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        comparison.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)