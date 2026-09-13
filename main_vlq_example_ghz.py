import argparse
from pathlib import Path
import os
import sys; sys.path.append("..")
from core.config import load_config
# Force matplotlib to use a non-interactive backend for headless execution
import matplotlib
matplotlib.use('Agg')

from qaas.client import QProvider
from qiskit import QuantumCircuit
from iqm.qiskit_iqm import transpile_to_IQM
from qiskit.visualization import plot_histogram

parser = argparse.ArgumentParser(description="VLQ Example Script")
parser.add_argument("--path_logdir", type=str, default=".", help="Path to output directory for logs and plots")
args = parser.parse_args()
output_dir = Path(args.path_logdir)
output_dir.mkdir(parents=True, exist_ok=True)

cfg = load_config("config/default.yml")
    
PROJECT = cfg["q"]["project_id"] 
RESOURCE = cfg["q"]["resource_id"] 

print(f'Trying to reach VLQ with project {PROJECT} and resource {RESOURCE}')
# ==========================================
# 1. AUTHENTICATION & TOKEN LOADING
# ==========================================
token_path = os.path.expanduser("~/.lexis_token")

if not os.path.exists(token_path):
    print(f"Error: Token file not found at {token_path}. Please run '.scripts/run_get_lexis_token.sh' first.", file=sys.stderr)
    sys.exit(1)

with open(token_path, "r") as f:
    token = f.read().strip()

try:
    provider = QProvider(token, PROJECT)
    backend = provider.get_backend(RESOURCE)
    print("Successfully authenticated with VLQ via saved token!")
except Exception as e:
    print(f"Authentication failed. Your token might have expired (5-day limit). Run '.scripts/run_get_lexis_token.sh' again. Error: {e}", file=sys.stderr)
    sys.exit(1)


# ==========================================
# 2. CIRCUIT CREATION
# ==========================================
print("\nCreating quantum circuit...")
num_qb = 5
qc = QuantumCircuit(num_qb)
qc.h(0)
for qb in range(1, num_qb):
    qc.cx(0, qb)

qc.barrier()
qc.measure_all()

# Save the original circuit drawing as an image
fig_qc = qc.draw(output='mpl')
fig_qc.savefig(f'{output_dir}/circuit_original.png', bbox_inches='tight')
print("-> Saved original circuit layout to 'circuit_original.png'")


# ==========================================
# 3. TRANSPILATION
# ==========================================
print("\nTranspiling circuit for the VLQ backend...")
qc_transpiled = transpile_to_IQM(qc, backend)

# Save the transpiled circuit drawing as an image
fig_transpiled = qc_transpiled.draw(output="mpl")
fig_transpiled.savefig(f'{output_dir}/circuit_transpiled.png', bbox_inches='tight')
print("-> Saved transpiled circuit layout to 'circuit_transpiled.png'")


# ==========================================
# 4. EXECUTION ON VLQ
# ==========================================
SHOTS = 5000
print(f"\nSubmitting job to VLQ machine ({SHOTS} shots)...")
job = backend.run(qc_transpiled, shots=SHOTS)

print("Waiting for backend execution results...")
results = job.result().get_counts()

# Print raw dictionary to the Slurm log file
print("\nRaw counts from execution:")
print(results)


# ==========================================
# 5. POST-PROCESSING & PLOTTING
# ==========================================
# Filter out low-frequency noise
result_clean = {key: count for key, count in results.items() if count > 15}

# Generate and save the histogram plot
print("\nGenerating final histogram...")
fig_hist = plot_histogram(result_clean)
fig_hist.savefig(f'{output_dir}/results_histogram.png', bbox_inches='tight')
print("-> Saved execution histogram to 'results_histogram.png'")

print("\n[SUCCESS] VLQ computation finished completely!")

# Manually delete the backend/provider objects to trigger their cleanup 
# while the Python interpreter modules are still fully alive.
try:
    del backend
    del provider
except NameError:
    pass