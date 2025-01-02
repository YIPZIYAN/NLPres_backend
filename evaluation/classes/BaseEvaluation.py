from evaluation.interfaces.EvaluationInterface import EvaluationInterface


class BaseEvaluation(EvaluationInterface):
    def __init__(self, project, documents, user_ids: list):
        self.project = project
        self.documents = documents
        self.user_ids = user_ids


    def cohen_kappa(self):
        pass

    def fleiss_kappa(self):
        pass