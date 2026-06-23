import os
import struct
import socket
import polars as pl
from scapy.utils import RawPcapReader

pcap_file = "data/CIC-IDS-2017_original/Friday-WorkingHours.pcap"
output_parquet = "data/CIC-IDS-2017_processed/Friday-WorkingHours.parquet"

print(f"Starting optimized multi-threaded parsing of {pcap_file}...")

# Temporary lists for fast block accumulation
timestamps = []
src_ips = []
dst_ips = []
sports = []
dports = []
protos = []
sizes = []

dfs = []
packet_count = 0
parsed_count = 0
chunk_size = 1_000_000  # Flush to Polars every 1M packets to keep memory flat

with RawPcapReader(pcap_file) as reader:
    for packet_bytes, packet_metadata in reader:
        packet_count += 1
        if packet_count % 1_000_000 == 0:
            print(f"Scanned {packet_count} raw frames...")

        if len(packet_bytes) < 34:  # Minimum bounds check (14 Eth + 20 IP)
            continue

        # Check for IPv4 EtherType (0x0800) at bytes 12-13
        if packet_bytes[12:14] != b'\x08\x00':
            continue

        # Protocol is at byte 23
        proto = packet_bytes[23]
        if proto not in (6, 17):  # We only aggregate TCP (6) and UDP (17)
            continue

        # Internet Header Length (IHL) is the lower 4 bits of byte 14
        ihl = (packet_bytes[14] & 0x0F) * 4
        l4_start = 14 + ihl

        if len(packet_bytes) < l4_start + 4:
            continue

        # Unpack Source Port and Destination Port from Layer 4
        sport, dport = struct.unpack('!HH', packet_bytes[l4_start:l4_start+4])

        # Convert IP bytes to strings using low-level socket operations
        src_ip = socket.inet_ntoa(packet_bytes[26:30])
        dst_ip = socket.inet_ntoa(packet_bytes[30:34])

        # --- FIX: PCAP vs PCAPNG Metadata Bridge ---
        if hasattr(packet_metadata, 'sec'):
            # Standard PCAP format
            ts_us = int(packet_metadata.sec * 1_000_000 + packet_metadata.usec)
        elif hasattr(packet_metadata, 'tshigh'):
            # PCAPNG format (PacketMetadataNg)
            ts = (packet_metadata.tshigh << 32) | packet_metadata.tslow
            tsresol = getattr(packet_metadata, 'tsresol', 1_000_000)
            if tsresol == 0: tsresol = 1_000_000 # Failsafe against division by zero
            ts_us = int((ts / tsresol) * 1_000_000)
        else:
            continue  # Failsafe if Scapy yields an unrecognized block type
            
        wirelen = getattr(packet_metadata, 'wirelen', len(packet_bytes))
        # -------------------------------------------

        # Append to primitives lists
        timestamps.append(ts_us)
        src_ips.append(src_ip)
        dst_ips.append(dst_ip)
        sports.append(sport)
        dports.append(dport)
        protos.append("TCP" if proto == 6 else "UDP")
        sizes.append(wirelen)
        parsed_count += 1

        # Periodic memory flush
        if parsed_count % chunk_size == 0:
            chunk_df = pl.DataFrame({
                "timestamp": timestamps, "src_ip": src_ips, "dst_ip": dst_ips,
                "sport": sports, "dport": dports, "proto": protos, "size": sizes
            }, schema={
                "timestamp": pl.Int64, "src_ip": pl.String, "dst_ip": pl.String,
                "sport": pl.Int32, "dport": pl.Int32, "proto": pl.String, "size": pl.Int64
            })
            dfs.append(chunk_df)
            timestamps, src_ips, dst_ips, sports, dports, protos, sizes = [], [], [], [], [], [], []

# Flush leftover frames
if src_ips:
    chunk_df = pl.DataFrame({
        "timestamp": timestamps, "src_ip": src_ips, "dst_ip": dst_ips,
        "sport": sports, "dport": dports, "proto": protos, "size": sizes
    }, schema={
        "timestamp": pl.Int64, "src_ip": pl.String, "dst_ip": pl.String,
        "sport": pl.Int32, "dport": pl.Int32, "proto": pl.String, "size": pl.Int64
    })
    dfs.append(chunk_df)

print(f"\nParsing complete. Extracted {parsed_count} L4 packets.")
print("Concatenating tracking matrix into Polars...")
df = pl.concat(dfs)

print("Running vectorized bidirectional flow aggregation in Polars...")

# 1. Orientation Sorting: Create direction-agnostic keys natively
is_fwd = (pl.col("src_ip") < pl.col("dst_ip")) | ((pl.col("src_ip") == pl.col("dst_ip")) & (pl.col("sport") <= pl.col("dport")))

df = df.with_columns(
    pl.when(is_fwd).then(pl.col("src_ip")).otherwise(pl.col("dst_ip")).alias("flow_src_ip"),
    pl.when(is_fwd).then(pl.col("sport")).otherwise(pl.col("dport")).alias("flow_src_port"),
    pl.when(is_fwd).then(pl.col("dst_ip")).otherwise(pl.col("src_ip")).alias("flow_dst_ip"),
    pl.when(is_fwd).then(pl.col("dport")).otherwise(pl.col("sport")).alias("flow_dst_port"),
)

group_cols = ["flow_src_ip", "flow_src_port", "flow_dst_ip", "flow_dst_port", "proto"]

# 2. Window processing: Identify who truly initiated the flow chronologically
df = df.with_columns(
    pl.col("src_ip").sort_by("timestamp").first().over(group_cols).alias("flow_initiator_ip")
)

# 3. Categorize packet directions relative to the true flow initiator
df = df.with_columns(
    pl.when(pl.col("src_ip") == pl.col("flow_initiator_ip")).then(1).otherwise(0).alias("is_src_pkt"),
    pl.when(pl.col("src_ip") != pl.col("flow_initiator_ip")).then(1).otherwise(0).alias("is_dst_pkt"),
    pl.when(pl.col("src_ip") == pl.col("flow_initiator_ip")).then(pl.col("size")).otherwise(0).alias("src_bytes_pkt"),
    pl.when(pl.col("src_ip") != pl.col("flow_initiator_ip")).then(pl.col("size")).otherwise(0).alias("dst_bytes_pkt"),
)

# 4. Multi-threaded group aggregation
agg_df = df.group_by(group_cols).agg([
    pl.col("timestamp").min().alias("TIME"),
    (pl.col("timestamp").max() - pl.col("timestamp").min()).alias("DURATION"),
    pl.col("src_ip").sort_by("timestamp").first().alias("SRC IP"),
    pl.col("sport").sort_by("timestamp").first().alias("SRC PORT"),
    pl.col("dst_ip").sort_by("timestamp").first().alias("DST IP"),
    pl.col("dport").sort_by("timestamp").first().alias("DST PORT"),
    pl.col("is_src_pkt").sum().alias("SRC PACKETS"),
    pl.col("is_dst_pkt").sum().alias("DST PACKETS"),
    pl.col("src_bytes_pkt").sum().alias("SRC BYTES"),
    pl.col("dst_bytes_pkt").sum().alias("DST BYTES"),
])

# 5. Calculate DUAL status, add PROTOCOL, and map APPLICATION via fast joins
well_known_ports = {21: "FTP", 22: "SSH", 80: "HTTP", 443: "SSL", 389: "LDAP", 3268: "LDAP"}
mapping_df = pl.DataFrame(
    {"PORT": list(well_known_ports.keys()), "APP_NAME": list(well_known_ports.values())},
    schema={"PORT": pl.Int32, "APP_NAME": pl.String}
)

agg_df = agg_df.with_columns(
    pl.when((pl.col("SRC PACKETS") > 0) & (pl.col("DST PACKETS") > 0)).then(1).otherwise(0).alias("DUAL"),
    pl.col("proto").alias("PROTOCOL")
)

agg_df = agg_df.join(mapping_df, left_on="SRC PORT", right_on="PORT", how="left").rename({"APP_NAME": "APP_SRC"})
agg_df = agg_df.join(mapping_df, left_on="DST PORT", right_on="PORT", how="left").rename({"APP_NAME": "APP_DST"})
agg_df = agg_df.with_columns(pl.coalesce(["APP_SRC", "APP_DST", pl.lit("UNKNOWN")]).alias("APPLICATION"))

# 6. Restructure precisely to matching schema columns order
final_df = agg_df.select([
    "TIME", "DURATION", "SRC IP", "SRC PORT", "DST IP", "DST PORT",
    "DUAL", "PROTOCOL", "APPLICATION", "SRC PACKETS", "DST PACKETS", "SRC BYTES", "DST BYTES"
])

# Make sure the output directory actually exists before saving
os.makedirs(os.path.dirname(output_parquet), exist_ok=True)

print(f"Saving fully aggregated flow records to {output_parquet}...")
final_df.write_parquet(output_parquet, compression="snappy")
print("Optimization task complete!")