from allauth.socialaccount.providers.mediawiki.provider import settings
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
import numpy as np
from agreement.utils.transform import pivot_table_frequency
from agreement.utils.kernels import linear_kernel
from agreement.metrics import cohens_kappa, krippendorffs_alpha
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from document.models import Document, Annotation
from project.models import Project
from userprofile.models import CustomUser


# Create your views here.
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def binary_classification(request, project_id):

    user_id_1 = request.data.get('user_id_1')
    user_id_2 = request.data.get('user_id_2')

    if not user_id_1 or not user_id_2:
        return Response({'error': 'Please provide both user_id_1 and user_id_2'}, status=400)

    user_1 = get_object_or_404(CustomUser, pk=user_id_1)
    user_2 = get_object_or_404(CustomUser, pk=user_id_2)

    project = get_object_or_404(Project, pk=project_id)
    documents = Document.objects.filter(project=project)
    document_data = []

    for doc in documents:
        annotations = Annotation.objects.filter(document=doc,user__in=[user_1,user_2])

        for annotation in annotations:
            document_data.append([doc.id, annotation.user.id, annotation.label.id])

    dataset = np.array(document_data)

    questions_answers_table = pivot_table_frequency(dataset[:, 0], dataset[:, 2])
    users_answers_table = pivot_table_frequency(dataset[:, 1], dataset[:, 2])

    kappa = cohens_kappa(questions_answers_table, users_answers_table)
    weighted_kappa = cohens_kappa(questions_answers_table, users_answers_table, weights_kernel=linear_kernel)
    alpha = krippendorffs_alpha(questions_answers_table)

    result = {
        "kappa": kappa,
        "weighted_kappa": weighted_kappa,
        "alpha": alpha
    }
    return Response(result)
