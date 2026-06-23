# SAIQ Forge
https://github.com/rddrdhd/saiq-forge

Statistical/AI/Quantum methods for network anomaly detection in HPC environment.

In development as a part of my [PhD thesis](https://www.overleaf.com/project/69b27d1754e1e94ecea885e8).

## How to

0. copy the config/default_template.yml to config/default.yml, and update values.
1. copy the template from "jobs" directory and edit the "TODO"s
2. submit the edited script by calling "sbatch my_edited_script.sh"

The numbers in /jobs & /tests are corresponding. (eg. job 01 calls test 01 etc)

Start with generating baseline for your data (sbatch jobs/my_03_profile_data.sh), then train the network (sbatch jobs/template_02_main.sh), and you can also check the data in Tensorboard (easiest way is to go to https://www.lumi.csc.fi/pun/sys/dashboard/batch_connect/sys/ood-tensorboard/session_contexts/new)

## Data
Apart from our internal datasets 24-01-classification, classification_2 & generated_data_randomized, I work with benchmarking data too. 

- CICIDS207 https://www.unb.ca/cic/datasets/ids-2017.html (use script with built container to generate the right format)
    - ./scripts/build_container_lumi.sh
    - singularity exec --bind $PWD:/workspace --pwd /workspace saiq-forge.sif python3 scripts/pcap_to_parquet.py