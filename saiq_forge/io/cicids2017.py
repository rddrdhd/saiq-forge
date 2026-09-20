import math
import random
from pathlib import Path
from typing import List, Tuple

import pandas as pd

BENIGN = 0


def _log1p_minmax_fit(df: pd.DataFrame, feature_cols: List[str], lo: float, hi: float):
    """Fits log1p+min-max bounds on df (the benign training split only —
    fitting on the full mixed set would leak eval-set distribution shape
    into training), returns a transform callable for any row."""
    logged = {c: [math.log1p(max(0.0, v)) for v in df[c]] for c in feature_cols}
    bounds = {c: (min(logged[c]), max(logged[c])) for c in feature_cols}

    def transform(row) -> dict:
        out = {}
        for c in feature_cols:
            v = math.log1p(max(0.0, row[c]))
            c_min, c_max = bounds[c]
            span = c_max - c_min
            scaled = (v - c_min) / span if span > 0 else 0.0
            out[c] = lo + scaled * (hi - lo)
        return out

    return transform


def load_pilot_dataset(
    path,
    scale_range: Tuple[float, float] = (0.0, 1.0),
) -> Tuple[List[dict], List[dict], List[int]]:
    """Loads the pre-built, pre-labeled CICIDS2017 pilot parquet (produced by
    scripts/build_qml_pilot_dataset.py on the danger branch — the top-K
    mutual-information-ranked numeric flow features plus a binary label,
    already joined against CICIDS2017's official ground truth). That
    dataset-prep work is already done and already lives on this allocation,
    so this loader does not repeat it.

    Returns (benign_train_records, eval_records, eval_labels):
    benign-only rows for unsupervised training (design decision: autoencoders
    here train exclusively on normal traffic, per the Deep Learning detector
    class convention), the full benign+attack set for evaluation.
    """
    df = pd.read_parquet(Path(path))
    feature_cols = [c for c in df.columns if c not in ("label", "Label")]

    benign_df = df[df["label"] == BENIGN]
    if benign_df.empty:
        raise ValueError(f"no benign (label=={BENIGN}) rows found in {path}")

    transform = _log1p_minmax_fit(benign_df, feature_cols, *scale_range)

    benign_records = [transform(row) for _, row in benign_df.iterrows()]
    eval_records = [transform(row) for _, row in df.iterrows()]
    eval_labels = df["label"].astype(int).tolist()

    return benign_records, eval_records, eval_labels


def sample_capped_subset(
    eval_records: List[dict],
    eval_labels: List[int],
    n: int,
    seed: int = 0,
) -> Tuple[List[dict], List[int]]:
    """A small, class-balanced-as-possible subset shared by all detectors
    when comparing against the VLQ hardware path's necessarily-capped
    evaluation set (real hardware, limited shot/queue budget) — so a metric
    difference isn't confounded by evaluating on different data."""
    rng = random.Random(seed)
    by_label = {}
    for record, label in zip(eval_records, eval_labels):
        by_label.setdefault(label, []).append(record)

    per_class = max(1, n // len(by_label))
    records, labels = [], []
    for label, class_records in by_label.items():
        chosen = rng.sample(class_records, min(per_class, len(class_records)))
        records.extend(chosen)
        labels.extend([label] * len(chosen))

    paired = list(zip(records, labels))
    rng.shuffle(paired)
    if not paired:
        return [], []
    records, labels = zip(*paired)
    return list(records), list(labels)
