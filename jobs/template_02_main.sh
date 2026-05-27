#!/bin/bash -l
#SBATCH --job-name=saiq_main
#SBATCH --account=project_XXXXX                     
#SBATCH --partition=dev-g
#SBATCH --exclusive
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=8                             # Ready for GPU computing
#SBATCH --gpus-per-node=8
#SBATCH --cpus-per-task=7 
#SBATCH --mem=32G
#SBATCH --time=00:15:00                                  # debug partition max is 30 min
#SBATCH --output=~/main_%j.out # TODO update
#SBATCH --error=~/main_%j.err # TODO update

# ── Load data from config  ─────────────────────────────────────────────────────────────────────
CONFIG_PATH="config/my_default.yml"
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

# ── Run ─────────────────────────────────────────────────────────────────────
srun sh scripts/run_main.sh --path_output="$LOG_DIR" --path_workdir="$WORKDIR" --path_data="$DATADIR"

# ── Move output ─────────────────────────────────────────────────────────────────────
mv ~/main_$SLURM_JOB_ID.out $LOG_DIR/ # TODO update
mv ~/main_$SLURM_JOB_ID.err $LOG_DIR/ # TODO update
# this is moving the logs from tmp dir to your log dir. Set the tmp dir to anywhere, just the same one as in the #SBATCH attrs.