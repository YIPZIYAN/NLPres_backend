from django.contrib.auth.models import User
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from userprofile.models import CustomUser
from userprofile.serializers import UserSerializer, ChangePasswordSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_user(request):
    username = request.query_params.get('username')
    if username is not None:
        serializer = UserSerializer(CustomUser.objects.filter(username__contains=username), many=True, context={'request': request})
        return Response(serializer.data,status=status.HTTP_200_OK)
    return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(request.user, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
