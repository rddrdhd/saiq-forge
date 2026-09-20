from dataclasses import dataclass


@dataclass(frozen=True)
class Flow:
    timestamp: float  # flow start, seconds since epoch
    duration: float  # seconds
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    application: str
    src_packets: int
    dst_packets: int
    src_bytes: int
    dst_bytes: int
