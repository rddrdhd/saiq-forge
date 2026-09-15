#!/usr/bin/bash
#SBATCH --job-name=saiq_qml_pilot_data
#SBATCH --account=project_XXXXX             # TODO update
#SBATCH --partition=debug   # CPU only - this is pandas/pyarrow data wrangling, no GPU/quantum
#SBATCH --exclusive
#SBATCH --time=00:15:00
#SBATCH --output=/path/to/your/saiq-forge/outputs/running/qml_pilot_data_%j.log  # TODO update

# Recovers ground-truth labels for CICIDS2017 Friday traffic by joining the
# official labelled flow CSVs onto our own pcap->parquet flow features, then
# selects the top-K (mutual-information-ranked) numeric features for the RQ5
# minimal quantum-vs-classical pilot. See scripts/build_qml_pilot_dataset.py
# for the join logic and its caveats (minute-resolution timestamps, ambiguous
# matches dropped rather than guessed).

WORKDIR=/path/to/your/saiq-forge        # TODO update
SIF=$WORKDIR/saiq-forge.sif

singularity exec \
    --bind "/pfs,/scratch,/project" --pwd $WORKDIR \
    $SIF python3 scripts/build_qml_pilot_dataset.py --top_k=4
