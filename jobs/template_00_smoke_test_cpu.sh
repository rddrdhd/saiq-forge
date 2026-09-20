#!/bin/bash
#SBATCH --job-name=saiq-forge-smoke
#SBATCH --account=project_XXXXXXX      # TODO update
#SBATCH --partition=small
#SBATCH --time=00:10:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --output=logs/%x-%j.out
set -euo pipefail

REPO_ROOT="${SLURM_SUBMIT_DIR:-$PWD}"  # sbatch runs a spooled copy of this script, so
                                        # ${BASH_SOURCE[0]} would point at /var/spool/...
module load cray-python
source "$REPO_ROOT/.venv/bin/activate"

CONFIG=${1:-config/config.yaml}
eval "$(python3 -c "
import yaml
with open('$CONFIG') as f:
    cfg = yaml.safe_load(f)
print('export WORKDIR=' + cfg['project']['workdir'])
print('export DATADIR=' + cfg['project']['datadir'])
print('export LOGSDIR=' + cfg['project']['logsdir'])
")"

cd "$WORKDIR"
python3 -m pytest tests/test_00_imports.py tests/test_02_windowing.py
