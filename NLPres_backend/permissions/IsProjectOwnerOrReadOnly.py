from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.permissions import BasePermission

from enums.Role import Role
from project.models import Project


class IsProjectOwnerOrReadOnly(BasePermission):
    """
    Custom permission to allow access only to owner of a project.
    """

    def has_permission(self, request, view):
        project_id = view.kwargs.get('project_id')
        if not project_id:
            return False

        project = get_object_or_404(Project, pk=project_id)
        if request.method in permissions.SAFE_METHODS:
            return project.collaborator_set.filter(user=request.user, joined_at__isnull=False).exists()

        return project.collaborator_set.filter(user=request.user, role=Role.OWNER.value).exists()
