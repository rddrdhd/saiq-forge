#!/bin/bash -e

#── Input attrs ───────────────────────────────────────────────────────────────
PATH_OUTPUT=""
PATH_WORKDIR=""
PATH_DATADIR=""
for arg in "$@"
do
    case $arg in
        --path_output=*)
        PATH_OUTPUT="${arg#*=}"  
        shift
        ;;
        --path_workdir=*)
        PATH_WORKDIR="${arg#*=}"  
        shift
        ;;
        --path_datadir=*)
        PATH_DATADIR="${arg#*=}"  
        shift
        ;;
    esac
done
# ── Info header ───────────────────────────────────────────────────────────────

echo "============================================================"
echo "  saiq-forge — profiling data"
echo "============================================================"
echo "Job ID    : $SLURM_JOB_ID"
echo "Node      : $(hostname)"
echo "CPUs      : $SLURM_CPUS_PER_TASK"
echo "Date      : $(date)"
echo "Workdir   : $PATH_WORKDIR"
echo "Datadir   : $PATH_DATADIR"
echo "============================================================"
echo ""

cd $PATH_WORKDIR

# ── Prepare env for pyarrow──────────────────────────────────────────────────────
# create env on first run to use pyarrow
#python3 -m venv --system-site-packages my_profile_env # should work with the pytorch mdoule too
#pip install --no-cache-dir pyarrow

source my_profile_env/bin/activate

# ── Run script ───────────────────────────────────────────────────────────────
python3 scripts/profile_data.py -v -s
EXIT_CODE=$?
exit $EXIT_CODE