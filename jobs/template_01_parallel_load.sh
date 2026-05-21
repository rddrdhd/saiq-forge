#!/bin/bash -l
#SBATCH --job-name=saiq_parallel_load
#SBATCH --account=project_XXXXXXXX                      # TODO update
#SBATCH --partition=debug
#SBATCH --exclusive
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=00:15:00                                  
#SBATCH --output=/path/to/your/saiq-forge/outputs/logs/parallel_load_%j.out # TODO update
#SBATCH --error=/path/to/your/saiq-forge/outputs/logs/parallel_load_%j.err # TODO update

# ── Paths ─────────────────────────────────────────────────────────────────────
WORKDIR=/scratch/project_XXXXXXXX/saiq-forge            # TODO update
SIF=$WORKDIR/saiq-forge.sif

# ── Environment hints ─────────────────────────────────────────────────────────
# Tell Polars to use all allocated CPUs for its thread pool.
# Without this it may try to use all cores on the node (128) and over-subscribe.
export POLARS_MAX_THREADS=$SLURM_CPUS_PER_TASK

# Needed for ProcessPoolExecutor fork safety on Linux
export PYTHONFAULTHANDLER=1

# ── Info header ───────────────────────────────────────────────────────────────
echo "============================================================"
echo "  saiq-forge — parallel parquet loading demo"
echo "============================================================"
echo "Job ID    : $SLURM_JOB_ID"
echo "Node      : $(hostname)"
echo "CPUs      : $SLURM_CPUS_PER_TASK"
echo "Date      : $(date)"
echo "Workdir   : $WORKDIR"
echo "Container : $SIF"
echo "============================================================"
echo ""

cd $WORKDIR

# ── Run: pytest with -s so worker prints are NOT captured ─────────────────────
echo "--- Running pytest (output capture disabled with -s) ---"
singularity exec \
    --bind $WORKDIR \
    $SIF \
    python -m pytest tests/test_parallel_load.py -v -s

EXIT_CODE=$?

echo ""
echo "============================================================"
echo "  Tests finished with exit code $EXIT_CODE at $(date)"
echo "============================================================"
exit $EXIT_CODE