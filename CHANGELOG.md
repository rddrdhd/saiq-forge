# CHANGELOG

## v0.2 - 202605121
Step 2: try sharding in parallel
0. copy the config/default_template.yml to config/default.yml, and update values.
1. copy the template from "jobs" directory and edit the "TODO"s
2. submit the edited script by calling "sbatch my_edited_script.sh"

The numbers in /jobs & /tests are corresponding. (eg. job 01 calls test 01 etc)

## v0.1 - 20260519
Step 1: Prepare the environment. For now just on LUMI using containers and try the imports.

0. `ssh lumi`
1. build the container by running the build_container_lumi.sh on LUMI (.sif files are in gitignore)
2. test the container by editing `template_sbatch_container.sh` and submit it with `sbatch`.