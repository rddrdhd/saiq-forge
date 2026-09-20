from abc import ABC, abstractmethod

from saiq_forge.features.windowing import Window


class FeatureExtractor(ABC):
    modality: str

    @abstractmethod
    def extract(self, window: Window) -> dict:
        raise NotImplementedError
