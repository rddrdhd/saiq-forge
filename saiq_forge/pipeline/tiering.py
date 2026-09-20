from typing import List, Sequence

from saiq_forge.detectors.base import Detector


class Tiering:
    """Runs detectors in order; each tier only scores what the previous tier passed."""

    def __init__(self, pass_threshold: float = 0.5):
        self.pass_threshold = pass_threshold

    def run(
        self,
        feature_vectors: Sequence[dict],
        detectors: Sequence[Detector],
    ) -> List[List[float]]:
        survivors = list(range(len(feature_vectors)))
        scores_by_tier = []

        for detector in detectors:
            tier_input = [feature_vectors[i] for i in survivors]
            detector.fit(tier_input)
            tier_scores = detector.score(tier_input)

            full_scores = [0.0] * len(feature_vectors)
            for idx, score in zip(survivors, tier_scores):
                full_scores[idx] = score
            scores_by_tier.append(full_scores)

            survivors = [
                idx for idx, score in zip(survivors, tier_scores)
                if score >= self.pass_threshold
            ]

        return scores_by_tier
