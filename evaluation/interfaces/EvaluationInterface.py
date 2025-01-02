from abc import ABC, abstractmethod


class EvaluationInterface(ABC):
    @abstractmethod
    def cohen_kappa(self):
        pass

    @abstractmethod
    def fleiss_kappa(self):
        pass
