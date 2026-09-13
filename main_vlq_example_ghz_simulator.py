"""
main_vlq_example_ghz_simulator.py
──────────────────────────────────
Same 5-qubit GHZ circuit as main_vlq_example_ghz.py, but run on Qiskit's
Aer statevector simulator with GPU acceleration on LUMI's own AMD MI250X
GPUs — no VLQ hardware, no LEXIS token, no py4lexis/QaaS needed.

This is meant as the "minimal example on a quantum simulator" step before
attempting a quantum/hybrid autoencoder: same circuit-building code, same
plotting, but the whole thing runs self-contained on a LUMI GPU node.

Must be run inside the official CSC Qiskit container (qiskit-aer-gpu on
LUMI is a custom ROCm/HIP build; the plain `pip install qiskit-aer-gpu`
wheel is CUDA-only and will not work here). See
jobs/template_05_vlq_example_ghz_simulator.sh for the exact invocation
(https://docs.csc.fi/apps/qiskit/).
"""

import argparse
from pathlib import Path

# Force matplotlib to use a non-interactive backend for headless execution
import matplotlib
matplotlib.use('Agg')

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram

parser = argparse.ArgumentParser(description="GHZ example on LUMI's Qiskit Aer GPU simulator")
parser.add_argument("--path_logdir", type=str, default=".", help="Path to output directory for logs and plots")
parser.add_argument("--num_qubits", type=int, default=5, help="Number of qubits in the GHZ state")
parser.add_argument("--shots", type=int, default=5000, help="Number of measurement shots")
args = parser.parse_args()
output_dir = Path(args.path_logdir)
output_dir.mkdir(parents=True, exist_ok=True)

# ==========================================
# 1. CIRCUIT CREATION
# ==========================================
print(f"\nCreating {args.num_qubits}-qubit GHZ circuit...")
qc = QuantumCircuit(args.num_qubits)
qc.h(0)
for qb in range(1, args.num_qubits):
    qc.cx(0, qb)

qc.barrier()
qc.measure_all()

# Save the circuit drawing as an image
fig_qc = qc.draw(output='mpl')
fig_qc.savefig(f'{output_dir}/circuit_original.png', bbox_inches='tight')
print("-> Saved circuit layout to 'circuit_original.png'")

# ==========================================
# 2. GPU-ACCELERATED SIMULATION
# ==========================================
print("\nInitializing AerSimulator on GPU (LUMI MI250X, statevector method)...")
simulator = AerSimulator(method="statevector", device="GPU")

print(f"Running {args.shots} shots...")
result = simulator.run(qc, shots=args.shots).result()
counts = result.get_counts()

# Print raw dictionary to the Slurm log file
print("\nRaw counts from execution:")
print(counts)

# ==========================================
# 3. POST-PROCESSING & PLOTTING
# ==========================================
# Filter out low-frequency noise, same threshold as the VLQ hardware example
result_clean = {key: count for key, count in counts.items() if count > 15}

print("\nGenerating final histogram...")
fig_hist = plot_histogram(result_clean)
fig_hist.savefig(f'{output_dir}/results_histogram.png', bbox_inches='tight')
print("-> Saved execution histogram to 'results_histogram.png'")

print("\n[SUCCESS] GPU simulator GHZ run finished completely!")
