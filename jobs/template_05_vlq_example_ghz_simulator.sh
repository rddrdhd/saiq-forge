#!/bin/bash -l
#SBATCH --job-name=saiq_vlq_sim
#SBATCH --account=project_XXXXX             # TODO update
#SBATCH --partition=standard-g
#SBATCH --nodes=1
#SBATCH --gpus-per-node=8
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=56
#SBATCH --time=00:15:00
#SBATCH --output=~/vlq_sim_%j.out           # TODO update
#SBATCH --error=~/vlq_sim_%j.err            # TODO update

# GHZ example on LUMI's own GPUs via the official CSC Qiskit-Aer-GPU container.
# No VLQ hardware and no LEXIS token needed — this is the "minimal example on a
# quantum simulator" step. Source: https://docs.csc.fi/apps/qiskit/
#
# Deliberately does NOT follow the run_*.sh + srun-wrapping pattern used by the
# other job templates (01-04): the container's srun invocation below needs a
# specific --cpu-bind mask matching the requested GPU/CPU layout, which would
# break if nested inside another srun step. Keep it a single top-level srun.
#
# The 8-GPU/56-core layout below is the CSC-verified one for a full LUMI-G
# node. This toy 5-qubit circuit does not need it — for a quick single-GPU
# test, drop to --gpus-per-node=1 and remove --cpu-bind (or work out the
# correct 1-GPU mask yourself; the hex mask below is only verified for 8 GPUs).

# ── Load data from config  ─────────────────────────────────────────────────────────────────────
CONFIG_PATH="config/default.yml"
eval $(python3 -c "
import yaml
with open('$CONFIG_PATH') as f:
    cfg = yaml.safe_load(f)
print(f'WORKDIR=\"{cfg.get(\"workdir\", \"\")}\"')
print(f'LOGSDIR=\"{cfg.get(\"logsdir\", \"\")}\"')
")

TODAYS_DATE=$(date +%Y%m%d)
LOG_DIR="${LOGSDIR}/${TODAYS_DATE}_$SLURM_JOB_ID"
mkdir -p "$LOG_DIR"
cd $WORKDIR

# ── Official CSC Qiskit container (LUMI's own AMD MI250X GPUs, ROCm build) ───
export LUMI_QISKIT_SINGULARITY_CONTAINER_PATH=/appl/local/quantum/qiskit/qiskit_2.3.0_csc.sif
export WRAPPER_PATH=/appl/local/quantum/qiskit/run-singularity-with-gpu-affinity

srun --cpu-bind=mask_cpu:0xfe000000000000,0xfe00000000000000,0xfe0000,0xfe000000,0xfe,0xfe00,0xfe00000000,0xfe0000000000 \
    $WRAPPER_PATH $LUMI_QISKIT_SINGULARITY_CONTAINER_PATH \
    python3 main_vlq_example_ghz_simulator.py --path_logdir="$LOG_DIR"

# ── Move output ─────────────────────────────────────────────────────────────────────
mv ~/vlq_sim_$SLURM_JOB_ID.out $LOG_DIR/  # TODO update
mv ~/vlq_sim_$SLURM_JOB_ID.err $LOG_DIR/  # TODO update
