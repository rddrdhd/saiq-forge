import os
from pathlib import Path

import pytest

from saiq_forge.pipeline.orchestrator import run

CONFIG_TEMPLATE = """
project:
  workdir: "{workdir}"
  datadir: "{datadir}"
  logsdir: "{logsdir}"
dataset:
  name: "dataset_b"
  path: "{data_path}"
features:
  modalities: ["T", "B"]
  window:
    width_sec: 5
    overlap: 0.5
detectors:
  active:
    - class: statistical
      method: zscore
      threshold: 3.0
      tier: cpu_statistical
"""


def test_end_to_end_on_a_real_capture(tmp_path):
    # Point SAIQ_FORGE_TEST_CAPTURE at a real dataset A/B/C flow-record CSV
    # to exercise this. No real data path is committed to this repo.
    data_path = os.environ.get("SAIQ_FORGE_TEST_CAPTURE")
    if not data_path or not Path(data_path).exists():
        pytest.skip("set SAIQ_FORGE_TEST_CAPTURE to a real capture CSV to run this test")

    config_path = tmp_path / "config.yaml"
    config_path.write_text(CONFIG_TEMPLATE.format(
        workdir=str(tmp_path),
        datadir=str(Path(data_path).parent),
        logsdir=str(tmp_path / "logs"),
        data_path=data_path,
    ))

    alerts = run(config_path)

    assert len(alerts) > 0
    assert all(0.0 <= a["score"] <= 1.0 for a in alerts)
