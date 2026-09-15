#!/bin/bash -l
#SBATCH --job-name=saiq_qml_pilot
#SBATCH --account=project_XXXXX             # TODO update
#SBATCH --partition=standard-g
#SBATCH --nodes=1
#SBATCH --gpus-per-node=8
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=56
#SBATCH --time=00:15:00
#SBATCH --output=/path/to/your/saiq-forge/outputs/running/qml_pilot_%j.out  # TODO update
#SBATCH --error=/path/to/your/saiq-forge/outputs/running/qml_pilot_%j.err   # TODO update

# RQ5 minimal pilot: VQC vs matched classical MLP on the CICIDS2017 pilot
# dataset (jobs/my_06_build_qml_pilot_dataset.sh must have been run first).
# Same container/wrapper as job 05 - see that template for why this is a
# single top-level srun, not nested under scripts/run_*.sh.

CONFIG_PATH="config/default.yml"
eval $(python3 -c "
import yaml
with open('$CONFIG_PATH') as f:
    cfg = yaml.safe_load(f)
print(f'WORKDIR=\"{cfg.get(\"workdir\", \"\")}\"')
print(f'LOGSDIR=\"{cfg.get(\"logsdir\", \"\")}\"')
")

TODAYS_DATE=$(date +%Y%m%d)
LOG_DIR="${LOGSDIR}/${TODAYS_DATE}_$SLURM_JOB_ID"
mkdir -p "$LOG_DIR"
cd $WORKDIR

export LUMI_QISKIT_SINGULARITY_CONTAINER_PATH=/appl/local/quantum/qiskit/qiskit_2.3.0_csc.sif
export WRAPPER_PATH=/appl/local/quantum/qiskit/run-singularity-with-gpu-affinity

srun --cpu-bind=mask_cpu:0xfe000000000000,0xfe00000000000000,0xfe0000,0xfe000000,0xfe,0xfe00,0xfe00000000,0xfe0000000000 \
    $WRAPPER_PATH $LUMI_QISKIT_SINGULARITY_CONTAINER_PATH \
    python3 main_qml_pilot_classifier.py --path_logdir="$LOG_DIR"

mv /path/to/your/saiq-forge/outputs/running/qml_pilot_$SLURM_JOB_ID.out $LOG_DIR/  # TODO update
mv /path/to/your/saiq-forge/outputs/running/qml_pilot_$SLURM_JOB_ID.err $LOG_DIR/  # TODO update
