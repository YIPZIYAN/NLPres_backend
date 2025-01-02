from rest_framework.exceptions import ValidationError
from sklearn.metrics import cohen_kappa_score

from NLPres_backend.util import flatten, compute_ratings_matrix
from document.models import Annotation
from evaluation.classes.BaseEvaluation import BaseEvaluation
from statsmodels.stats.inter_rater import fleiss_kappa as fleiss_kappa_score
from label.models import Label
from utility.FileProcessor import FileProcessor


class Sequential(BaseEvaluation):
    document_data = []
    label_data = []
    annotators = None

    def __init__(self, project, documents, user_ids: list):
        super().__init__(project, documents, user_ids)
        file_processor = FileProcessor()
        self.annotators = [[] for _ in range(len(user_ids))]

        for document in self.documents:
            for i, user_id in enumerate(self.user_ids):
                annotations = Annotation.objects.filter(document=document, user_id=user_id).all()
                annotations = sorted(annotations, key=lambda x: (x.start, x.end))
                all_label = [
                    [annotation.start, annotation.end, annotation.label.name] for annotation in annotations
                ]

                text = document.text
                labels = all_label
                tokens = []
                idx = 0

                prev_end = -1

                for label in labels:
                    start, end, label_name = label

                    if start != (prev_end + 1):
                        segment = text[prev_end + 1: start]
                        prev_end = start - 1
                        idx, tokens = file_processor.add_tokens(idx, tokens, segment)

                    word = text[start:end + 1] if (start == end) else text[start:end]
                    prev_end = end
                    idx, token = file_processor.create_token(idx, word, label_name)
                    tokens.append(token)

                if prev_end != len(text) - 1:
                    segment = text[prev_end + 1: len(text)]
                    idx, tokens = file_processor.add_tokens(idx, tokens, segment)

                self.annotators[i].append(token["upostag"] for token in tokens)

    def cohen_kappa(self):
        y1 = flatten(self.annotators[0])
        y2 = flatten(self.annotators[1])
        return cohen_kappa_score(y1, y2)

    def fleiss_kappa(self):
        categories = list(Label.objects.filter(project=self.project).values_list('name', flat=True))
        categories.append('_')
        data = []

        for annotator in self.annotators:
            flatten_annotator = flatten(annotator)
            data.append(flatten_annotator)

        data = list(map(list, zip(*data)))

        ratings_matrix = compute_ratings_matrix(categories, data)

        try:
            return fleiss_kappa_score(ratings_matrix)
        except:
            raise ValidationError("Fleiss Kappa score matrix is invalid or empty.")


