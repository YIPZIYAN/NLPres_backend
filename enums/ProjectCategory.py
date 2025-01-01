from enum import Enum


class ProjectCategory(Enum):
    CLASSIFICATION = 'text classification'
    SEQUENTIAL = 'sequential labelling'

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]

    @classmethod
    def from_value(cls, value):
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"'{value}' is not a valid value for {cls.__name__}.")
