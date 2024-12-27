from enum import Enum


class Role(Enum):
    OWNER = 'owner'
    ANNOTATOR = 'annotator'

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]