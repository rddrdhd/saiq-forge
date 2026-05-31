import torch
import math

def build_enrichment_fn(baseline, feature_flags):
    """Returns a stateful function to map over the dataset based on config toggles."""
    
    # Unpack baselines
    rare_src_ips = set(baseline["categorical_baselines"]["rare_src_ips_sample"])
    num_profiles = baseline["numerical_profiles"]
    
    def robust_score(value, profile):
        median = profile["median"]
        iqr = profile["iqr"]
        
        if abs(iqr) < 1e-12:
            return 0.0
            
        score = (value - median) / iqr
        
        # Hard clip to prevent gradient explosions
        if score > 10.0: return 10.0
        if score < -10.0: return -10.0
        return score

    def enrich(batch):
        batch_features = []
        
        for i in range(len(batch["SRC IP"])):
            # Extract raw values
            duration = float(batch["DURATION"][i])
            src_bytes = float(batch["SRC BYTES"][i])
            dst_bytes = float(batch["DST BYTES"][i])
            src_packets = float(batch["SRC PACKETS"][i])
            dst_packets = float(batch["DST PACKETS"][i])
            src_ip = batch["SRC IP"][i]
            protocol = str(batch["PROTOCOL"][i]).upper()
            
            row_vector = []
            
            # ----------------------------------------------------
            # 1. ORIGINAL FEATURES (Log-scaled to prevent explosion)
            # ----------------------------------------------------
            if feature_flags.get("use_raw_duration", False):
                row_vector.append(math.log1p(max(0, duration)))
                
            if feature_flags.get("use_raw_src_bytes", False):
                row_vector.append(math.log1p(max(0, src_bytes)))
                
            if feature_flags.get("use_raw_dst_bytes", False):
                row_vector.append(math.log1p(max(0, dst_bytes)))
                
            if feature_flags.get("use_raw_src_packets", False):
                row_vector.append(math.log1p(max(0, src_packets)))
                
            if feature_flags.get("use_raw_dst_packets", False):
                row_vector.append(math.log1p(max(0, dst_packets)))

            # ----------------------------------------------------
            # 2. COMPUTED / ENRICHED FEATURES
            # ----------------------------------------------------
            if feature_flags.get("use_robust_duration", False):
                row_vector.append(robust_score(duration, num_profiles["DURATION"]))
                
            if feature_flags.get("use_robust_src_bytes", False):
                row_vector.append(robust_score(src_bytes, num_profiles["SRC BYTES"]))
                
            if feature_flags.get("use_robust_dst_bytes", False):
                row_vector.append(robust_score(dst_bytes, num_profiles["DST BYTES"]))

            if feature_flags.get("use_rare_src_ip", False):
                row_vector.append(1.0 if src_ip in rare_src_ips else 0.0)

            if feature_flags.get("use_protocol_encoding", False):
                # Simple one-hot encoding for the most common protocols
                row_vector.append(1.0 if protocol == "TCP" else 0.0)
                row_vector.append(1.0 if protocol == "UDP" else 0.0)
                row_vector.append(1.0 if protocol not in ["TCP", "UDP"] else 0.0)

            batch_features.append(row_vector)
            
        return {
            "FEATURES": batch_features
        }
        
    return enrich