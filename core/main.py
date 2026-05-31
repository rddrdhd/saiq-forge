import json
import sys
import os
from pathlib import Path
import torch
import torch.distributed as dist
import torch.nn as nn
from datasets import load_dataset
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from core.config import load_config
from modules.data_enrichment import build_enrichment_fn
from modules.models.autoencoder import NetworkAutoencoder
from modules.engine import train_epoch, run_inference_and_flag

rank = int(os.environ.get("SLURM_PROCID", 0))
world_size = int(os.environ.get("SLURM_NTASKS", 1))
local_rank = int(os.environ.get("LOCAL_RANK", 0))

def pprint(text):
    if rank == 0:
        print(f"[Main]: {text}")

if __name__ == "__main__":
    cfg = load_config("config/default.yml")
    pprint(f'Running SAIQ-forge with data from {cfg["input"]["file_data"]} and { cfg["output"]["file_baseline"]}')
    # Load Baselines
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
    # Model Setup
    model_type = cfg["nn"].get("model_type", "autoencoder")
    learning_rate = cfg["nn"].get("learning_rate", 0.001)

    if model_type == "autoencoder":
        # Pull architecture params from config
        hidden_dims = cfg["nn"]["autoencoder"].get("encoder_hidden_dims", [16, 8])
        latent_dim = cfg["nn"]["autoencoder"].get("latent_dim", 4)
        
        model = NetworkAutoencoder(
            input_dim=input_dim, 
            hidden_dims=hidden_dims, 
            latent_dim=latent_dim
        ).to(device)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss(reduction='none')
    
    # Setup TensorBoard Writer (Only on Rank 0 so we don't duplicate logs)
    writer = None
    if rank == 0:
        writer = SummaryWriter(log_dir="outputs/runs/autoencoder_experiment_1")

    # --- Phase 1: Training ---
    epochs = cfg["nn"].get("epochs", 5)
    pprint(f"Starting Phase 1: Training {model_type.upper()} for {epochs} epochs...")
    
    for epoch in range(epochs):
        avg_train_loss = train_epoch(model, dataloader, optimizer, criterion, device, epoch, writer, rank)
        pprint(f"Epoch [{epoch+1}/{epochs}] - Loss: {avg_train_loss:.6f}")

    # --- Phase 2: Static Inference & Flagging ---
    pprint("Starting Phase 2: Static Inference and Anomaly Flagging...")
    all_scores, malicious_indices = run_inference_and_flag(model, dataloader, criterion, device, rank, writer)

    if writer:
        writer.close()
    dist.destroy_process_group()