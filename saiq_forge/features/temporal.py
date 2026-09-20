from saiq_forge.features.base import FeatureExtractor
from saiq_forge.features.registry import register


@register("T")
class TemporalFeatures(FeatureExtractor):
    modality = "T"

    def extract(self, window):
        records = window.records
        if not records:
            return {
                "packet_rate": 0.0,
                "byte_rate": 0.0,
                "mean_inter_arrival": 0.0,
                "mean_duration": 0.0,
            }

        span = max(window.end - window.start, 1e-9)
        timestamps = sorted(r.timestamp for r in records)
        inter_arrivals = [b - a for a, b in zip(timestamps, timestamps[1:])]
        total_packets = sum(r.src_packets + r.dst_packets for r in records)
        total_bytes = sum(r.src_bytes + r.dst_bytes for r in records)

        return {
            "packet_rate": total_packets / span,
            "byte_rate": total_bytes / span,
            "mean_inter_arrival": (
                sum(inter_arrivals) / len(inter_arrivals) if inter_arrivals else 0.0
            ),
            "mean_duration": sum(r.duration for r in records) / len(records),
        }
