from saiq_forge.config.loader import load_config
from saiq_forge.detectors import registry as detector_registry
from saiq_forge.features import registry as feature_registry
from saiq_forge.features.windowing import sliding_windows
from saiq_forge.io.captures import load_capture
from saiq_forge.pipeline.tiering import Tiering


def run(config_path) -> list:
    config = load_config(config_path)

    flows = load_capture(config["dataset"]["path"])

    window_cfg = config["features"]["window"]
    windows = list(sliding_windows(
        flows,
        timestamp_fn=lambda flow: flow.timestamp,
        width_sec=window_cfg["width_sec"],
        overlap=window_cfg["overlap"],
    ))

    extractors = [feature_registry.get_extractor(m)() for m in config["features"]["modalities"]]
    feature_vectors = []
    for window in windows:
        merged = {}
        for extractor in extractors:
            merged.update(extractor.extract(window))
        feature_vectors.append(merged)

    detectors = []
    for detector_cfg in config["detectors"]["active"]:
        detector_cls = detector_registry.get_detector(detector_cfg["class"], detector_cfg["method"])
        detectors.append(detector_cls(threshold=detector_cfg["threshold"]))

    scores_by_tier = Tiering().run(feature_vectors, detectors)
    final_scores = scores_by_tier[-1] if scores_by_tier else [0.0] * len(windows)

    return [
        {"start": window.start, "end": window.end, "score": score}
        for window, score in zip(windows, final_scores)
    ]
