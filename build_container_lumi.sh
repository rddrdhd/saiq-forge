#!/bin/bash

module purge
module load CrayEnv
module load cotainr

cotainr --version

# Build the container (~5 min on LUMI)
# --system=lumi-c targets LUMI's CPU partition (x86, no ROCm needed)
# --accept-licenses avoids the interactive Miniforge license prompt
cotainr build saiq-forge.sif \
  --system=lumi-c \
  --conda-env=environment.yml \
  --accept-licenses

# Confirm it was created
ls -lh saiq-forge.sif    # ~1 GB

# ----------------------------------------------------
# cheatsheet after loading modules:
# ----------------------------------------------------
# singularity exec saiq-forge.sif python -c "print('Hello world')"

# singularity exec python -c "
#   import polars as pl
#   import dask
#   import rich
#   import pytest
#   print('polars:', pl.__version__)
#   print('dask:  ', dask.__version__)
#   print('All imports OK')
#   "