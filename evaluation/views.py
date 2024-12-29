from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.admin import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats.inter_rater import fleiss_kappa as fleiss_kappa_score

from NLPres_backend.permissions.IsProjectCollaborator import IsProjectCollaborator
from document.models import Annotation, Document
from enums.ProjectCategory import ProjectCategory
from label.models import Label
from project.models import Project


def compute_cohen_kappa(project, documents, user_ids):
    # Initialize annotators list
    annotators = [[] for _ in range(2)]

    # Retrieve annotations for each document and user
    for doc in documents:
        for idx, user_id in enumerate(user_ids):
            annotations = Annotation.objects.filter(document=doc, user_id=user_id).select_related("label")
            if not annotations.exists():
                raise ValidationError(f"No annotations found for user {user_id} in document {doc.id}.")

            label = annotations.first().label.name
            annotators[idx].append(label)

    # Check for consistent annotation counts
    if len(annotators[0]) != len(annotators[1]):
        raise ValidationError("Mismatch in annotation counts between users.")

    # Compute Cohen's Kappa
    return cohen_kappa_score(annotators[0], annotators[1])


def compute_fleiss_kappa(project, documents, user_ids):
    categories = list(Label.objects.filter(project=project).values_list('name', flat=True))
    if not categories:
        raise ValidationError("No labels found for this project.")

    ratings_matrix = []
    for doc in documents:
        annotations = Annotation.objects.filter(document=doc, user_id__in=user_ids).select_related("label")
        if not annotations.exists():
            raise ValidationError(f"No annotations found for document ID {doc.id}.")

        label_counts = [annotations.filter(label__name=category).count() for category in categories]
        ratings_matrix.append(label_counts)

    try:
        return fleiss_kappa_score(ratings_matrix)
    except:
        raise ValidationError("Fleiss Kappa score matrix is invalid or empty.")


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

    # Dynamically call the appropriate function
    kappa_function_map = {
        "cohen": compute_cohen_kappa,
        "fleiss": compute_fleiss_kappa,
    }

    kappa_function = kappa_function_map[method]
    kappa = kappa_function(project, documents, user_ids)

    return Response({"method": method, "kappa": kappa}, status=status.HTTP_200_OK)
