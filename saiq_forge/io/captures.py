import csv
from pathlib import Path
from typing import List

from saiq_forge.io.schema import Flow

# Real captures (datasets A/B/C) ship as semicolon-delimited flow records
# with TIME/DURATION in microseconds since epoch, not raw pcaps.
_MICROS = 1_000_000


def load_capture(path) -> List[Flow]:
    flows = []
    with open(Path(path), newline="") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        for row in reader:
            flows.append(Flow(
                timestamp=int(row["TIME"]) / _MICROS,
                duration=int(row["DURATION"]) / _MICROS,
                src_ip=row["SRC IP"],
                dst_ip=row["DST IP"],
                src_port=int(row["SRC PORT"]),
                dst_port=int(row["DST PORT"]),
                protocol=row["PROTOCOL"],
                application=row["APPLICATION"],
                src_packets=int(row["SRC PACKETS"]),
                dst_packets=int(row["DST PACKETS"]),
                src_bytes=int(row["SRC BYTES"]),
                dst_bytes=int(row["DST BYTES"]),
            ))
    return flows
