import math

from saiq_forge.detectors.base import Detector
from saiq_forge.detectors.registry import register


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


class _BaselineDetector(Detector):
    tier = "cpu_statistical"

    def __init__(self, threshold: float, **_ignored):
        self.threshold = threshold
        self._fit_stats = {}

    def fit(self, feature_vectors):
        if not feature_vectors:
            raise ValueError("cannot fit on zero feature vectors")
        for key in feature_vectors[0]:
            self._fit_stats[key] = self._stats([fv[key] for fv in feature_vectors])

    def score(self, feature_vectors):
        return [self._score_one(fv) for fv in feature_vectors]

    def _score_one(self, feature_vector):
        deviations = [
            self._deviation(value, self._fit_stats[key])
            for key, value in feature_vector.items()
            if key in self._fit_stats
        ]
        return _clip01(max(deviations) / self.threshold) if deviations else 0.0

    def _stats(self, values):
        raise NotImplementedError

    def _deviation(self, value, stat):
        raise NotImplementedError


@register("statistical", "zscore")
class ZScoreDetector(_BaselineDetector):
    def _stats(self, values):
        n = len(values)
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n
        return {"mean": mean, "std": math.sqrt(variance)}

    def _deviation(self, value, stat):
        if stat["std"] == 0:
            return 0.0
        return abs(value - stat["mean"]) / stat["std"]


@register("statistical", "iqr")
class IQRDetector(_BaselineDetector):
    def _stats(self, values):
        ordered = sorted(values)
        n = len(ordered)
        q1 = ordered[n // 4]
        q3 = ordered[(3 * n) // 4]
        return {"q1": q1, "q3": q3, "iqr": q3 - q1}

    def _deviation(self, value, stat):
        if stat["iqr"] == 0:
            return 0.0
        if value > stat["q3"]:
            return (value - stat["q3"]) / stat["iqr"]
        if value < stat["q1"]:
            return (stat["q1"] - value) / stat["iqr"]
        return 0.0
