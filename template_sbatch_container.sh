#!/usr/bin/bash
#SBATCH --job-name test
#SBATCH --account project_XXXXXXXXX
#SBATCH --partition debug
#SBATCH --exclusive
#SBATCH --time 00:00:10
#SBATCH --output=/path/to/your/outputs/my_log.log

singularity exec \
    --bind /path/to/your/saiq-forge \
    saiq-forge.sif python tests/test_imports.py -v 