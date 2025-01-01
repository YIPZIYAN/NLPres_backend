from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from NLPres_backend.permissions.IsProjectOwnerOrReadOnly import IsProjectOwnerOrReadOnly
from NLPres_backend.permissions.IsProjectCollaborator import IsProjectCollaborator
from NLPres_backend.util import calculate_progress
from document.models import Document
from project.models import Project, Collaborator
from project.serializers import ProjectSerializer, CollaboratorSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def index(request):
    return Response(ProjectSerializer(Project.objects.filter(collaborator__user=request.user), many=True,
                                      context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create(request):
    serializer = ProjectSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsProjectOwnerOrReadOnly])
def project_details(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == 'GET':
        return Response(ProjectSerializer(project, context={'request': request}).data)

    elif request.method == 'PUT':
        serializer = ProjectSerializer(project, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsProjectOwnerOrReadOnly])
def completed_collaborators(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    total_count = Document.objects.filter(project=project).count()

    completed = []
    for collaborator in project.collaborator_set.all():
        progress_data = calculate_progress(collaborator.user, project)
        if progress_data['completed'] == total_count:
            completed.append(collaborator)

    serializer = CollaboratorSerializer(completed, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProjectOwnerOrReadOnly])
def collaborator_create(request, project_id):
    serializer = CollaboratorSerializer(data=request.data, context={'request': request, 'project_id': project_id})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsProjectOwnerOrReadOnly])
def collaborator_delete(request, project_id, collaborator_id):
    project = get_object_or_404(Project, pk=project_id)
    collaborator = get_object_or_404(Collaborator, pk=collaborator_id, project=project)
    documents = Document.objects.filter(project_id=project_id)

    for document in documents:
        document.annotation_set.filter(user=collaborator.user).delete()

    collaborator.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def collaborator_quit(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    collaborator = project.collaborator_set.get(user=request.user)
    documents = Document.objects.filter(project_id=project_id)

    for document in documents:
        document.annotation_set.filter(user=collaborator.user).delete()

    collaborator.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_invitation(request, project_id):
    collaborator = get_object_or_404(Collaborator, user=request.user, project_id=project_id)

    if collaborator.joined_at is not None:
        return Response({"detail": "Invitation already accepted."}, status=status.HTTP_400_BAD_REQUEST)

    collaborator.joined_at = now()
    collaborator.save()

    return Response({"detail": "Invitation accepted successfully."}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_invitation(request, project_id):
    collaborator = get_object_or_404(Collaborator, user=request.user, project_id=project_id)

    collaborator.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


