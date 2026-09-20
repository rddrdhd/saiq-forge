#!/bin/bash
#SBATCH --job-name=saiq-forge-phase1-cpu
#SBATCH --account=project_XXXXXXX      # TODO update
#SBATCH --partition=small
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --output=logs/%x-%j.out
set -euo pipefail

# Statistical tier only (Phase 1) — CPU-bound, no GPU benefit. `small` is
# billed per-core, not per-node, which matters since this doesn't need a
# whole node's worth of cores.
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
