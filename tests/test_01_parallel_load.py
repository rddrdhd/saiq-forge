"""
tests/test_01_parallel_load.py
───────────────────────────
Demonstrates and tests parallel parquet loading.

Two modes
─────────
1. pytest  — run as part of the test suite:
       singularity exec saiq-forge.sif python -m pytest tests/test_parallel_load.py -v -s

2. standalone — run directly to see live worker output:
       singularity exec saiq-forge.sif python tests/test_parallel_load.py

The -s flag in pytest is important here: it disables output capture
so the [Worker XX | pid=... ] lines appear in the SLURM log in real time.

Expected output
───────────────
[ParquetLoader] Dispatching 4 shards across 4 workers (4 file(s) total)

[Worker 00 | pid=12345 | nid007916] loaded 1 file(s) → 1,250 rows  (1823.4s span)
[Worker 01 | pid=12346 | nid007916] loaded 1 file(s) → 1,250 rows  (1801.2s span)
[Worker 02 | pid=12347 | nid007916] loaded 1 file(s) → 1,250 rows  (1798.9s span)
[Worker 03 | pid=12348 | nid007916] loaded 1 file(s) → 1,251 rows  (1800.1s span)

[ParquetLoader] All workers done. Total rows across all shards: 5,001
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import polars as pl
import pytest

# Make the project root importable regardless of CWD
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from core.config import load_config
from modules.ingestion.loader import ParquetLoader


# ─────────────────────────────────────────────────────────────────────────────
# Fixture: generate synthetic parquet files (4 files → 4 workers)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_test_parquets(data_dir: Path, n_files: int = 4, rows_per_file: int = 500) -> list[Path]:
    """
    Write N synthetic parquet files into data_dir.
    Reuses files if they already exist (faster repeat runs).
    """
    import numpy as np
    import pyarrow as pa
    import pyarrow.parquet as pq

    data_dir.mkdir(parents=True, exist_ok=True)
    files = []

    for i in range(n_files):
        out_path = data_dir / f"traffic_part_{i:02d}.parquet"
        if out_path.exists():
            files.append(out_path)
            continue

        rng = np.random.default_rng(seed=i)
        base_ns = 1_737_700_000_000_000_000 + i * 1_800 * 10**9  # each file 30 min apart
        times   = base_ns + np.sort(rng.integers(0, 1_800 * 10**9, rows_per_file))

        protocols    = rng.choice(["TCP", "UDP", "ICMP"], rows_per_file, p=[0.55, 0.40, 0.05])
        applications = rng.choice(["DNS", "SSL", "HTTP", "UNKNOWN"], rows_per_file)

        df = pa.table({
            "TIME":        times.astype("int64"),
            "DURATION":    rng.integers(500, 2_000_000, rows_per_file).astype("int64"),
            "SRC_IP":      [f"10.0.{i}.{j % 254 + 1}" for j in range(rows_per_file)],
            "SRC_PORT":    rng.integers(32768, 60999, rows_per_file).astype("int32").tolist(),
            "DST_IP":      rng.choice(["8.8.8.8", "1.1.1.1", "93.184.216.34"], rows_per_file).tolist(),
            "DST_PORT":    rng.choice([53, 80, 443], rows_per_file).astype("int32").tolist(),
            "DUAL":        rng.integers(0, 2, rows_per_file).astype("int8").tolist(),
            "PROTOCOL":    protocols.tolist(),
            "APPLICATION": applications.tolist(),
            "SRC_PACKETS": rng.integers(1, 20, rows_per_file).astype("int32").tolist(),
            "DST_PACKETS": rng.integers(0, 20, rows_per_file).astype("int32").tolist(),
            "SRC_BYTES":   rng.integers(40, 15000, rows_per_file).astype("int64").tolist(),
            "DST_BYTES":   rng.integers(0, 15000, rows_per_file).astype("int64").tolist(),
        })
        pq.write_table(df, str(out_path))
        files.append(out_path)
        print(f"  [fixture] Wrote {out_path.name} ({rows_per_file} rows)", flush=True)

    return sorted(files)


@pytest.fixture(scope="module")
def cfg_with_test_data(tmp_path_factory):
    """
    Load config and point input.path at the generated test parquet files.
    Uses a module-scoped tmp dir so files are only generated once.
    """
    data_dir = tmp_path_factory.mktemp("parquet_data")
    _generate_test_parquets(data_dir, n_files=4, rows_per_file=500)

    cfg = load_config()
    # Override the path to point at our temp test data
    cfg["input"]["path"] = str(data_dir / "*.parquet")
    cfg["input"]["_resolved_path"] = str(data_dir / "*.parquet")
    return cfg


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestConfigLoads:
    """Config must load cleanly and contain expected keys."""

    def test_config_loads(self):
        cfg = load_config()
        assert "input" in cfg
        assert "schema" in cfg
        assert "batching" in cfg
        assert "parallel" in cfg

    def test_config_has_resolved_path(self):
        cfg = load_config()
        assert "_resolved_path" in cfg["input"]

    def test_batching_defaults(self):
        cfg = load_config()
        assert cfg["batching"]["window_sec"] == 300
        assert cfg["batching"]["overlap_fraction"] == 0.5

    def test_schema_column_names_present(self):
        cfg = load_config()
        schema = cfg["schema"]
        for key in ["time_col", "src_ip_col", "dst_ip_col", "protocol_col"]:
            assert key in schema, f"Missing schema key: {key}"


class TestSingleLoad:
    """Single-process loader must produce a normalised DataFrame."""

    def test_load_returns_dataframe(self, cfg_with_test_data):
        loader = ParquetLoader(cfg_with_test_data)
        df = loader.load(verbose=True)
        assert isinstance(df, pl.DataFrame)

    def test_load_has_derived_columns(self, cfg_with_test_data):
        loader = ParquetLoader(cfg_with_test_data)
        df = loader.load(verbose=False)
        for col in ["TIME_SEC", "DATETIME", "DURATION_SEC", "SRC_BPP", "BYTE_ASYM"]:
            assert col in df.columns, f"Missing derived column: {col}"

    def test_load_is_sorted_by_time(self, cfg_with_test_data):
        loader = ParquetLoader(cfg_with_test_data)
        df = loader.load(verbose=False)
        times = df["TIME_SEC"].to_list()
        assert times == sorted(times), "DataFrame is not sorted by TIME_SEC"

    def test_load_correct_row_count(self, cfg_with_test_data):
        loader = ParquetLoader(cfg_with_test_data)
        df = loader.load(verbose=False)
        # 4 files × 500 rows = 2000 rows expected
        assert len(df) == 2000

    def test_no_nulls_in_key_columns(self, cfg_with_test_data):
        loader = ParquetLoader(cfg_with_test_data)
        df = loader.load(verbose=False)
        for col in ["TIME_SEC", "SRC_IP", "DST_IP", "PROTOCOL"]:
            assert df[col].null_count() == 0, f"{col} has unexpected nulls"


class TestParallelLoad:
    """
    Parallel loader must produce one result per worker, all with correct data.
    The [Worker XX | pid=...] lines prove separate processes loaded each shard.
    """

    def test_parallel_returns_correct_worker_count(self, cfg_with_test_data):
        loader = ParquetLoader(cfg_with_test_data)
        results = loader.load_parallel_shards(n_workers=4)
        # 4 files → 4 workers → 4 results
        assert len(results) == 4

    def test_each_worker_returns_dataframe(self, cfg_with_test_data):
        loader = ParquetLoader(cfg_with_test_data)
        results = loader.load_parallel_shards(n_workers=4)
        for worker_id, df, info in results:
            assert isinstance(df, pl.DataFrame), f"Worker {worker_id} did not return a DataFrame"

    def test_each_worker_has_unique_pid(self, cfg_with_test_data):
        """Different pids confirm separate OS processes were used."""
        loader = ParquetLoader(cfg_with_test_data)
        results = loader.load_parallel_shards(n_workers=4)
        pids = [info["pid"] for _, _, info in results]
        # All pids should be different from the main process
        main_pid = os.getpid()
        for pid in pids:
            assert pid != main_pid, f"Worker ran in the main process (pid={pid})"

    def test_parallel_total_rows_matches_single(self, cfg_with_test_data):
        """Concatenated parallel shards must have the same row count as single load."""
        loader = ParquetLoader(cfg_with_test_data)

        df_single = loader.load(verbose=False)
        results    = loader.load_parallel_shards(n_workers=4)

        total_parallel = sum(len(df) for _, df, _ in results)
        assert total_parallel == len(df_single), (
            f"Row count mismatch: parallel={total_parallel}, single={len(df_single)}"
        )

    def test_worker_info_fields(self, cfg_with_test_data):
        """Each worker's info dict must contain identity fields."""
        loader = ParquetLoader(cfg_with_test_data)
        results = loader.load_parallel_shards(n_workers=2)
        for _, _, info in results:
            assert "worker_id" in info
            assert "hostname"  in info
            assert "pid"       in info
            assert "n_rows"    in info

    def test_fewer_workers_than_files(self, cfg_with_test_data):
        """2 workers loading 4 files — each worker gets 2 files."""
        loader = ParquetLoader(cfg_with_test_data)
        results = loader.load_parallel_shards(n_workers=2)
        assert len(results) == 2
        for _, _, info in results:
            assert len(info["files"]) == 2  # 2 files per worker

    def test_more_workers_than_files_clamps(self, cfg_with_test_data):
        """Requesting 8 workers for 4 files should clamp to 4."""
        loader = ParquetLoader(cfg_with_test_data)
        results = loader.load_parallel_shards(n_workers=8)
        assert len(results) == 4  # clamped to n_files


# ─────────────────────────────────────────────────────────────────────────────
# Standalone entry point (run directly, not via pytest)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Run as:  python tests/test_parallel_load.py
    Useful to see worker output in real time without pytest's capture.
    """
    print("=" * 60)
    print("saiq-forge — parallel parquet loading demo")
    print("=" * 60)

    data_dir = _PROJECT_ROOT / "data"
    generated = _generate_test_parquets(data_dir, n_files=4, rows_per_file=1000)
    print(f"\nTest data: {len(generated)} parquet files in {data_dir}\n")

    cfg = load()
    cfg["input"]["path"]           = str(data_dir / "*.parquet")
    cfg["input"]["_resolved_path"] = str(data_dir / "*.parquet")

    loader = ParquetLoader(cfg)

    print("── Single-process load ──────────────────────────────────")
    df = loader.load(verbose=True)
    print(f"Result: {len(df):,} rows, {len(df.columns)} columns\n")

    print("── Parallel load (4 workers) ────────────────────────────")
    results = loader.load_parallel_shards(n_workers=4)

    print("\nPer-worker summary:")
    for worker_id, df_shard, info in results:
        print(
            f"  Worker {worker_id:02d} | pid={info['pid']:>6} | "
            f"host={info['hostname']} | "
            f"files={info['files']} | "
            f"rows={info['n_rows']:,}"
        )

    all_df = pl.concat([df for _, df, _ in results])
    print(f"\nConcatenated total: {len(all_df):,} rows")
    print("\nDone.")