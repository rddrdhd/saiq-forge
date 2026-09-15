"""
main_qml_pilot_classifier.py
──────────────────────────────
RQ5 minimal pilot: a small Variational Quantum Circuit (VQC) classifier vs. a
parameter-matched classical MLP, on the CICIDS2017 Friday attack/benign
dataset recovered by scripts/build_qml_pilot_dataset.py. Runs on LUMI's own
GPUs via the official CSC Qiskit-Aer-GPU container - no VLQ hardware yet,
see CLAUDE.md "Immediate direction" (simulator first).

Deliberately minimal, not the full Phase~4 protocol in teze_tex/Body.tex:
- 4 features/qubits (whatever build_qml_pilot_dataset.py selected by mutual
  information), not the full 16.
- A single fixed circuit depth, not a depth sweep for barren-plateau analysis.
- MLP hidden size chosen to roughly match the VQC's parameter count, not
  matched by effective dimension / expressibility (Abbas 2021, Sim 2019).
- One noiseless + one illustrative-noise condition, not an IBMQ-calibrated
  noise model.
This is the "does the pipeline work end-to-end and is either model even
usable" pass; the full matched-baseline protocol is future work.

The VQC is built and trained by hand (angle encoding + entangling ansatz +
COBYLA, evaluated via AerSimulator.run()) rather than via qiskit_machine_learning's
VQC/EstimatorQNN wrappers, to avoid depending on primitive-interface versions
we have not verified against this container's qiskit_aer 0.17.2 / qiskit 2.3.1.
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import MinMaxScaler

from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

PILOT_DATA = Path(__file__).resolve().parent / "data/generated-outputs/qml_pilot_cicids2017.parquet"

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--path_logdir", type=str, default=".")
parser.add_argument("--n_per_class", type=int, default=150,
                     help="Balanced subsample size per class - this is a pilot, not the full n=5000 Phase 4 protocol")
parser.add_argument("--reps", type=int, default=2, help="Entangling ansatz layers")
parser.add_argument("--shots", type=int, default=512)
parser.add_argument("--maxiter", type=int, default=80, help="COBYLA iterations")
parser.add_argument("--seed", type=int, default=0)
args = parser.parse_args()
output_dir = Path(args.path_logdir)
output_dir.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(args.seed)

# ==========================================
# 1. DATA
# ==========================================
print(f"Loading pilot dataset from {PILOT_DATA}...")
df = pd.read_parquet(PILOT_DATA)
feature_cols = [c for c in df.columns if c not in ("label", "Label")]
n_qubits = len(feature_cols)
print(f"Features (== qubits): {feature_cols}")

balanced = (
    df.groupby("label", group_keys=False)
    .apply(lambda g: g.sample(n=min(args.n_per_class, len(g)), random_state=args.seed))
)
print(f"Balanced subsample: {len(balanced)} rows, class counts: {balanced['label'].value_counts().to_dict()}")

X_raw = balanced[feature_cols].to_numpy(dtype=float)
y = balanced["label"].to_numpy(dtype=int)
X_train_raw, X_test_raw, y_train, y_test = train_test_split(
    X_raw, y, test_size=0.3, random_state=args.seed, stratify=y
)

# log1p first - byte/packet/duration counts are heavily right-skewed
scaler = MinMaxScaler(feature_range=(0, np.pi))
X_train = scaler.fit_transform(np.log1p(X_train_raw))
X_test = scaler.transform(np.log1p(X_test_raw))
print(f"Train/test: {len(X_train)}/{len(X_test)}")

# ==========================================
# 2. VQC DEFINITION (angle encoding + entangling ansatz)
# ==========================================
n_params = n_qubits * (args.reps + 1)
print(f"\nBuilding {n_qubits}-qubit VQC, {args.reps} entangling layers, {n_params} trainable parameters...")

feature_params = ParameterVector("x", n_qubits)
weight_params = ParameterVector("theta", n_params)


def build_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(n_qubits)
    for q in range(n_qubits):
        qc.ry(feature_params[q], q)  # angle encoding of the classical features
    idx = 0
    for layer in range(args.reps + 1):
        for q in range(n_qubits):
            qc.ry(weight_params[idx], q)
            idx += 1
        if layer < args.reps:
            for q in range(n_qubits - 1):
                qc.cx(q, q + 1)
    qc.measure_all()
    return qc


circuit_template = build_circuit()


def run_batch(X: np.ndarray, weights: np.ndarray, simulator: AerSimulator) -> np.ndarray:
    """Returns P(class=1) per sample, estimated as (1 - <Z_0>) / 2 from shot counts."""
    bound_circuits = [
        circuit_template.assign_parameters(
            {**{feature_params[q]: X[i, q] for q in range(n_qubits)},
             **{weight_params[j]: weights[j] for j in range(n_params)}}
        )
        for i in range(len(X))
    ]
    results = simulator.run(bound_circuits, shots=args.shots).result()
    probs = np.empty(len(X))
    for i in range(len(X)):
        counts = results.get_counts(i)
        total = sum(counts.values())
        # qubit 0 is the rightmost bit in Qiskit's little-endian bitstring
        ones = sum(c for bits, c in counts.items() if bits[-1] == "1")
        probs[i] = ones / total
    return probs


def train_vqc(simulator: AerSimulator, label: str, x0: np.ndarray) -> np.ndarray:
    print(f"\nTraining VQC ({label}) via COBYLA, {args.maxiter} iterations...")

    def loss(weights):
        p = np.clip(run_batch(X_train, weights, simulator), 1e-6, 1 - 1e-6)
        return -np.mean(y_train * np.log(p) + (1 - y_train) * np.log(1 - p))

    res = minimize(loss, x0, method="COBYLA", options={"maxiter": args.maxiter})
    print(f"  final training loss: {res.fun:.4f}")
    return res.x


def evaluate(probs: np.ndarray, y_true: np.ndarray, label: str) -> dict:
    preds = (probs >= 0.5).astype(int)
    metrics = {
        "accuracy": accuracy_score(y_true, preds),
        "f1": f1_score(y_true, preds),
        "roc_auc": roc_auc_score(y_true, probs),
    }
    print(f"  [{label}] accuracy={metrics['accuracy']:.3f} f1={metrics['f1']:.3f} roc_auc={metrics['roc_auc']:.3f}")
    return metrics


# ==========================================
# 3. NOISELESS + ILLUSTRATIVE-NOISE CONDITIONS
# ==========================================
results_table = {}

# Same starting weights for both conditions - otherwise a noiseless-vs-noisy
# performance difference is confounded with differing random initialization
# rather than isolating the effect of noise.
shared_x0 = rng.uniform(0, 2 * np.pi, n_params)

sim_noiseless = AerSimulator(method="statevector", device="GPU")
weights = train_vqc(sim_noiseless, "noiseless", shared_x0)
results_table["VQC (noiseless sim)"] = evaluate(run_batch(X_test, weights, sim_noiseless), y_test, "VQC noiseless")

# Illustrative depolarizing noise, NOT calibrated to real hardware - that
# calibration (IBMQ Nairobi error rates) is part of the full Phase 4 protocol.
noise_model = NoiseModel()
noise_model.add_all_qubit_quantum_error(depolarizing_error(0.001, 1), ["ry"])
noise_model.add_all_qubit_quantum_error(depolarizing_error(0.01, 2), ["cx"])
sim_noisy = AerSimulator(method="statevector", device="GPU", noise_model=noise_model)
weights_noisy = train_vqc(sim_noisy, "noisy", shared_x0)
results_table["VQC (illustrative noise)"] = evaluate(run_batch(X_test, weights_noisy, sim_noisy), y_test, "VQC noisy")

# ==========================================
# 4. MATCHED CLASSICAL BASELINE
# ==========================================
# Rough parameter match only (see module docstring) - not effective-dimension
# or expressibility matched.
hidden = (max(2, n_params // (n_qubits + 2)),)
mlp = MLPClassifier(hidden_layer_sizes=hidden, max_iter=2000, random_state=args.seed)
print(f"\nTraining matched classical MLP, hidden_layer_sizes={hidden} "
      f"(target ~{n_params} VQC params)...")
mlp.fit(X_train, y_train)
mlp_n_params = sum(w.size for w in mlp.coefs_) + sum(b.size for b in mlp.intercepts_)
print(f"  actual MLP parameter count: {mlp_n_params} (VQC: {n_params})")
mlp_probs = mlp.predict_proba(X_test)[:, 1]
results_table["Classical MLP (matched)"] = evaluate(mlp_probs, y_test, "MLP")

# ==========================================
# 5. SUMMARY
# ==========================================
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
summary_df = pd.DataFrame(results_table).T
print(summary_df.to_string())
summary_df.to_csv(output_dir / "qml_pilot_results.csv")

fig, ax = plt.subplots(figsize=(7, 4))
summary_df[["accuracy", "f1", "roc_auc"]].plot.bar(ax=ax)
ax.set_ylim(0, 1.05)
ax.set_title(f"VQC vs matched MLP - {n_qubits}-feature CICIDS2017 pilot (n={len(balanced)})")
fig.tight_layout()
fig.savefig(output_dir / "qml_pilot_comparison.png")
print(f"\n-> Saved {output_dir}/qml_pilot_results.csv and qml_pilot_comparison.png")
print("\n[SUCCESS] QML pilot finished completely!")
