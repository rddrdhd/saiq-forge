#!/bin/bash -l
#SBATCH --job-name=saiq_main
#SBATCH --account=project_XXXXX                     
#SBATCH --partition=standard-g
#SBATCH --exclusive
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=8                             # Ready for GPU computing
#SBATCH --gpus-per-node 8
#SBATCH --cpus-per-task 7 
#SBATCH --mem=32G
#SBATCH --time=00:15:00                                  # debug partition max is 30 min
#SBATCH --output=/path/to/your/saiq-forge/outputs/logs/main_%j.out # TODO update
#SBATCH --error=/path/to/your/saiq-forge/outputs/logs/main_%j.err # TODO update

# ── Paths ─────────────────────────────────────────────────────────────────────
WORKDIR=/scratch/project_XXXXXXXX/saiq-forge            # TODO update
SIF=$WORKDIR/saiq-forge.sif

export POLARS_MAX_THREADS=$SLURM_CPUS_PER_TASK
export PYTHONFAULTHANDLER=1

# ── Info header ───────────────────────────────────────────────────────────────
echo "============================================================"
echo "  saiq-forge — main"
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
export DATADIR="/path/to/your/data" # TODO update

singularity exec \
    --bind "$WORKDIR",\
    --bind "$DATADIR":/data \
    $SIF \
    python core/main.py -v -s

EXIT_CODE=$?

exit $EXIT_CODE