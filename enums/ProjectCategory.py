from enum import Enum


class ProjectCategory(Enum):
    CLASSIFICATION = 'text classification'
    SEQUENTIAL = 'sequential labelling'

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]