from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from document.serializers import DocumentSerializer

@api_view(['GET'])
def index(request):
    return Response(DocumentSerializer(Docu))

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_dataset(request):
    serializer = DocumentSerializer(data=request.data)
    if serializer.is_valid():
        response_data = serializer.save()
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
