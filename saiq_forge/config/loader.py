import yaml

from saiq_forge.config.validate import validate

DEFAULTS = {
    "execution": {"backend": "local"},
    "features": {"window": {"width_sec": 10, "overlap": 0.5}},
    "detectors": {"active": []},
}


def _merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path) -> dict:
    with open(path) as fh:
        raw = yaml.safe_load(fh) or {}
    return validate(_merge(DEFAULTS, raw))
