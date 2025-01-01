from sklearn.metrics import cohen_kappa_score

from document.models import Annotation
from evaluation.classes.BaseEvaluation import BaseEvaluation
from evaluation.interfaces.EvaluationInterface import EvaluationInterface
from utility.FileProcessor import FileProcessor


class Sequential(BaseEvaluation):
    document_data = []
    label_data = []
    annotators = [[] for _ in range(2)]

    def __init__(self, project, documents, user_ids: list):
        super().__init__(project, documents, user_ids)
        file_processor = FileProcessor()

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

                Sequential.annotators[i].append(token["upostag"] for token in tokens)

    def cohen_kappa(self):
        y1 = Sequential.annotators[0]
        y2 = Sequential.annotators[1]
        return cohen_kappa_score(y1, y2)

    def fleiss_kappa(self):
        pass
