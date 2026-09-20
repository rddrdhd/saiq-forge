#!/bin/bash
#SBATCH --job-name=saiq-forge-phase1-gpu
#SBATCH --account=project_XXXXXXX      # TODO update
#SBATCH --partition=dev-g
#SBATCH --time=00:30:00
#SBATCH --gpus-per-node=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --output=logs/%x-%j.out
set -euo pipefail

# Same statistical-tier pipeline as template_01_phase1_baseline_cpu.sh. The
# Z-score/IQR detector has no compute-bound reason to need a GPU; this
# template exists only so the job can run on a GPU-partition allocation
# when that's what's actually available, not because the workload benefits.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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
python3 -m saiq_forge.cli run --config "$CONFIG"
