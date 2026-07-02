import os
from datetime import datetime
import torch
import torch.nn as nn
import torch.distributed as dist
from torch.utils.tensorboard import SummaryWriter

from core.modules.models.autoencoder import NetworkAutoencoder
from core.modules.engine import train_epoch, run_inference_and_flag

def get_model(model_type: str, input_dim: int, nn_cfg: dict, device: torch.device):
    """
    Factory function to choose the model. (TODO: add ELIFs)
    """
    if model_type == "autoencoder":
        hidden_dims = nn_cfg.get("autoencoder", {}).get("encoder_hidden_dims", [16, 8])
        latent_dim = nn_cfg.get("autoencoder", {}).get("latent_dim", 4)
        
        model = NetworkAutoencoder(
            input_dim=input_dim, 
            hidden_dims=hidden_dims, 
            latent_dim=latent_dim
        )
        return model.to(device)
    
    # elif model_type == "vae":
    #     return VariationalAutoencoder(...).to(device)
    
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def run_training_pipeline(cfg: dict, dataloader: torch.utils.data.DataLoader, input_dim: int, device: torch.device, rank: int):
    """
    Run training pipeline
    """
    def pprint(text):
        if rank == 0:
            print(f"[Training]: {text}")

    # Load params from config
    nn_cfg = cfg.get("nn", {})
    model_type = nn_cfg.get("model_type", "autoencoder")
    learning_rate = nn_cfg.get("learning_rate", 0.001)
    epochs = nn_cfg.get("epochs", 5)

    # Init model, optimizer & criterion
    model = get_model(model_type, input_dim, nn_cfg, device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss(reduction='none')
    
    # TensorBoard Writer (only rank 0)
    writer = None
    if rank == 0:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_dir = f"{cfg['output'].get('dir_tensorboard','outputs/runs/default')}/run_{timestamp}"
        writer = SummaryWriter(log_dir=run_dir)

    # --- Phase 1: Training ---
    pprint(f"Starting Phase 1: Training {model_type.upper()} for {epochs} epochs...")
    for epoch in range(epochs):
        avg_train_loss = train_epoch(model, dataloader, optimizer, criterion, device, epoch, writer, rank)
        pprint(f"Epoch [{epoch+1}/{epochs}] - Loss: {avg_train_loss:.6f}")

    # --- Phase 2: Static Inference & Flagging ---
    pprint("Starting Phase 2: Static Inference and Anomaly Flagging...")
    all_scores, malicious_indices = run_inference_and_flag(model, dataloader, criterion, device, rank, writer)

    # Clean up Tensorboard
    if writer:
        writer.close()
        
    return all_scores, malicious_indices