from abc import ABC, abstractmethod
from typing import Sequence


class Detector(ABC):
    tier: str

    @abstractmethod
    def fit(self, feature_vectors: Sequence[dict]) -> None:
        raise NotImplementedError

    @abstractmethod
    def score(self, feature_vectors: Sequence[dict]) -> list:
        """One anomaly score per feature vector, each in [0, 1]."""
        raise NotImplementedError
