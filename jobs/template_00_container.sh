#!/usr/bin/bash
#SBATCH --job-name=test
#SBATCH --account=project_XXXXXXXXX     # TODO update
#SBATCH --partition=debug
#SBATCH --exclusive
#SBATCH --time=00:00:10
#SBATCH --output=/path/to/your/saiq-forge/outputs/my_log.log   # TODO update

WORKDIR=/path/to/your/saiq-forge    # TODO update
SIF=$WORKDIR/saiq-forge.sif

singularity exec \
    --bind $WORKDIR \
    $SIF python tests/test_00_imports.py -v 