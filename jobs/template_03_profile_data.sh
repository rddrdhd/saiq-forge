#!/bin/bash -l
#SBATCH --job-name=saiq_profile
#SBATCH --account=project_XXXXX                   
#SBATCH --partition=debug                                 # CPU
#SBATCH --exclusive
#SBATCH --nodes=1
#SBATCH --time=00:15:00                                  
#SBATCH --output=~/profile_%j.out # TODO update
#SBATCH --error=~/profile_%j.err # TODO update

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

TODAYS_DATE=$(date +%Y%m%d)
LOG_DIR="${LOGSDIR}/${TODAYS_DATE}_$SLURM_JOB_ID"
mkdir -p "$LOG_DIR"
cd $WORKDIR

# ── Load modules ─────────────────────────────────────────────────────────
module use /appl/local/csc/modulefiles/
module load pytorch/2.4

# ── Run ─────────────────────────────────────────────────────────────────────
srun sh scripts/run_profile_data.sh --path_output="$LOG_DIR" --path_workdir="$WORKDIR" --path_data="$DATADIR"

# ── Move output ─────────────────────────────────────────────────────────────────────
mv ~/profile_$SLURM_JOB_ID.out $LOG_DIR/ # TODO update
mv ~/profile_$SLURM_JOB_ID.err $LOG_DIR/ # TODO update
# this is moving the logs from tmp dir to your log dir. Set the tmp dir to anywhere, just the same one as in the #SBATCH attrs.