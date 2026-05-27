"""
core/main.py
"""
import pandas as pd
import sys
from pathlib import Path
import os

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from core.config import load_config
from modules.parquet_loader import load_full_parquet, batch_sharded_parquet

rank = int(os.environ.get("SLURM_PROCID", 0))
world_size = int(os.environ.get("SLURM_NTASKS", 1))

def pprint(text):
    print(f"[R{rank}]: {text}")

if __name__ == "__main__":
    cfg = load_config("config/my_default.yml")

    df_geo = load_full_parquet(cfg["input"]["file_geo"])
    pprint(f"Checking df_geo: {df_geo.shape}")
    if not df_geo.empty:
        pprint(f"{df_geo.head(2)}")

    pprint("Loading shards")
    GROUPS_PER_BATCH = 1 # set 1 for small batches, 5 for bigger - TODO tunable parameter
    data_generator = batch_sharded_parquet(cfg["input"]["file_data"], rank, world_size, groups_per_batch=GROUPS_PER_BATCH)
    pprint("Shard generator loaded")
    for batch_idx, df_batch_data in enumerate(data_generator):
            pprint("===============")
            pprint(f"Working on batch {batch_idx + 1}, shape: {df_batch_data.shape}: {df_batch_data.head(5)}")
    pprint("Shards generated")

