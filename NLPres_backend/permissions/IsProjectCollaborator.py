from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission

from project.models import Project


class IsProjectCollaborator(BasePermission):
    """
    Custom permission to allow access only to collaborators of a project.
    """

    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return False

        project = get_object_or_404(Project, pk=project_id)
        return project.collaborator_set.filter(user=request.user, joined_at__isnull=False).exists()
