import torch

def train_epoch(model, dataloader, optimizer, criterion, device):
    """Trains the model for a single epoch and returns the average loss."""
    model.train()
    total_loss = 0.0
    
    for batch in dataloader:
        features = batch["FEATURES"].to(device).float()
        
        optimizer.zero_grad()
        reconstructed = model(features)
        
        # Calculate mean loss for the backward pass
        loss = criterion(reconstructed, features).mean()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        
    return total_loss / len(dataloader)

def run_inference_and_flag(model, dataloader, criterion, device, rank):
    """Runs data through the trained model, calculates threshold, and flags anomalies."""
    model.eval()
    all_losses = []
    
    # 1. Collect all reconstruction errors without tracking gradients
    with torch.no_grad():
        for batch in dataloader:
            features = batch["FEATURES"].to(device).float()
            reconstructed = model(features)
            
            # Get per-record loss (do not average across the batch)
            per_record_loss = criterion(reconstructed, features).mean(dim=1)
            all_losses.append(per_record_loss)
            
    # Combine all batch losses into a single 1D tensor
    all_losses = torch.cat(all_losses)
    
    # 2. Calculate the statistical threshold (Mean + 3 * StdDev)
    loss_mean = all_losses.mean().item()
    loss_std = all_losses.std().item()
    threshold = loss_mean + (3 * loss_std)
    
    if rank == 0:
        print(f"\n--- Inference Stats ---")
        print(f"Mean Loss: {loss_mean:.6f} | StdDev: {loss_std:.6f}")
        print(f"Anomaly Threshold: {threshold:.6f}")
    
    # 3. Flag the malicious records
    malicious_indices = (all_losses > threshold).nonzero(as_tuple=True)[0]
    
    if rank == 0:
        print(f"Found {len(malicious_indices)} potential anomalies out of {len(all_losses)} records.")
        
        # Print the highest loss value found
        if len(malicious_indices) > 0:
            max_loss = all_losses.max().item()
            print(f"Highest single anomaly score: {max_loss:.6f}")
            
    return all_losses, malicious_indices