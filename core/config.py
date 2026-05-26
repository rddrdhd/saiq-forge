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

    if not default_path.exists() and override_path is None:
        raise FileNotFoundError(
            f"Default config not found at {default_path}\n"
            "Make sure you run from inside the saiq-forge project directory."
        )
    if override_path is None:
        with open(default_path) as f:
            cfg = yaml.safe_load(f) or {}
    else: 
        with open(override_path) as f:
            cfg = yaml.safe_load(f) or {}
    

    return cfg


def project_root() -> Path:
    """Return the absolute path to the saiq-forge project root."""
    return _PROJECT_ROOT