#!/bin/bash
# Creates a small venv on top of LUMI's cray-python module. Deliberately a
# plain venv, not a container: current dependencies are just pyyaml+pytest,
# small enough that LUMI's own "keep it small" guidance for bare venvs
# applies. Revisit toward a cotainr-built container once heavier
# dependencies (numpy/pandas/scikit-learn, later PyTorch+ROCm) land.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${1:-$REPO_ROOT/.venv}"

if command -v module >/dev/null 2>&1; then
    module load cray-python
fi

python3 -m venv --system-site-packages "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$REPO_ROOT/requirements.txt"

echo "Environment ready at $VENV_DIR"
echo "Activate it with: source $VENV_DIR/bin/activate"
