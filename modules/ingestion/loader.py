"""
modules/ingestion/loader.py
───────────────────────────
ParquetLoader — config-driven loader with parallel shard support.

Two public methods
──────────────────
load()
    Loads all files matching config["input"]["path"] into one normalised
    DataFrame.  Good for dev, single-node batch, and test fixtures.

load_parallel_shards(n_workers)
    Splits the file list into n_workers shards and returns a list of
    (worker_id, shard_DataFrame) pairs.  Each shard is loaded in a
    separate process so you see one print line per worker — proof that
    data is flowing to each slot.

Why spawn instead of fork?
──────────────────────────
Python's default multiprocessing start method on Linux is 'fork'.
On HPC clusters (and anywhere Polars/NumPy are imported before the
fork), child processes inherit the parent's internal thread pools in
a LOCKED state → they hang indefinitely waiting for a lock that will
never release.  'spawn' starts a clean Python interpreter per worker,
avoiding this entirely.  It is slightly slower to start up but always
correct on LUMI and other HPC environments.

sys.path and spawn
──────────────────
Unlike fork, spawn does NOT inherit the parent's sys.path.  Each worker
must re-add the project root before importing project modules.  We pass
project_root as part of the args tuple so workers can do this themselves.
"""

from __future__ import annotations

import glob
import multiprocessing as mp
import os
import socket
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import polars as pl

from modules.ingestion import schema as sch


# ─────────────────────────────────────────────────────────────────────────────
# Internal worker — must be top-level for pickling by multiprocessing
# ─────────────────────────────────────────────────────────────────────────────

def _load_shard(args: tuple) -> tuple[int, pl.DataFrame, dict]:
    """
    Load one shard (a subset of files) into a normalised DataFrame.

    Parameters (packed as a tuple for ProcessPoolExecutor compatibility)
    ----------
    worker_id    : integer index of this worker
    file_paths   : list of parquet file paths this worker owns
    schema_cfg   : schema config dict (time_unit, duration_unit, etc.)
    project_root : absolute path to project root — needed because spawn
                   starts a clean interpreter that does NOT inherit the
                   parent's sys.path (unlike fork).

    Returns
    -------
    (worker_id, DataFrame, info_dict)
    """
    import sys
    worker_id, file_paths, schema_cfg, project_root = args

    # Restore project root on sys.path — required with spawn start method
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Now safe to import project modules
    from modules.ingestion import schema as sch_local

    time_unit     = schema_cfg.get("time_unit",     "ns")
    duration_unit = schema_cfg.get("duration_unit", "us")

    lf = pl.scan_parquet(file_paths)
    lf = sch_local.normalize(lf, time_unit=time_unit, duration_unit=duration_unit)
    df = lf.sort("TIME_SEC").collect()

    info = {
        "worker_id":  worker_id,
        "hostname":   socket.gethostname(),
        "pid":        os.getpid(),
        "files":      [Path(p).name for p in file_paths],
        "n_rows":     len(df),
        "n_cols":     len(df.columns),
        "time_range": round(df["TIME_SEC"].max() - df["TIME_SEC"].min(), 2),
    }

    # This print goes to the SLURM .out log — one line per worker
    print(
        f"[Worker {worker_id:02d} | pid={os.getpid()} | {socket.gethostname()}] "
        f"loaded {len(file_paths)} file(s) → {len(df):,} rows  "
        f"({info['time_range']}s span)",
        flush=True,
    )

    return worker_id, df, info


# ─────────────────────────────────────────────────────────────────────────────
# Public class
# ─────────────────────────────────────────────────────────────────────────────

class ParquetLoader:
    """
    Config-driven loader for network flow parquet files.

    Parameters
    ----------
    cfg : full config dict from core.config.load_config()
    """

    def __init__(self, cfg: dict[str, Any]) -> None:
        self._cfg          = cfg
        self._input_cfg    = cfg.get("input", {})
        self._schema_cfg   = cfg.get("schema", {})
        self._batching_cfg = cfg.get("batching", {})

        # Resolved glob pattern (set by core.config)
        self._path_pattern: str = (
            self._input_cfg.get("_resolved_path")
            or self._input_cfg.get("path", "data/*.parquet")
        )

        # Project root — passed to spawn workers so they can fix sys.path
        self._project_root: str = str(Path(__file__).resolve().parent.parent.parent)

    # ── path helpers ─────────────────────────────────────────────────────────

    def resolve_files(self) -> list[str]:
        """Expand the glob pattern and return a sorted list of file paths."""
        files = sorted(glob.glob(self._path_pattern))
        if not files:
            raise FileNotFoundError(
                f"No parquet files found matching: {self._path_pattern!r}\n"
                "Check config input.path and make sure data files are present."
            )
        return files

    # ── single-process load ───────────────────────────────────────────────────

    def load(self, verbose: bool = True) -> pl.DataFrame:
        """
        Load all matching files into one sorted DataFrame.
        Single-process — good for dev and small datasets.
        """
        files = self.resolve_files()

        time_unit     = self._batching_cfg.get("time_unit",    "ns")
        duration_unit = self._schema_cfg.get("duration_unit",  "us")

        if verbose:
            print(f"[Loader] Reading {len(files)} file(s) from {self._path_pattern!r}", flush=True)

        lf = pl.scan_parquet(files)
        lf = sch.normalize(lf, time_unit=time_unit, duration_unit=duration_unit)
        df = lf.sort("TIME_SEC").collect()

        if verbose:
            info = sch.summary(df)
            print(
                f"[Loader] Loaded {info['n_rows']:,} rows | "
                f"{info['time_range_sec']}s span | "
                f"{info['unique_src_ips']} src IPs",
                flush=True,
            )
        return df

    # ── parallel shard load ───────────────────────────────────────────────────

    def load_parallel_shards(
        self,
        n_workers: int | None = None,
    ) -> list[tuple[int, pl.DataFrame, dict]]:
        """
        Split files across n_workers processes, load in parallel.

        Uses 'spawn' start method to avoid fork+thread-pool deadlocks
        that occur on HPC clusters when Polars is imported before forking.

        Parameters
        ----------
        n_workers : number of parallel workers.
                    None → reads from config parallel.n_workers,
                           then falls back to os.cpu_count().

        Returns
        -------
        List of (worker_id, DataFrame, info_dict) in worker_id order.
        Concatenate with:  pl.concat([df for _, df, _ in results])
        """
        files = self.resolve_files()

        # Resolve n_workers
        if n_workers is None:
            n_workers = (
                self._cfg.get("parallel", {}).get("n_workers")
                or os.cpu_count()
                or 4
            )
        n_workers = min(n_workers, len(files))

        schema_cfg = {
            "time_unit":     self._batching_cfg.get("time_unit",    "ns"),
            "duration_unit": self._schema_cfg.get("duration_unit",  "us"),
        }

        # Distribute files round-robin across workers
        shards: list[list[str]] = [[] for _ in range(n_workers)]
        for i, f in enumerate(files):
            shards[i % n_workers].append(f)

        # project_root is the 4th element — spawn workers use it to fix sys.path
        task_args = [
            (worker_id, shard_files, schema_cfg, self._project_root)
            for worker_id, shard_files in enumerate(shards)
            if shard_files
        ]

        print(
            f"\n[ParquetLoader] Dispatching {len(task_args)} shards "
            f"across {n_workers} workers ({len(files)} file(s) total)"
            f"\n[ParquetLoader] start_method=spawn (HPC-safe, avoids fork+thread deadlock)\n",
            flush=True,
        )

        results: list[Any] = [None] * len(task_args)

        # ── spawn context — the key HPC fix ──────────────────────────────────
        spawn_ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=n_workers, mp_context=spawn_ctx) as executor:
            future_map = {
                executor.submit(_load_shard, args): args[0]
                for args in task_args
            }
            for future in as_completed(future_map):
                worker_id, df, info = future.result()
                results[worker_id] = (worker_id, df, info)

        total_rows = sum(info["n_rows"] for _, _, info in results)
        print(
            f"\n[ParquetLoader] All workers done. "
            f"Total rows across all shards: {total_rows:,}\n",
            flush=True,
        )

        return results