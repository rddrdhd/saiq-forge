import json
import sys
import os
from pathlib import Path
import torch
import torch.distributed as dist
from datasets import load_dataset
from torch.utils.data import DataLoader

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from core.config import load_config
from core.modules.data_enrichment import build_enrichment_fn
from core.modules.training import run_training_pipeline

rank = int(os.environ.get("SLURM_PROCID", 0))
world_size = int(os.environ.get("SLURM_NTASKS", 1))
local_rank = int(os.environ.get("LOCAL_RANK", 0))

def pprint(text):
    if rank == 0:
        print(f"[Main]: {text}")

if __name__ == "__main__":
    cfg = load_config("config/default.yml")
    pprint(f'Running SAIQ-forge with data from {cfg["input"]["file_data"]} and {cfg["output"]["file_baseline"]}')
    
    # Load pre-generated baselines
    with open(cfg["output"]["file_baseline"], "r") as f:
        baseline = json.load(f)
        rare_src_ips = set(baseline["categorical_baselines"]["rare_src_ips_sample"])
        num_profiles = baseline["numerical_profiles"]

    dist.init_process_group(backend="gloo") 
    device = torch.device(f"cuda:{local_rank}" if torch.cuda.is_available() else "cpu")

    # Data Loading
    dataset = load_dataset("parquet", data_files=cfg["input"]["file_data"])["train"]
    sharded_dataset = dataset.shard(num_shards=world_size, index=rank)
    
    feature_flags = cfg["nn"].get("features", {})
    enrich_fn = build_enrichment_fn(baseline, feature_flags)
    
    enriched_dataset = sharded_dataset.map(enrich_fn, batched=True)
    enriched_dataset.set_format(type="torch", columns=["FEATURES"])
    
    dataloader = DataLoader(enriched_dataset, batch_size=cfg["nn"]["batch_size"])
    input_dim = next(iter(dataloader))["FEATURES"].shape[1]
    
    if rank == 0:
        first_batch = next(iter(dataloader))
        features_check = first_batch["FEATURES"].float()
        print("\n--- Tensor Sanity Check ---")
        print(f"Batch Shape: {list(features_check.shape)}")
        print(f"Global Min:  {features_check.min().item():.4f}")
        print(f"Global Max:  {features_check.max().item():.4f}")
        print(f"Global Mean: {features_check.mean().item():.4f}")
        print("---------------------------\n")
    dist.barrier()

    # --- Training ---
    all_scores, malicious_indices = run_training_pipeline(
        cfg=cfg, 
        dataloader=dataloader, 
        input_dim=input_dim, 
        device=device, 
        rank=rank
    )

    dist.destroy_process_group()