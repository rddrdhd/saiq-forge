"""
core/config.py
──────────────
Loads config/default.yml (and an optional override file) into a plain
dict that every module can import.

Usage
─────
    from core.config import load_config

    cfg = load_config()                        # uses config/default.yml
    cfg = load_config("config/hpc.yml")        # merges hpc.yml on top

Keys are accessed like a normal dict:
    cfg["input"]["path"]
    cfg["parallel"]["mode"]
    cfg["batching"]["window_sec"]

Path resolution
───────────────
All path values that start with a relative segment are resolved relative
to the project root (the directory that contains the config/ folder),
NOT relative to the CWD.  This means jobs submitted from any directory
on LUMI always find the right files.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

# Project root = parent of this file's parent (saiq-forge/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base (override wins on conflicts)."""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def load_config(override_path: str | Path | None = None) -> dict[str, Any]:
    """
    Load config/default.yml and optionally merge an override file on top.

    Parameters
    ----------
    override_path : path to a second YAML file whose values take precedence.
                    Useful for hpc.yml, experiment-specific configs, etc.

    Returns
    -------
    dict — merged configuration
    """
    default_path = _PROJECT_ROOT / "config" / "default.yml"

    if not default_path.exists():
        raise FileNotFoundError(
            f"Default config not found at {default_path}\n"
            "Make sure you run from inside the saiq-forge project directory."
        )

    with open(default_path) as f:
        cfg = yaml.safe_load(f) or {}

    if override_path is not None:
        override_path = Path(override_path)
        if not override_path.is_absolute():
            override_path = _PROJECT_ROOT / override_path
        with open(override_path) as f:
            overrides = yaml.safe_load(f) or {}
        cfg = _deep_merge(cfg, overrides)

    # Resolve the input path relative to project root if it's not absolute
    raw_input_path = cfg.get("input", {}).get("path", "")
    if raw_input_path and not Path(raw_input_path).is_absolute():
        cfg["input"]["_resolved_path"] = str(_PROJECT_ROOT / raw_input_path)
    else:
        cfg["input"]["_resolved_path"] = raw_input_path

    # Resolve output dir similarly
    raw_out = cfg.get("output", {}).get("base_dir", "outputs")
    if not Path(raw_out).is_absolute():
        cfg["output"]["_resolved_base_dir"] = str(_PROJECT_ROOT / raw_out)
    else:
        cfg["output"]["_resolved_base_dir"] = raw_out

    return cfg


def project_root() -> Path:
    """Return the absolute path to the saiq-forge project root."""
    return _PROJECT_ROOT