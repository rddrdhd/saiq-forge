import json
import math
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc

from core.config import load_config

def calculate_entropy(array):
    """
    Calculates the system-wide Shannon Entropy of a categorical/discrete column.
    Formula: H(X) = -sum(P(x_i) * log2(P(x_i)))
    """
    vc = pc.value_counts(array)
    counts = vc.field("counts").to_pylist()
    total = sum(counts)
    if total == 0:
        return 0.0
    
    entropy = 0.0
    for c in counts:
        p = c / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy

def clean_timestamp_column(time_column):
    """
    Parses space-separated timestamp string format (e.g., '1 710 909 590 610 420')
    or raw integers into a clean float64 Unix timestamp in seconds.
    """
    try:
        if pa.types.is_string(time_column.type):
            cleaned_strings = pc.replace_substring_regex(time_column, pattern=" ", replacement="")
            float_array = pc.cast(cleaned_strings, pa.float64())
        else:
            float_array = pc.cast(time_column, pa.float64())
        
        return pc.divide(float_array, 1000000.0)
    except Exception:
        return pc.divide(pc.cast(time_column, pa.float64()), 1000000.0)

def generate_baseline(parquet_path, output_json_path):
    print("Opening parquet file and parsing schema...")
    dataset = pq.ParquetDataset(parquet_path)
    
    columns = [
        "DURATION", "SRC IP", "DST IP", "SRC PORT", "DST PORT", 
        "PROTOCOL", "APPLICATION", "SRC PACKETS", "DST PACKETS", 
        "SRC BYTES", "DST BYTES", "TIME"
    ]
    table = dataset.read(columns=columns)
    
    cleaned_time = clean_timestamp_column(table["TIME"])
    table = table.append_column("CLEANED_TIME", cleaned_time)
    
    if "DURATION" in table.column_names:
        cleaned_duration = pc.divide(pc.cast(table["DURATION"], pa.float64()), 1000000.0)
        # Swap out the raw microsecond column with the clean second column
        table = table.drop(["DURATION"]).append_column("DURATION", cleaned_duration)

    # Filter table for clean application profiling (ignoring UNKNOWN values)
    app_filter = pc.not_equal(table["APPLICATION"], "UNKNOWN")
    filtered_table = table.filter(app_filter)
    
    stats = {}

    # --- 1. OVERALL GLOBAL TRAFFIC STATISTICS ---
    print("Computing overall file traffic summaries...")
    total_flows = len(table)
    min_time = pc.min(table["CLEANED_TIME"]).as_py()
    max_time = pc.max(table["CLEANED_TIME"]).as_py()
    timespan_seconds = max_time - min_time if max_time and min_time else 1.0
    
    total_src_bytes = pc.sum(table["SRC BYTES"]).as_py() or 0
    total_dst_bytes = pc.sum(table["DST BYTES"]).as_py() or 0
    total_src_pkts = pc.sum(table["SRC PACKETS"]).as_py() or 0
    total_dst_pkts = pc.sum(table["DST PACKETS"]).as_py() or 0

    stats["global_summary"] = {
        "total_records": total_flows,
        "file_timespan_seconds": float(timespan_seconds),
        "total_bytes_transferred": int(total_src_bytes + total_dst_bytes),
        "total_packets_transferred": int(total_src_pkts + total_dst_pkts),
        "file_avg_bytes_per_sec": float((total_src_bytes + total_dst_bytes) / timespan_seconds),
        "file_avg_packets_per_sec": float((total_src_pkts + total_dst_pkts) / timespan_seconds)
    }

    # --- 2. HEAVY-TAILED NUMERICAL PROFILING ---
    print("Profiling numerical distributions via robust quantiles...")
    numerical_cols = ["DURATION", "SRC PACKETS", "DST PACKETS", "SRC BYTES", "DST BYTES"]
    stats["numerical_profiles"] = {}
    
    for col in numerical_cols:
        arr = table[col]
        q_vals = pc.quantile(arr, q=[0.25, 0.50, 0.75, 0.95, 0.99, 0.999]).to_pylist()
        iqr = q_vals[2] - q_vals[0]
        
        stats["numerical_profiles"][col] = {
            "min": float(pc.min(arr).as_py()),
            "max": float(pc.max(arr).as_py()),
            "mean": float(pc.mean(arr).as_py()),
            "stddev": float(pc.stddev(arr).as_py()),
            "p25": q_vals[0],
            "median": q_vals[1],
            "p75": q_vals[2],
            "p95": q_vals[3],
            "p99": q_vals[4],
            "p999": q_vals[5],
            "iqr": iqr
        }

    # --- 3. STRUCTURAL RATIO PROFILES ---
    print("Computing behavioral asymmetry metrics...")
    ratio_src_dst_bytes = pc.divide(table["SRC BYTES"], pc.add(table["DST BYTES"], 1))
    ratio_src_pkt_size = pc.divide(table["SRC BYTES"], pc.add(table["SRC PACKETS"], 1))
    
    stats["ratio_profiles"] = {
        "SRC_TO_DST_BYTES_ASYMMETRY": {
            "median": pc.quantile(ratio_src_dst_bytes, q=0.5)[0].as_py(),
            "p95": pc.quantile(ratio_src_dst_bytes, q=0.95)[0].as_py(),
            "p99": pc.quantile(ratio_src_dst_bytes, q=0.99)[0].as_py()
        },
        "SRC_AVG_PACKET_SIZE": {
            "median": pc.quantile(ratio_src_pkt_size, q=0.5)[0].as_py(),
            "p95": pc.quantile(ratio_src_pkt_size, q=0.95)[0].as_py(),
            "p99": pc.quantile(ratio_src_pkt_size, q=0.99)[0].as_py()
        }
    }

    # --- 4. GLOBAL INFORMATION ENTROPY ---
    print("Calculating system-wide feature entropies...")
    categorical_entropy_cols = ["SRC PORT", "DST PORT", "PROTOCOL", "APPLICATION"]
    stats["global_entropy"] = {}
    for col in categorical_entropy_cols:
        # Evaluate APPLICATION column using the filtered table to avoid 'UNKNOWN' bias
        source_array = filtered_table[col] if col == "APPLICATION" else table[col]
        stats["global_entropy"][col] = calculate_entropy(source_array)

    # --- 5. TOPOLOGICAL GRAPH STRUCTURAL PROFILE (Fan-Out) ---
    print("Profiling network structural connection boundaries...")
    grouped_graph = table.group_by("SRC IP").aggregate([
        ("DST IP", "count_distinct"),
        ("DST PORT", "count_distinct")
    ])
    
    dst_ip_agg_col = [c for c in grouped_graph.column_names if "DST IP" in c][0]
    dst_port_agg_col = [c for c in grouped_graph.column_names if "DST PORT" in c][0]
    
    stats["structural_limits"] = {
        "max_unique_dst_ips_per_src": int(pc.max(grouped_graph[dst_ip_agg_col]).as_py()),
        "p95_unique_dst_ips_per_src": float(pc.quantile(grouped_graph[dst_ip_agg_col], q=0.95)[0].as_py()),
        "max_unique_dst_ports_per_src": int(pc.max(grouped_graph[dst_port_agg_col]).as_py()),
        "p95_unique_dst_ports_per_src": float(pc.quantile(grouped_graph[dst_port_agg_col], q=0.95)[0].as_py())
    }

    # --- 6. CATEGORICAL EXCEPTIONS & PROBABILISTIC CO-OCCURRENCE MAPS ---
    print("Mapping context rules and structural rarities...")
    
    src_ip_vc = pc.value_counts(table["SRC IP"])
    rare_src_ips = [item["values"] for item in src_ip_vc.to_pylist() if item["counts"] < 3]
    
    dst_ip_vc = pc.value_counts(table["DST IP"])
    rare_dst_ips = [item["values"] for item in dst_ip_vc.to_pylist() if item["counts"] < 3]
    
    stats["categorical_baselines"] = {
        "rare_src_ips_sample": rare_src_ips[:2000],
        "rare_dst_ips_sample": rare_dst_ips[:2000]
    }
    
    # Calculate conditional probabilities: P(App | Port)
    port_app_group = filtered_table.group_by(["DST PORT", "APPLICATION"]).aggregate([("CLEANED_TIME", "count")])
    count_col = [c for c in port_app_group.column_names if "CLEANED_TIME" in c or "count" in c][0]
    
    port_totals_group = filtered_table.group_by("DST PORT").aggregate([("CLEANED_TIME", "count")])
    port_totals_col = [c for c in port_totals_group.column_names if "CLEANED_TIME" in c or "count" in c][0]
    port_totals_dict = {str(row["DST PORT"]): row[port_totals_col] for row in port_totals_group.to_pylist()}
    
    probabilistic_port_mapping = {}
    for row in port_app_group.to_pylist():
        port = str(row["DST PORT"])
        app = row["APPLICATION"]
        pair_count = row[count_col]
        total_port_count = port_totals_dict.get(port, 1)
        
        conditional_probability = pair_count / total_port_count
        
        # Keep application mapping ONLY if it accounts for >= 30% of traffic on that destination port
        if conditional_probability >= 0.30 and pair_count > 5:
            if port not in probabilistic_port_mapping:
                probabilistic_port_mapping[port] = []
            if app not in probabilistic_port_mapping[port]:
                probabilistic_port_mapping[port].append(app)
                
    stats["categorical_baselines"]["probabilistic_port_applications"] = probabilistic_port_mapping

    # --- 7. EXPORT ARTIFACT ---
    print(f"Writing comprehensive metrics to {output_json_path}...")
    with open(cfg["output"]["file_baseline"], "w") as f:
        json.dump(
            stats,
            f,
            indent=4,
            allow_nan=False
        )
    print("Baseline generation completed successfully!")

if __name__ == "__main__":
    cfg = load_config("config/default.yml")
    generate_baseline(cfg["input"]["file_data"], cfg["output"]["file_baseline"])