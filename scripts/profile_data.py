import os
import json
import math
import socket
import struct
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
import matplotlib.pyplot as plt

from core.config import load_config

def ip_to_int(ip_series):
    """Fast vector conversion of IP strings to unit32 integers for merge_asof."""
    def convert(ip):
        try:
            return struct.unpack("!I", socket.inet_aton(str(ip)))[0]
        except Exception:
            return 0
    return ip_series.apply(convert)

def calculate_entropy(array):
    """Calculates the system-wide Shannon Entropy of a categorical/discrete column."""
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
    """Parses space-separated timestamp string format or raw integers into clean float64 Unix seconds."""
    try:
        if pa.types.is_string(time_column.type):
            cleaned_strings = pc.replace_substring_regex(time_column, pattern=" ", replacement="")
            float_array = pc.cast(cleaned_strings, pa.float64())
        else:
            float_array = pc.cast(time_column, pa.float64())
        
        return pc.divide(float_array, 1000000.0)
    except Exception:
        return pc.divide(pc.cast(time_column, pa.float64()), 1000000.0)

def generate_plots(report_dir, country_counts, times, protocol_counts):
    """Generates and writes high-quality static diagnostic plots to disk."""
    print("Generating profile diagnostic visualization graphics...")
    plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
    
    # 1. Top Target Countries Plot
    if not country_counts.empty:
        plt.figure(figsize=(10, 5))
        country_counts.head(10).plot(kind='bar', color='#1f77b4', edgecolor='black')
        plt.title("Top 10 Destination Countries by Network Flow Volume", fontsize=12, fontweight='bold')
        plt.xlabel("Country", fontsize=10)
        plt.ylabel("Total Flows Logged", fontsize=10)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(report_dir, "top_countries.png"), dpi=150)
        plt.close()

    # 2. Traffic Volume Over Time Plot
    plt.figure(figsize=(12, 4.5))
    counts, bins = np.histogram(times, bins=60)
    plt.fill_between(bins[:-1], counts, color='#ff7f0e', alpha=0.6, edgecolor='#d62728', linewidth=1.5)
    plt.title("Network Capture Traffic Density Timeline (Flows per Bin)", fontsize=12, fontweight='bold')
    plt.xlabel("Relative Timeline (Seconds)", fontsize=10)
    plt.ylabel("Active Conversational Flow Count", fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(report_dir, "traffic_over_time.png"), dpi=150)
    plt.close()

    # 3. Protocol Distribution Plot
    if not protocol_counts.empty:
        plt.figure(figsize=(8, 5))
        protocol_counts.plot(kind='pie', autopct='%1.1f%%', startangle=140, 
                             colors=['#2ca02c', '#9467bd', '#bcbd22', '#17becf'])
        plt.title("Protocol Utilization Matrix Distribution", fontsize=12, fontweight='bold')
        plt.ylabel("")  # Clear target default label
        plt.tight_layout()
        plt.savefig(os.path.join(report_dir, "protocol_distribution.png"), dpi=150)
        plt.close()

def generate_baseline(parquet_path, geo_parquet_path, output_json_path, report_dir="reports"):
    os.makedirs(report_dir, exist_ok=True)
    print("Opening network data parquet file and parsing schema...")
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
        table = table.drop(["DURATION"]).append_column("DURATION", cleaned_duration)

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

    # --- 2. VECTORIZED GEOGRAPHIC THREAT INTEL PROFILING ---
    print("Enriching network telemetry with vectorized GeoIP tables...")
    country_counts_series = pd.Series(dtype=int)
    try:
        df_geo = pd.read_parquet(geo_parquet_path).sort_values('start_ip_num')
        
        # Pull distinct target IPs with structural value counts straight out of PyArrow
        dst_vc = pc.value_counts(table["DST IP"])
        df_unique_dst = pd.DataFrame({
            'DST IP': dst_vc.field("values").to_pylist(),
            'flow_count': dst_vc.field("counts").to_pylist()
        })
        
        df_unique_dst['IP_NUM'] = ip_to_int(df_unique_dst['DST IP'])
        df_unique_dst = df_unique_dst.sort_values('IP_NUM')
        

        df_unique_dst['IP_NUM'] = df_unique_dst['IP_NUM'].astype('int64')
        df_geo['start_ip_num'] = df_geo['start_ip_num'].astype('int64')
        df_geo['end_ip_num'] = df_geo['end_ip_num'].astype('int64')
        # Blazing fast merge_asof interval connection
        merged_geo = pd.merge_asof(df_unique_dst, df_geo, left_on='IP_NUM', right_on='start_ip_num', direction='backward')
        valid_geo = merged_geo[merged_geo['IP_NUM'] <= merged_geo['end_ip_num']]
        
        country_counts_series = valid_geo.groupby('country_name')['flow_count'].sum().sort_values(ascending=False)
        stats["geo_profile"] = {
            "top_countries": country_counts_series.head(15).to_dict()
        }
    except Exception as e:
        print(f"⚠️ GeoIP Mapping Failed: {e}. Skipping contextual additions.")
        # incompatible merge keys [0] dtype('int64') and dtype('uint32'), must be the same type. Skipping contextual additions.
        stats["geo_profile"] = {"error": str(e)}

    # --- 3. HEAVY-TAILED NUMERICAL PROFILING ---
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

    # --- 4. STRUCTURAL RATIO PROFILES ---
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

    # --- 5. GLOBAL INFORMATION ENTROPY ---
    print("Calculating system-wide feature entropies...")
    categorical_entropy_cols = ["SRC PORT", "DST PORT", "PROTOCOL", "APPLICATION"]
    stats["global_entropy"] = {}
    for col in categorical_entropy_cols:
        source_array = filtered_table[col] if col == "APPLICATION" else table[col]
        stats["global_entropy"][col] = calculate_entropy(source_array)

    # --- 6. TOPOLOGICAL GRAPH STRUCTURAL PROFILE (Fan-Out) ---
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

    # --- 7. CATEGORICAL EXCEPTIONS & PROBABILISTIC MAPS ---
    print("Mapping context rules and structural rarities...")
    src_ip_vc = pc.value_counts(table["SRC IP"])
    rare_src_ips = [item["values"] for item in src_ip_vc.to_pylist() if item["counts"] < 3]
    
    dst_ip_vc = pc.value_counts(table["DST IP"])
    rare_dst_ips = [item["values"] for item in dst_ip_vc.to_pylist() if item["counts"] < 3]
    
    stats["categorical_baselines"] = {
        "rare_src_ips_sample": rare_src_ips[:2000],
        "rare_dst_ips_sample": rare_dst_ips[:2000]
    }
    
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
        
        if conditional_probability >= 0.30 and pair_count > 5:
            if port not in probabilistic_port_mapping:
                probabilistic_port_mapping[port] = []
            if app not in probabilistic_port_mapping[port]:
                probabilistic_port_mapping[port].append(app)
                
    stats["categorical_baselines"]["probabilistic_port_applications"] = probabilistic_port_mapping

    # --- 8. GRAPHIC VISUALIZATION GENERATION ---
    proto_vc = pc.value_counts(table["PROTOCOL"])
    protocol_counts_series = pd.Series(
        proto_vc.field("counts").to_pylist(),
        index=proto_vc.field("values").to_pylist()
    )
    times_array = table["CLEANED_TIME"].to_numpy()
    
    generate_plots(report_dir, country_counts_series, times_array, protocol_counts_series)

    # --- 9. EXPORT ARTIFACT ---
    print(f"Writing comprehensive metrics to {output_json_path}...")
    with open(output_json_path, "w") as f:
        json.dump(stats, f, indent=4, allow_nan=False)
        
    # --- 10. BRIEF TERMINAL SUMMARY LOG ---
    print("\n" + "="*50)
    print("📊 DATASET TRAFFIC PROFILE COMPLETED SUCCESSFULY")
    print("="*50)
    print(f"Total Flows Audited  : {total_flows:,}")
    print(f"Dataset Timespan     : {timespan_seconds:,.2f} seconds")
    print(f"Total Volumetric Payload : {(total_src_bytes + total_dst_bytes) / (1024**2):,.2f} MB")
    if not country_counts_series.empty:
        print(f"Top Country Location : {country_counts_series.index[0]} ({country_counts_series.iloc[0]:,} flows)")
    print(f"Diagnostic Plots Output Folder: ./{report_dir}/")
    print("="*50 + "\n")

if __name__ == "__main__":
    cfg = load_config("config/default.yml")
    print(f'Profiling data from {cfg["input"]["file_data"]} using GeoIP database {cfg["input"]["file_geo"]}')
    generate_baseline(
        parquet_path=cfg["input"]["file_data"], 
        geo_parquet_path=cfg["input"]["file_geo"],
        output_json_path=cfg["output"]["file_baseline"],
        report_dir=cfg["output"]["dir_reports"]
    )