#!/bin/bash -e

# ── Env hints ─────────────────────────────────────────────────────────
export POLARS_MAX_THREADS=$SLURM_CPUS_PER_TASK
export PYTHONFAULTHANDLER=1
export NCCL_SOCKET_IFNAME=hsn0,hsn1,hsn2,hsn3
export MPICH_GPU_SUPPORT_ENABLED=1
export OMP_NUM_THREADS=7

export RANK=$SLURM_PROCID
export LOCAL_RANK=$SLURM_LOCALID 
export WORLD_SIZE=$SLURM_NPROCS
export MASTER_ADDR=$(python3 scripts/get_master.py "$SLURM_NODELIST")
export MASTER_PORT=29600

TODAYS_DATE=$(date +%Y%m%d)

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
if [ "${RANK}" -eq 0 ]; then
echo "============================================================"
echo "  saiq-forge — main"
echo "============================================================"
echo "Job ID    : $SLURM_JOB_ID"
echo "Node      : $(hostname)"
echo "CPUs      : $SLURM_CPUS_PER_TASK"
echo "Date      : $(date)"
echo "Workdir   : $PATH_WORKDIR"
echo "Datadir   : $PATH_DATADIR"
echo "Log dir   : $PATH_OUTPUT"
echo "============================================================"
echo ""
fi

# ── Run script ───────────────────────────────────────────────────────────────
cd $PATH_WORKDIR
python3 core/main.py -v -s
EXIT_CODE=$?
exit $EXIT_CODE