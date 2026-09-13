#!/bin/bash -l
#SBATCH --job-name=saiq_vlq_ghz
#SBATCH --account=project_XXXXX             # TODO update                    
#SBATCH --partition=dev-g
#SBATCH --exclusive
#SBATCH --nodes=1

#SBATCH --mem=32G
#SBATCH --time=00:05:00                     
#SBATCH --output=~/vlq_ghz_%j.out           # TODO update
#SBATCH --error=~/vlq_ghz_%j.err            # TODO update

# partition names for LUMI: https://docs.lumi-supercomputer.eu/runjobs/scheduled-jobs/partitions/

# ── Load data from config  ─────────────────────────────────────────────────────────────────────
CONFIG_PATH="config/default.yml"
eval $(python3 -c "
import yaml
with open('$CONFIG_PATH') as f:
    cfg = yaml.safe_load(f)
print(f'WORKDIR=\"{cfg.get(\"workdir\", \"\")}\"')
print(f'DATADIR=\"{cfg.get(\"datadir\", \"\")}\"')
print(f'LOGSDIR=\"{cfg.get(\"logsdir\", \"\")}\"')
")
# ── Set other things ─────────────────────────────────────────────────────────────────────
           
#SIF=$WORKDIR/saiq-forge.sif

TODAYS_DATE=$(date +%Y%m%d)
LOG_DIR="${LOGSDIR}/${TODAYS_DATE}_$SLURM_JOB_ID"
mkdir -p "$LOG_DIR"
cd $WORKDIR

# ── Load modules ─────────────────────────────────────────────────────────

module use /appl/local/csc/modulefiles/
module load pytorch/2.4

# ── Environment hints ─────────────────────────────────────────────────────────
export POLARS_MAX_THREADS=$SLURM_CPUS_PER_TASK
export PYTHONFAULTHANDLER=1


# ── Run ─────────────────────────────────────────────────────────────────────
srun sh scripts/run_main_vlq_example_ghz.sh --path_output="$LOG_DIR" --path_workdir="$WORKDIR" --path_data="$DATADIR"

# ── Move output ─────────────────────────────────────────────────────────────────────
mv ~/vlq_ghz_$SLURM_JOB_ID.out $LOG_DIR/  # TODO update
mv ~/vlq_ghz_$SLURM_JOB_ID.err $LOG_DIR/  # TODO update
