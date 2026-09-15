"""
scripts/build_qml_pilot_dataset.py
───────────────────────────────────
Recovers ground-truth attack/benign labels for CICIDS2017 Friday traffic by
joining the official CICFlowMeter-labelled flow CSVs
(data/CIC-IDS-2017_original/GeneratedLabelledFlows.zip) onto our own
pcap->parquet flow features (data/CIC-IDS-2017_processed/Friday-WorkingHours.parquet).

scripts/fast_pcap_to_parquet.py does not carry labels through, so without this
join there is no ground truth to train or score a classifier against - this is
step 0 of the RQ5 minimal pilot (see CLAUDE.md "Immediate direction").

Join key: SRC IP, DST IP, SRC PORT, DST PORT, PROTOCOL (mapped TCP/UDP -> IANA
number), and flow-start minute (the labelled CSV's Timestamp has only minute
resolution, so this is necessarily coarse). CICFlowMeter and our own pcap
parser don't necessarily agree on which side of a flow is "source" - both
orientations are tried. Any flow or label row that ends up matching more than
once (either orientation, either side) is dropped as ambiguous rather than
guessed at, and the drop rate is reported.

Output: a small labelled parquet with the top-K (by mutual information)
numeric flow features + binary label, ready for the VQC-vs-MLP pilot script.

Run inside saiq-forge.sif (pandas/pyarrow/scikit-learn only - no quantum libs
needed for this step):
    singularity exec --bind "/pfs,/scratch,/project" --pwd $PWD saiq-forge.sif \
        python3 scripts/build_qml_pilot_dataset.py --top_k=4
"""
import argparse
import zipfile
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from sklearn.feature_selection import mutual_info_classif

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LABELLED_ZIP = PROJECT_ROOT / "data/CIC-IDS-2017_original/GeneratedLabelledFlows.zip"
OUR_PARQUET = PROJECT_ROOT / "data/CIC-IDS-2017_processed/Friday-WorkingHours.parquet"
OUT_PATH = PROJECT_ROOT / "data/generated-outputs/qml_pilot_cicids2017.parquet"

# These three cover the full Friday-WorkingHours.pcap we process.
FRIDAY_LABEL_FILES = [
    "TrafficLabelling /Friday-WorkingHours-Morning.pcap_ISCX.csv",
    "TrafficLabelling /Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
    "TrafficLabelling /Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
]
PROTO_TO_NUM = {"TCP": 6, "UDP": 17}
NUMERIC_FEATURES = ["DURATION", "SRC PACKETS", "DST PACKETS", "SRC BYTES", "DST BYTES"]


def load_labels() -> pd.DataFrame:
    # Known CICIDS2017 quirk: the "Afternoon" files' Timestamp column was
    # written in 12-hour format with no AM/PM marker, so e.g. the DDoS file
    # (documented attack window ~15:56-16:16) shows hours like "3:41"-"4:19".
    # Verified against this exact release by inspecting the raw values -
    # DDoS hours fall in 3-4, PortScan in 1-2, both consistent with PM once
    # shifted +12h and inconsistent with their documented attack windows
    # otherwise. The Morning file uses a genuine 24h clock and needs no fix.
    frames = []
    with zipfile.ZipFile(LABELLED_ZIP) as z:
        for name in FRIDAY_LABEL_FILES:
            with z.open(name) as f:
                df = pd.read_csv(f, encoding="latin1")
            df.columns = [c.strip() for c in df.columns]
            df["_pm_fix"] = "Afternoon" in name
            frames.append(df)
    labels = pd.concat(frames, ignore_index=True)
    labels = labels.rename(columns={
        "Source IP": "SRC IP", "Source Port": "SRC PORT",
        "Destination IP": "DST IP", "Destination Port": "DST PORT",
        "Protocol": "PROTOCOL_NUM",
    })
    ts = pd.to_datetime(labels["Timestamp"], format="%d/%m/%Y %H:%M", errors="coerce")
    if ts.isna().mean() > 0.5:  # some CICIDS2017 dumps use m/d/Y instead of d/m/Y
        ts = pd.to_datetime(labels["Timestamp"], format="%m/%d/%Y %H:%M", errors="coerce")
    ts = ts + pd.to_timedelta(labels["_pm_fix"].astype(int) * 12, unit="h")
    labels["MINUTE"] = ts.dt.floor("min")
    labels["PROTOCOL_NUM"] = pd.to_numeric(labels["PROTOCOL_NUM"], errors="coerce").astype("Int64")
    labels["LABEL_BIN"] = (labels["Label"].str.upper() != "BENIGN").astype(int)
    labels["_label_id"] = range(len(labels))
    return labels[["SRC IP", "SRC PORT", "DST IP", "DST PORT", "PROTOCOL_NUM", "MINUTE",
                    "Label", "LABEL_BIN", "_label_id"]]


def load_flows() -> pd.DataFrame:
    df = pq.read_table(OUR_PARQUET).to_pandas()
    df["PROTOCOL_NUM"] = df["PROTOCOL"].map(PROTO_TO_NUM).astype("Int64")
    df["MINUTE"] = pd.to_datetime(df["TIME"], unit="us").dt.floor("min")
    df["_flow_id"] = range(len(df))
    return df


def join_one_orientation(flows: pd.DataFrame, labels: pd.DataFrame, swapped: bool,
                          minute_col: str = "MINUTE") -> pd.DataFrame:
    key_flow = ["SRC IP", "SRC PORT", "DST IP", "DST PORT", "PROTOCOL_NUM", minute_col]
    key_label = ["SRC IP", "SRC PORT", "DST IP", "DST PORT", "PROTOCOL_NUM", "MINUTE"]
    if swapped:
        flows = flows.rename(columns={
            "SRC IP": "DST IP", "DST IP": "SRC IP",
            "SRC PORT": "DST PORT", "DST PORT": "SRC PORT",
        })
    return flows.merge(labels, left_on=key_flow, right_on=key_label, how="inner",
                        suffixes=("", "_lbl"))


def scan_hour_offsets(flows: pd.DataFrame, labels: pd.DataFrame, hours=range(-12, 13)) -> int:
    """CICFlowMeter's Timestamp is written in the capture machine's local time
    (CICIDS2017 was captured at UNB, Atlantic time), while our own TIME comes
    straight from pcap (true UTC) - so a constant hour offset is expected.
    Scan it instead of hardcoding a guess that may not match this specific
    dataset release."""
    print("scanning hour offsets to find clock alignment (straight orientation only)...")
    counts = {}
    for h in hours:
        shifted = flows["MINUTE"] + pd.Timedelta(hours=h)
        tmp = flows.assign(_SHIFTED_MINUTE=shifted)
        n = len(join_one_orientation(tmp, labels, swapped=False, minute_col="_SHIFTED_MINUTE"))
        counts[h] = n
    ranked = sorted(counts.items(), key=lambda t: -t[1])
    print("offset (hours) -> raw match count:", ranked)
    best_offset, best_count = ranked[0]
    if best_count < 1000:
        print(f"WARNING: even the best offset ({best_offset}h) only gives {best_count} matches - "
              "this is not just a clock offset, something else is wrong with the join keys.")
    return best_offset


def main(top_k: int):
    flows = load_flows()
    labels = load_labels()
    print(f"flows: {len(flows)}, labelled rows: {len(labels)}")
    print("our flow time range (UTC):", flows["MINUTE"].min(), "-", flows["MINUTE"].max())
    print("labelled Timestamp range:", labels["MINUTE"].min(), "-", labels["MINUTE"].max())

    best_offset = scan_hour_offsets(flows, labels)
    flows["MINUTE"] = flows["MINUTE"] + pd.Timedelta(hours=best_offset)
    print(f"applying {best_offset}h offset to our flow timestamps before the real join")

    straight = join_one_orientation(flows, labels, swapped=False)
    swapped = join_one_orientation(flows, labels, swapped=True)
    merged = pd.concat([straight, swapped], ignore_index=True)
    print(f"raw matches: straight={len(straight)}, swapped={len(swapped)}, union={len(merged)}")

    # Drop anything ambiguous: a flow or a label row matched more than once,
    # in either orientation, rather than guessing which match is right.
    merged = merged[~merged["_flow_id"].duplicated(keep=False)]
    merged = merged[~merged["_label_id"].duplicated(keep=False)]
    match_rate = len(merged) / len(flows)
    print(f"unique unambiguous matches: {len(merged)} ({match_rate:.1%} of our flows)")

    if len(merged) < 100:
        print("WARNING: match count is very low - join keys likely need revisiting "
              "before trusting anything downstream of this.")

    X = merged[NUMERIC_FEATURES].fillna(0)
    y = merged["LABEL_BIN"]
    print("class balance (0=benign, 1=attack):", y.value_counts(normalize=True).to_dict())

    mi = mutual_info_classif(X, y, random_state=0)
    ranked = sorted(zip(NUMERIC_FEATURES, mi), key=lambda t: -t[1])
    print("mutual information ranking:", ranked)
    top_features = [f for f, _ in ranked[:top_k]]
    print(f"selected top-{top_k} features (== qubit count for the pilot): {top_features}")

    out = merged[top_features + ["LABEL_BIN", "Label"]].rename(columns={"LABEL_BIN": "label"})
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PATH, index=False)
    print(f"wrote {len(out)} rows -> {OUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top_k", type=int, default=4,
                         help="Number of MI-ranked features to keep (== qubit count in the pilot)")
    args = parser.parse_args()
    main(args.top_k)
