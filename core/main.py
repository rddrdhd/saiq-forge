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
from modules.parquet_loader import load_sharded_parquet

rank = int(os.environ.get("SLURM_PROCID", 0))
world_size = int(os.environ.get("SLURM_NTASKS", 1))
process_number = rank + 1

def pprint(text):
    print(f"[{process_number}/{world_size}]: {text}")

if __name__ == "__main__":
    cfg = load_config("config/my_default.yml")
    pprint("Start")
    df_geo = load_sharded_parquet(cfg["input"]["path_geo"], rank, world_size)
    df_data = load_sharded_parquet(cfg["input"]["path_data"], rank, world_size)
    pprint(f"Checking df_geo: {df_geo.shape}")
    if not df_geo.empty:
        pprint(f"{df_geo.head(2)}")
    pprint(f"Checking df_data: {df_data.shape}")
    if not df_data.empty:
        pprint(f"{df_data.head(2)}")
    pprint("Finish")
