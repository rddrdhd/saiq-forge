#!/bin/bash
module use /appl/local/csc/modulefiles/
module load pytorch/2.4

VENV_DIR="my_vlq_venv"

python3 -m venv "$VENV_DIR"

source "$VENV_DIR/bin/activate"

pip3 install --upgrade pip setuptools wheel

pip3 install --index-url https://opencode.it4i.eu/api/v4/projects/107/packages/pypi/simple py4lexis
pip3 install git+https://github.com/It4innovations/quantum-as-a-service.git@v0.2.0
pip3 install matplotlib
