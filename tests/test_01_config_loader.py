import pytest

from saiq_forge.config.loader import load_config
from saiq_forge.config.validate import ConfigError

VALID_YAML = """
project:
  workdir: "/tmp/work"
  datadir: "/tmp/data"
  logsdir: "/tmp/logs"
dataset:
  name: "dataset_b"
  path: "/tmp/data/dataset_b.csv"
features:
  modalities: ["T", "B"]
  window:
    width_sec: 10
    overlap: 0.5
detectors:
  active:
    - class: statistical
      method: zscore
      threshold: 3.0
      tier: cpu_statistical
"""


def _write(tmp_path, content):
    path = tmp_path / "config.yaml"
    path.write_text(content)
    return path


def test_load_valid_config(tmp_path):
    config = load_config(_write(tmp_path, VALID_YAML))
    assert config["features"]["modalities"] == ["T", "B"]
    assert config["execution"]["backend"] == "local"


def test_unknown_modality_rejected(tmp_path):
    bad = VALID_YAML.replace('["T", "B"]', '["T", "TO"]')
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, bad))


def test_unknown_detector_method_rejected(tmp_path):
    bad = VALID_YAML.replace("method: zscore", "method: not_a_method")
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, bad))


def test_overlap_out_of_range_rejected(tmp_path):
    bad = VALID_YAML.replace("overlap: 0.5", "overlap: 1.0")
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, bad))


def test_zero_width_rejected(tmp_path):
    bad = VALID_YAML.replace("width_sec: 10", "width_sec: 0")
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, bad))
