from rest_framework.exceptions import ValidationError
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats.inter_rater import fleiss_kappa as fleiss_kappa_score

from document.models import Annotation
from evaluation.classes.BaseEvaluation import BaseEvaluation
from label.models import Label


class Classification(BaseEvaluation):
    def cohen_kappa(self):
        annotators = [[] for _ in range(2)]

        for doc in self.documents:
            for idx, user_id in enumerate(self.user_ids):
                annotations = Annotation.objects.filter(document=doc, user_id=user_id).select_related("label")
                if not annotations.exists():
                    raise ValidationError(f"No annotations found for user {user_id} in document {doc.id}.")

                label = annotations.first().label.name
                annotators[idx].append(label)

        if len(annotators[0]) != len(annotators[1]):
            raise ValidationError("Mismatch in annotation counts between users.")

        return cohen_kappa_score(annotators[0], annotators[1])

    def fleiss_kappa(self):
        categories = list(Label.objects.filter(project=self.project).values_list('name', flat=True))
        if not categories:
            raise ValidationError("No labels found for this project.")
        ratings_matrix = []
        for doc in self.documents:
            annotations = Annotation.objects.filter(document=doc, user_id__in=self.user_ids).select_related("label")
            if not annotations.exists():
                raise ValidationError(f"No annotations found for document ID {doc.id}.")

            label_counts = [annotations.filter(label__name=category).count() for category in categories]
            ratings_matrix.append(label_counts)

        try:
            return fleiss_kappa_score(ratings_matrix)
        except:
            raise ValidationError("Fleiss Kappa score matrix is invalid or empty.")
