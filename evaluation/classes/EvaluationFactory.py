from rest_framework.exceptions import ValidationError

from enums.ProjectCategory import ProjectCategory
from evaluation.classes.Classification import Classification
from evaluation.classes.Sequential import Sequential
from evaluation.interfaces.EvaluationInterface import EvaluationInterface


class KappaFactory:

    def __init__(self, project, documents, user_ids: list):
        self.project = project
        self.documents = documents
        self.user_ids = user_ids

    def create_kappa_computation(self, project_category: ProjectCategory) -> EvaluationInterface:
        if project_category == ProjectCategory.CLASSIFICATION.value:
            return Classification(self.project, self.documents, self.user_ids)
        elif project_category == ProjectCategory.SEQUENTIAL.value:
            return Sequential(self.project,self.documents,self.user_ids)
        else:
            raise ValidationError("Invalid project category.")
