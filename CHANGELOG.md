# CHANGELOG
## v0.1 - 20260519
Step 1: Prepare the environment. For now just on LUMI using containers and try the imports.

0. `ssh lumi`
1. build the container by running the build_container_lumi.sh on LUMI (.sif files are in gitignore)
2. test the container by editing `template_sbatch_container.sh` and submit it with `sbatch`.