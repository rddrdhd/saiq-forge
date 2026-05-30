import json
import pyarrow.parquet as pq
import pyarrow.compute as pc
from collections import Counter

from core.config import load_config

def generate_baseline(parquet_path, output_json_path):
    print("Opening parquet file ...")
    dataset = pq.ParquetDataset(parquet_path)
    
    # 1. Calculate numerical extremes using PyArrow Compute (Fast & memory-efficient)
    table = dataset.read(columns=["DURATION", "SRC BYTES"])
    
    stats = {
        "DURATION": {
            "min": float(pc.min(table["DURATION"]).as_py()),
            "max": float(pc.max(table["DURATION"]).as_py()),
            "mean": float(pc.mean(table["DURATION"]).as_py()),
            "std": float(pc.stddev(table["DURATION"]).as_py()),
        },
        "SRC_BYTES": {
            "mean": float(pc.mean(table["SRC BYTES"]).as_py()),
            "std": float(pc.stddev(table["SRC BYTES"]).as_py()),
        },
        "RARE_IPS": []
    }
    
    # 2. Find Categorical Extremes (Rare IPs)
    print("Analyzing IP frequencies...")
    ip_table = dataset.read(columns=["SRC IP"])
    # Convert chunked array to python list and count occurrences
    ip_counts = Counter(ip_table["SRC IP"].to_pylist())
    
    # Flag any IP that appears less than 3 times as a "rare/suspicious" IP
    rare_ips = [ip for ip, count in ip_counts.items() if count < 3]
    stats["RARE_IPS"] = rare_ips

    # 3. Save as a JSON artifact
    with open(output_json_path, "w") as f:
        json.dump(stats, f, indent=4)
    print(f"Baseline saved successfully to {output_json_path}!")

if __name__ == "__main__":
    cfg = load_config("config/default.yml")
    generate_baseline(cfg["input"]["file_data"], cfg["output"]["file_baseline"])