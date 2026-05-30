"""
core/main.py
"""
import json
import sys
from pathlib import Path
import os
import torch
import torch.distributed as dist
from collections import defaultdict
from datasets import load_dataset
from torch.utils.data import DataLoader
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from core.config import load_config
from modules.parquet_loader import load_full_parquet, batch_sharded_parquet

rank = int(os.environ.get("SLURM_PROCID", 0))
world_size = int(os.environ.get("SLURM_NTASKS", 1))


rare_src_ips = None
num_profiles = None

def pprint(text):
    print(f"[R{rank}]: {text}")

def robust_score(value, profile):
    median = profile["median"]
    iqr = profile["iqr"]

    if abs(iqr) < 1e-12:
        return 0.0

    return (value - median) / iqr

def enrich_with_baseline(batch):

    rare_src_scores = []
    duration_scores = []

    for i in range(len(batch["SRC IP"])):

        src_ip = batch["SRC IP"][i]

        duration = float(batch["DURATION"][i])

        rare_src_scores.append(
            1.0 if src_ip in rare_src_ips else 0.0
        )

        duration_scores.append(
            robust_score(
                duration,
                num_profiles["DURATION"]
            )
        )

    return {
        "FEATURE_RARE_SRC_IP": rare_src_scores,
        "FEATURE_DURATION_DEV": duration_scores
    }
if __name__ == "__main__":
    cfg = load_config("config/default.yml")

    with open(cfg["output"]["file_baseline"], "r") as f:
        baseline = json.load(f)
    
        # lookup tables
        rare_src_ips = set(
            baseline["categorical_baselines"]["rare_src_ips_sample"]
        )

        rare_dst_ips = set(
            baseline["categorical_baselines"]["rare_dst_ips_sample"]
        )

        port_app_map = baseline["categorical_baselines"][
            "probabilistic_port_applications"
        ]

        num_profiles = baseline["numerical_profiles"]

        ratio_profiles = baseline["ratio_profiles"]
    

    dist.init_process_group(backend="gloo") # Use "nccl" for actual GPU training, "gloo" is safe for CPU/GPU testing

    dist.barrier()
    dataset = load_dataset("parquet", data_files=cfg["input"]["file_data"])["train"]
    sharded_dataset = dataset.shard(num_shards=world_size, index=rank)
    print(f"\n--- [Rank {rank}/{world_size}] Total rows assigned: {len(sharded_dataset)} ---")


    # Apply the enrichment on-the-fly using our dynamically built dictionary
    enriched_dataset = sharded_dataset.map(enrich_with_baseline, batched=True)
    
    # Set PyTorch format
    enriched_dataset.set_format(type="torch", columns=["DURATION", "FEATURE_RARE_SRC_IP", "FEATURE_DURATION_DEV"])
    dataloader = DataLoader(enriched_dataset, batch_size=cfg["nn"]["batch_size"])

    # Verify results
    for batch in dataloader:
        if rank == 0:
            print("\n--- Dynamically Learned Anomaly Scores (Rank 0) ---")
            print("Rare IP Scores:", batch["FEATURE_RARE_SRC_IP"])
            print("Feature duration:", batch["FEATURE_DURATION_DEV"])
        break
    # for batch_idx, batch in enumerate(dataloader): # returns dictionaries of tensors
    #     # print("\n--- Raw Data Dictionary ---", flush=True)
    #     # pprint(str(batch))

    #     for key, value in batch.items():
    #             if hasattr(value, "shape"):
    #                 print(f"Key: {key:<15} | Shape: {str(list(value.shape)):<12} | Type: {value.dtype}", flush=True)
    #             else:
    #                 print(f"Key: {key:<15} | Type: {type(value).__name__:<12} | Value: {value}", flush=True)

        
    # Clean up the distributed environment
    dist.destroy_process_group()