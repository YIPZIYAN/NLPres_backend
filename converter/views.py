from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from converter.serializers import ConverterSerializer


@api_view(['POST'])
def convert_file(request):
    serializer = ConverterSerializer(data=request.data)
    if serializer.is_valid():
        zip_buffer, content_type = serializer.save()
        response = HttpResponse(zip_buffer, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename="converted_files.zip"'
        return response

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


