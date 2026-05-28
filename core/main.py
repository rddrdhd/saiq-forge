"""
core/main.py
"""
import pandas as pd
import sys
from pathlib import Path
import os
import torch
import torch.distributed as dist
from datasets import load_dataset
from torch.utils.data import DataLoader
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

    dist.init_process_group(backend="gloo") # Use "nccl" for actual GPU training, "gloo" is safe for CPU/GPU testing

    dist.barrier()
    dataset = load_dataset("parquet", data_files=cfg["input"]["file_data"])["train"]
    sharded_dataset = dataset.shard(num_shards=world_size, index=rank)
    print(f"\n--- [Rank {rank}/{world_size}] Total rows assigned: {len(sharded_dataset)} ---")
    dataloader = DataLoader(sharded_dataset, batch_size=cfg["nn"]["batch_size"])
    
    for batch_idx, batch in enumerate(dataloader): # returns dictionaries of tensors
        # print("\n--- Raw Data Dictionary ---", flush=True)
        # pprint(str(batch))

        for key, value in batch.items():
                if hasattr(value, "shape"):
                    print(f"Key: {key:<15} | Shape: {str(list(value.shape)):<12} | Type: {value.dtype}", flush=True)
                else:
                    print(f"Key: {key:<15} | Type: {type(value).__name__:<12} | Value: {value}", flush=True)

        
    # Clean up the distributed environment
    dist.destroy_process_group()