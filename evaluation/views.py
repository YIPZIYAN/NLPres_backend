from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.authtoken.admin import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from sklearn.metrics import cohen_kappa_score

from document.models import Annotation, Document
from project.models import Project


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cohen_kappa(request, project_id):
    user_ids = request.data.get("user_ids", [])

    # Validate the user IDs
    if not isinstance(user_ids, list) or len(user_ids) != 2:
        raise ValidationError("You must provide exactly 2 user IDs in a list.")

    if not User.objects.filter(id__in=user_ids).count() == 2:
        raise ValidationError("One or more provided user IDs do not exist.")

    # Get the project and its documents
    project = get_object_or_404(Project, pk=project_id)
    documents = Document.objects.filter(project=project)

    # Initialize annotators list
    annotators = [[] for _ in range(len(user_ids))]

    # Retrieve annotations for each document and user
    for doc in documents:
        for idx, user_id in enumerate(user_ids):
            annotations = Annotation.objects.filter(document=doc, user_id=user_id).select_related("label")
            if not annotations.exists():
                raise ValidationError("Annotators have not yet been completed.")

            label = annotations.first().label.name
            annotators[idx].append(label)

    # Check if annotators have equal lengths (sanity check for consistency)
    if len(annotators[0]) != len(annotators[1]):
        raise ValidationError("Mismatch in annotation counts between users.")


    kappa = cohen_kappa_score(annotators[0], annotators[1])

    return Response(kappa, status=status.HTTP_200_OK)
