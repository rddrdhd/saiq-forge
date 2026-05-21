"""
modules/ingestion/schema.py
───────────────────────────
Normalise raw flow columns into the canonical internal representation.

Reads column names from the config schema block so it is not hardcoded
to the exact field names in the parquet file.
"""

from __future__ import annotations
from typing import Any

import polars as pl

_TIME_UNIT_TO_NS: dict[str, int] = {
    "ns": 1,
    "us": 1_000,
    "ms": 1_000_000,
    "s":  1_000_000_000,
}

_DURATION_UNIT_TO_SEC: dict[str, float] = {
    "us": 1e-6,
    "ms": 1e-3,
    "s":  1.0,
}

REQUIRED_COLUMNS = [
    "TIME", "DURATION",
    "SRC_IP", "DST_IP", "SRC_PORT", "DST_PORT",
    "PROTOCOL", "APPLICATION", "DUAL",
    "SRC_PACKETS", "DST_PACKETS", "SRC_BYTES", "DST_BYTES",
]


def validate_columns(df: pl.LazyFrame | pl.DataFrame, schema_cfg: dict[str, Any] | None = None) -> None:
    """Raise ValueError if any required column is missing."""
    # Build expected names from config (or fall back to defaults)
    expected = list(REQUIRED_COLUMNS)
    if schema_cfg:
        expected = [
            schema_cfg.get("time_col", "TIME"),
            schema_cfg.get("duration_col", "DURATION"),
            schema_cfg.get("src_ip_col", "SRC_IP"),
            schema_cfg.get("dst_ip_col", "DST_IP"),
            schema_cfg.get("src_port_col", "SRC_PORT"),
            schema_cfg.get("dst_port_col", "DST_PORT"),
            schema_cfg.get("protocol_col", "PROTOCOL"),
            schema_cfg.get("application_col", "APPLICATION"),
            "DUAL",
            schema_cfg.get("src_packets_col", "SRC_PACKETS"),
            schema_cfg.get("dst_packets_col", "DST_PACKETS"),
            schema_cfg.get("src_bytes_col", "SRC_BYTES"),
            schema_cfg.get("dst_bytes_col", "DST_BYTES"),
        ]

    cols = df.collect_schema().names() if isinstance(df, pl.LazyFrame) else df.columns
    missing = [c for c in expected if c not in cols]
    if missing:
        raise ValueError(f"Missing required columns: {missing}\nFound: {cols}")


def normalize(
    lf: pl.LazyFrame,
    time_unit: str = "ns",
    duration_unit: str = "us",
) -> pl.LazyFrame:
    """
    Add derived columns to the LazyFrame:
      TIME_SEC, DATETIME, DURATION_SEC, SRC_BPP, DST_BPP,
      BYTE_ASYM, TOTAL_BYTES, TOTAL_PACKETS
    """
    if time_unit not in _TIME_UNIT_TO_NS:
        raise ValueError(f"time_unit must be one of {list(_TIME_UNIT_TO_NS)}")
    if duration_unit not in _DURATION_UNIT_TO_SEC:
        raise ValueError(f"duration_unit must be one of {list(_DURATION_UNIT_TO_SEC)}")

    time_ns_factor = _TIME_UNIT_TO_NS[time_unit]
    dur_factor = _DURATION_UNIT_TO_SEC[duration_unit]

    time_sec_expr = (pl.col("TIME").cast(pl.Float64) * time_ns_factor / 1e9).alias("TIME_SEC")

    if time_unit == "ns":
        datetime_expr = pl.from_epoch(pl.col("TIME"), time_unit="ns").alias("DATETIME")
    elif time_unit == "us":
        datetime_expr = pl.from_epoch(pl.col("TIME"), time_unit="us").alias("DATETIME")
    elif time_unit == "ms":
        datetime_expr = pl.from_epoch(pl.col("TIME"), time_unit="ms").alias("DATETIME")
    else:
        datetime_expr = pl.from_epoch(pl.col("TIME"), time_unit="s").alias("DATETIME")

    # Clip before deriving ratios
    lf = lf.with_columns([
        pl.col("SRC_PACKETS").clip(lower_bound=1),
        pl.col("DST_PACKETS").clip(lower_bound=0),
        pl.col("SRC_BYTES").clip(lower_bound=0),
        pl.col("DST_BYTES").clip(lower_bound=0),
    ])

    lf = lf.with_columns([
        time_sec_expr,
        datetime_expr,
        (pl.col("DURATION").cast(pl.Float64) * dur_factor).alias("DURATION_SEC"),
        (pl.col("SRC_BYTES") / pl.col("SRC_PACKETS").cast(pl.Float64)).alias("SRC_BPP"),
        (pl.col("DST_BYTES") / (pl.col("DST_PACKETS").cast(pl.Float64) + 1e-6)).alias("DST_BPP"),
        (pl.col("SRC_BYTES").cast(pl.Float64) /
         (pl.col("SRC_BYTES") + pl.col("DST_BYTES") + 1).cast(pl.Float64)).alias("BYTE_ASYM"),
        (pl.col("SRC_BYTES") + pl.col("DST_BYTES")).alias("TOTAL_BYTES"),
        (pl.col("SRC_PACKETS") + pl.col("DST_PACKETS")).alias("TOTAL_PACKETS"),
    ])

    return lf


def summary(df: pl.DataFrame) -> dict:
    """Lightweight data-quality summary — used in run_metadata.json."""
    t_min = df["TIME_SEC"].min()
    t_max = df["TIME_SEC"].max()
    return {
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "time_range_sec": round(t_max - t_min, 2),
        "unique_src_ips": df["SRC_IP"].n_unique(),
        "unique_dst_ips": df["DST_IP"].n_unique(),
        "protocols": df["PROTOCOL"].value_counts().to_dicts(),
        "null_counts": {c: df[c].null_count() for c in df.columns if df[c].null_count() > 0},
    }