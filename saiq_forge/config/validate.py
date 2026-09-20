from saiq_forge.detectors import registry as detector_registry
from saiq_forge.features import registry as feature_registry


class ConfigError(ValueError):
    pass


def validate(config: dict) -> dict:
    modalities = config.get("features", {}).get("modalities", [])
    known_modalities = feature_registry.available_modalities()
    unknown_modalities = set(modalities) - known_modalities
    if unknown_modalities:
        raise ConfigError(
            f"unknown feature modalities: {sorted(unknown_modalities)} "
            f"(known: {sorted(known_modalities)})"
        )

    window = config.get("features", {}).get("window", {})
    width = window.get("width_sec")
    if not isinstance(width, (int, float)) or width <= 0:
        raise ConfigError(f"features.window.width_sec must be > 0, got {width!r}")

    overlap = window.get("overlap")
    if not isinstance(overlap, (int, float)) or not (0 <= overlap < 1):
        raise ConfigError(f"features.window.overlap must be in [0, 1), got {overlap!r}")

    for detector_cfg in config.get("detectors", {}).get("active", []):
        try:
            detector_registry.get_detector(detector_cfg.get("class"), detector_cfg.get("method"))
        except KeyError as exc:
            raise ConfigError(str(exc)) from exc

    return config
