"""
core/config.py
──────────────
Loads config file.yml into a plain dict that every module can import.

Usage
─────
    from core.config import load_config

    cfg = load_config()                        # uses config/default.yml
    cfg = load_config("config/hpc.yml")       

Keys are accessed like a normal dict:
    cfg["input"]["path"]
    cfg["parallel"]["mode"]
    cfg["batching"]["window_sec"]
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Project root = parent of this file's parent (saiq-forge/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """
    Load config/default.yml

    Parameters
    ----------
    path : if using anything else than config/default.yml

    Returns
    -------
    dict - config
    """
    default_path = _PROJECT_ROOT / "config" / "default.yml"

    if not default_path.exists() and path is None:
        raise FileNotFoundError(
            f"Default config not found at {default_path}\n"
            "Make sure you run from inside the saiq-forge project directory."
        )
    if path is None:
        with open(default_path) as f:
            cfg = yaml.safe_load(f) or {}
    else: 
        with open(path) as f:
            cfg = yaml.safe_load(f) or {}
    
    return cfg


def project_root() -> Path:
    """Return the absolute path to the saiq-forge project root."""
    return _PROJECT_ROOT