import time
import torch
import torch.distributed as dist

def train_epoch(model, dataloader, optimizer, criterion, device, epoch, writer=None, rank=0):
    model.train()
    total_loss = 0.0
    local_sample_count = 0
    t_epoch_start = time.perf_counter()

    for batch_idx, batch in enumerate(dataloader):
        features = batch["FEATURES"].to(device).float()
        optimizer.zero_grad()
        reconstructed = model(features)

        loss = criterion(reconstructed, features).mean()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        local_sample_count += features.shape[0]

        # Log batch-level loss to TensorBoard
        if writer and rank == 0:
            global_step = epoch * len(dataloader) + batch_idx
            writer.add_scalar('Training/Batch_Loss', loss.item(), global_step)

    avg_loss = total_loss / len(dataloader)
    epoch_wall_seconds = time.perf_counter() - t_epoch_start

    # --- GLOBAL THROUGHPUT (tqe.tex Sec. 5.1 scaling numbers) ---
    # Sum samples across ranks, take the slowest rank's wall time as the
    # effective epoch duration (there's no DDP gradient sync here to force
    # ranks to lock-step, so they can drift).
    local_count_t = torch.tensor([local_sample_count], dtype=torch.float64, device=device)
    local_time_t = torch.tensor([epoch_wall_seconds], dtype=torch.float64, device=device)
    dist.all_reduce(local_count_t, op=dist.ReduceOp.SUM)
    dist.all_reduce(local_time_t, op=dist.ReduceOp.MAX)
    global_samples = local_count_t.item()
    max_epoch_seconds = local_time_t.item()
    throughput = global_samples / max_epoch_seconds if max_epoch_seconds > 0 else 0.0

    # Log epoch-level loss
    if writer and rank == 0:
        writer.add_scalar('Training/Epoch_Loss', avg_loss, epoch)
        writer.add_scalar('Training/Epoch_Seconds', max_epoch_seconds, epoch)
        writer.add_scalar('Training/Throughput_Samples_Per_Sec', throughput, epoch)
    if rank == 0:
        print(f"  epoch wall time (slowest rank): {max_epoch_seconds:.2f}s | "
              f"global throughput: {throughput:.1f} samples/sec ({int(global_samples)} samples total)")

    return avg_loss, {"epoch_seconds": max_epoch_seconds, "samples_per_sec": throughput,
                       "global_samples": global_samples}

def run_inference_and_flag(model, dataloader, criterion, device, rank, writer=None):
    """Runs data through the trained model, calculates global threshold, and flags anomalies."""
    model.eval()
    all_losses = []
    t_inference_start = time.perf_counter()

    with torch.no_grad():
        for batch in dataloader:
            features = batch["FEATURES"].to(device).float()
            reconstructed = model(features)
            per_record_loss = criterion(reconstructed, features).mean(dim=1)
            all_losses.append(per_record_loss)
    local_inference_seconds = time.perf_counter() - t_inference_start

    # Combine local losses
    all_losses = torch.cat(all_losses) if all_losses else torch.tensor([], device=device)
    # --- GLOBAL SYNCHRONIZATION ---
    # Use float64 to prevent numerical precision loss when summing massive datasets
    local_count = torch.tensor([len(all_losses)], dtype=torch.float64, device=device)
    local_sum = torch.sum(all_losses, dtype=torch.float64).unsqueeze(0) if len(all_losses) > 0 else torch.tensor([0.0], dtype=torch.float64, device=device)
    local_sum_sq = torch.sum(all_losses ** 2, dtype=torch.float64).unsqueeze(0) if len(all_losses) > 0 else torch.tensor([0.0], dtype=torch.float64, device=device)
    
    # Sum these values across all ranks
    dist.all_reduce(local_count, op=dist.ReduceOp.SUM)
    dist.all_reduce(local_sum, op=dist.ReduceOp.SUM)
    dist.all_reduce(local_sum_sq, op=dist.ReduceOp.SUM)
    
    global_count = local_count.item()
    
    if global_count == 0:
        return all_losses, []
        
    # Calculate global mean and standard deviation mathematically
    global_mean = (local_sum / local_count).item()
    global_var = (local_sum_sq / local_count) - (global_mean ** 2)
    # Ensure variance doesn't drop slightly below zero due to floating point math
    global_std = torch.sqrt(torch.clamp(global_var, min=0.0)).item() 
    
    threshold = global_mean + (3 * global_std)
    
    # --- FLAGGING ---
    # Every rank uses the exact same global threshold to flag its local records
    malicious_indices = (all_losses > threshold).nonzero(as_tuple=True)[0]
    
    # Sync the final counts for printing
    local_anomalies = torch.tensor([len(malicious_indices)], dtype=torch.int64, device=device)
    local_max_loss = torch.max(all_losses).unsqueeze(0) if len(all_losses) > 0 else torch.tensor([0.0], device=device)
    
    dist.all_reduce(local_anomalies, op=dist.ReduceOp.SUM)
    dist.all_reduce(local_max_loss, op=dist.ReduceOp.MAX)
    if writer and rank == 0:
        writer.add_histogram('Inference/Reconstruction_Errors', all_losses, 0)
        writer.add_scalar('Inference/Threshold', threshold, 0)
        writer.add_scalar('Inference/Anomalies_Found', local_anomalies.item(), 0)
    if rank == 0:
        print(f"\n--- Global Inference Stats ---")
        print(f"Total Records Processed: {int(global_count)}")
        print(f"Global Mean Loss: {global_mean:.6f} | Global StdDev: {global_std:.6f}")
        print(f"Global Anomaly Threshold: {threshold:.6f}")
        print(f"Found {local_anomalies.item()} potential anomalies globally.")
        
        if local_anomalies.item() > 0:
            print(f"Highest single anomaly score globally: {local_max_loss.item():.6f}")
            
    return all_losses, malicious_indices