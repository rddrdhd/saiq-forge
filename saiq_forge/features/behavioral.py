from saiq_forge.features.base import FeatureExtractor
from saiq_forge.features.registry import register


@register("B")
class BehavioralFeatures(FeatureExtractor):
    modality = "B"

    def extract(self, window):
        records = window.records
        if not records:
            return {
                "flow_count": 0,
                "unique_src_ips": 0,
                "unique_dst_ips": 0,
                "mean_src_bytes": 0.0,
                "mean_dst_bytes": 0.0,
            }

        return {
            "flow_count": len(records),
            "unique_src_ips": len({r.src_ip for r in records}),
            "unique_dst_ips": len({r.dst_ip for r in records}),
            "mean_src_bytes": sum(r.src_bytes for r in records) / len(records),
            "mean_dst_bytes": sum(r.dst_bytes for r in records) / len(records),
        }
