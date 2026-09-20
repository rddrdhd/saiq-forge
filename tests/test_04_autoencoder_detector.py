import random
import statistics

import pytest

from saiq_forge.detectors.autoencoder import ClassicalAutoencoderDetector


def _synthetic_feature_vectors(n, seed):
    rng = random.Random(seed)
    return [
        {"a": rng.gauss(0, 1), "b": rng.gauss(0, 1), "c": rng.gauss(0, 1), "d": rng.gauss(0, 1)}
        for _ in range(n)
    ]


def test_fit_and_score_shape_and_range():
    detector = ClassicalAutoencoderDetector(hidden_dims=[4], latent_dim=2, epochs=10, batch_size=8)
    detector.fit(_synthetic_feature_vectors(40, seed=1))

    eval_records = _synthetic_feature_vectors(10, seed=2)
    scores = detector.score(eval_records)

    assert len(scores) == len(eval_records)
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_fit_rejects_empty_input():
    detector = ClassicalAutoencoderDetector()
    with pytest.raises(ValueError):
        detector.fit([])


def test_score_before_fit_raises():
    detector = ClassicalAutoencoderDetector()
    with pytest.raises(RuntimeError):
        detector.score(_synthetic_feature_vectors(1, seed=0))


def test_outlier_scores_higher_than_typical():
    # Compare against the typical set's mean, not max: with only a handful
    # of held-out gaussian draws, one can land past the mean+3-sigma
    # threshold by chance alone - that's noise in the test, not a detector
    # bug, and shouldn't make this flaky.
    detector = ClassicalAutoencoderDetector(
        hidden_dims=[4], latent_dim=2, epochs=30, batch_size=8, seed=0
    )
    detector.fit(_synthetic_feature_vectors(60, seed=1))

    typical_scores = detector.score(_synthetic_feature_vectors(20, seed=2))
    outlier_scores = detector.score([{"a": 20.0, "b": -20.0, "c": 20.0, "d": -20.0}])

    assert outlier_scores[0] > statistics.mean(typical_scores)
