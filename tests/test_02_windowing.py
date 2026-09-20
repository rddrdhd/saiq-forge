import pytest

from saiq_forge.features.windowing import sliding_windows, step_seconds


def test_step_seconds_matches_overlap_fraction():
    # Guards the "step fraction vs overlap fraction" inversion the wiki
    # flags: overlap 0.75 must yield a SMALL step (0.25 * width), not large.
    assert step_seconds(width_sec=10, overlap=0.0) == 10
    assert step_seconds(width_sec=10, overlap=0.5) == 5
    assert step_seconds(width_sec=10, overlap=0.75) == 2.5


def test_zero_step_raises():
    with pytest.raises(ValueError):
        list(sliding_windows(
            [{"ts": 0}], timestamp_fn=lambda r: r["ts"], width_sec=10, overlap=1.0,
        ))


def test_sliding_windows_cover_full_span():
    records = [{"ts": t} for t in range(0, 20)]
    windows = list(sliding_windows(
        records, timestamp_fn=lambda r: r["ts"], width_sec=10, overlap=0.5,
    ))
    assert windows[0].start == 0
    assert windows[0].end == 10
    assert windows[1].start == 5
    assert windows[-1].start < 19


def test_empty_records_yield_no_windows():
    windows = list(sliding_windows(
        [], timestamp_fn=lambda r: r["ts"], width_sec=10, overlap=0.5,
    ))
    assert windows == []
