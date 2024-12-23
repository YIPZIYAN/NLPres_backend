from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from comparison.serializers import ComparisonSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def compare(request, project_id):
    serializer = ComparisonSerializer(data=request.data,  context={'project_id': project_id})
    if serializer.is_valid():
        response_data = serializer.save()
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)