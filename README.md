# SAIQ Forge
https://github.com/rddrdhd/saiq-forge

Statistical/AI/Quantum methods for network anomaly detection in HPC environment.

In development as a part of my [PhD thesis](https://www.overleaf.com/project/69b27d1754e1e94ecea885e8).

## How to

0. copy the *config/default_template.yml* to *config/default.yml*, and update values.
1. copy the template from *jobs* directory and edit the "TODO"s
2. submit the edited script by calling `sbatch my_edited_script.sh`

The numbers in */jobs* & */tests* are corresponding. (eg. job 01 calls test 01 etc)

Start with generating baseline for your data (`sbatch jobs/my_03_profile_data.sh`), then train the network (`sbatch jobs/my_02_main.sh`) according to your *cofing/default.yml*, and you can also check the data in Tensorboard (easiest way is to go to https://www.lumi.csc.fi/pun/sys/dashboard/batch_connect/sys/ood-tensorboard/session_contexts/new)

## Data
Apart from our internal datasets *24-01-classification*, *classification_2* & *generated_data_randomized*, let's swork with benchmarking data too. Let's start with [*CICIDS2017*](https://www.unb.ca/cic/datasets/ids-2017.html), specifically with *Friday-WorkingHours.pcap*.
But to work the same, we want them in the same format as our data. Instead of treating every packet as a separate line, we group packets sharing the same 5-tuple (Src IP, Dst IP, Src Port, Dst Port, Protocol) into a single bidirectional, and also in parquet instead of pcap:
- `srun --account=project_46xxxxxxx --partition=small-g --nodes=1 --ntasks=1 --cpus-per-task=16 --time=01:00:00 --pty bash` # let's not run this on login node lol
- `./scripts/build_container_lumi.sh` # build container if not built already
- `singularity exec --bind "/pfs,/scratch,/project" --pwd $PWD saiq-forge.sif python3 scripts/fast_pcap_to_parquet.py`

## WIP
Adding VLQ access. First step is to get the Lexis token. To get it, run `./scripts/run_get_lexis_token.sh`. Then, in the terminal, you'll see an URL to click and sign up to your account.
