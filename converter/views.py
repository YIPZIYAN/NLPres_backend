from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from converter.serializers import ConverterSerializer


@api_view(['POST'])
def convert_file(request):
    serializer = ConverterSerializer(data=request.data)
    if serializer.is_valid():
        converted_content, content_type = serializer.save()

        # Prepare the response with the converted file
        response = HttpResponse(converted_content, content_type=content_type)
        filename = request.data['file'].name.split('.')[0]
        response[
            'Content-Disposition'] = f'attachment; filename="{filename}.{serializer.validated_data["output_format"]}"'
        return response

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


