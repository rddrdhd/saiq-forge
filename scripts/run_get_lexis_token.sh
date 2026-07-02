#!/bin/bash

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
# ── Running VLQ part  ─────────────────────────────────────────────────────────────────────
cd $WORKDIR

VENV_DIR="my_vlq_venv"

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "[RUN_GET_LEXIS_TOKEN]: VLQ venv not found. Running build script."
    chmod +x $WORKDIR/scripts/build_vlq_venv.sh
    "$WORKDIR/scripts/build_vlq_venv.sh" || { echo "Build venv failed!"; exit 1; }
else
    echo "[RUN_GET_LEXIS_TOKEN]: VLQ venv found, skipping build script."
fi

source "$VENV_DIR/bin/activate"
python scripts/get_lexis_token.py