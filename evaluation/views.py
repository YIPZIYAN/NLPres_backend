from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.admin import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from scipy.constants import value

from NLPres_backend.permissions.IsProjectCollaborator import IsProjectCollaborator
from document.models import Document
from enums.EvaluationMethod import EvaluationMethod
from enums.ProjectCategory import ProjectCategory
from evaluation.classes.EvaluationFactory import KappaFactory
from project.models import Project


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsProjectCollaborator])
def calculate_kappa(request, project_id):
    """
    API endpoint to calculate Cohen's Kappa or Fleiss' Kappa.
    Request body must include:
    - "method": either "cohen" or "fleiss"
    - "user_ids": a list of user IDs
    """
    method = request.data.get("method")
    user_ids = request.data.get("user_ids", [])

    # Validate the method
    if method not in ["cohen", "fleiss"]:
        raise ValidationError("Invalid method. Choose either 'cohen' or 'fleiss'.")

    # Validate the user IDs
    if not isinstance(user_ids, list) or len(user_ids) < 2:
        raise ValidationError("You must provide at least 2 user IDs in a list.")

    if User.objects.filter(id__in=user_ids).count() < len(user_ids):
        raise ValidationError("One or more provided user IDs do not exist.")

    # Get the project
    project = get_object_or_404(Project, pk=project_id)
    if not project.category == ProjectCategory.CLASSIFICATION.value:
        raise ValidationError("Project category is not classification.")

    # Get documents
    documents = Document.objects.filter(project=project)
    if not documents.exists():
        raise ValidationError("No documents found for this project.")

    factory = KappaFactory(project, documents, user_ids)
    kappa_computation = factory.create_kappa_computation(ProjectCategory.from_value(project.category).value)

    method_function_map = {
        EvaluationMethod.COHEN.value: kappa_computation.cohen_kappa,
        EvaluationMethod.FLEISS.value: kappa_computation.fleiss_kappa,
    }

    # Call the appropriate kappa computation method
    kappa = method_function_map[method]()

    return Response({"method": method, "kappa": kappa}, status=status.HTTP_200_OK)
