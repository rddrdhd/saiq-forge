# SAIQ-Forge

A modular, config-driven framework for real-time network anomaly detection,
fusing multiple feature modalities with multiple detector classes. Built
and benchmarked on LUMI (Slurm, AMD MI250X/ROCm).

This README is operational (setup, running, configuring). For the
architecture rationale — why the pipeline is tiered, why windows are
overlap-parameterized, what each modality/detector class is for — see the
wiki (`wiki/`) and `../a0_THESIS/Body.tex`; this file deliberately doesn't
duplicate that.

## Status

Implemented so far: Temporal (`T`) and Behavioral (`B`) feature extractors,
a statistical detector (Z-score/IQR) as the CPU-only first pipeline tier,
loading for the real flow-record captures (datasets A/B/C). Not yet built:
Topological/Geographical extractors, classical-ML/deep-learning/graph/
quantum detectors, the CICIDS2017/UNSW-NB15 benchmark loader, HPC scale-out.

## Requirements

Python 3.9+, `pyyaml`, `pytest` to run the tests. No GPU/ROCm dependency is
needed for anything currently implemented (see "Slurm" below on why a GPU
template exists anyway).

## Environment setup

**On LUMI**, don't rely on the bare system `python3` — it won't have
`pyyaml`/`pytest`, and per LUMI's own Python docs, installing packages
directly into a large shared environment on Lustre is discouraged. For
this repo's current, tiny dependency list, a small venv layered on the
`cray-python` module is the right amount of tooling (a full `cotainr`
container is overkill for two pure-Python packages — that's worth revisiting
once heavier dependencies like scikit-learn or PyTorch+ROCm land in a later
slice). Run once, from the login node:

```
./scripts/setup_env.sh
```

This loads `cray-python`, creates a venv at `.venv/` (gitignored — pass a
different path as `$1` if you want it elsewhere), and installs
`requirements.txt` into it. Activate it in any shell before running the
CLI or tests:

```
source .venv/bin/activate
```

The Slurm templates in `jobs/` already do this activation themselves
(`module load cray-python` + `source .venv/bin/activate`, resolved relative
to the repo root), so a job submitted from this repo just needs
`./scripts/setup_env.sh` to have been run beforehand — no manual activation
needed inside the job.

**On a non-LUMI machine** (no `module` command), the script skips the
`module load` step automatically and just creates a plain venv:
`python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
works the same way by hand if you'd rather not use the script.

## Quickstart

1. Copy the example config and fill in your real paths:
   ```
   cp config/config.example.yaml config/config.yaml
   ```
   Edit `config/config.yaml`'s `project.workdir`/`datadir`/`logsdir` and
   `dataset.path`. This file is gitignored — it's where real LUMI paths and
   the project number live, never in a tracked file.

2. Run the pipeline:
   ```
   python -m saiq_forge.cli run --config config/config.yaml
   ```
   This prints one JSON alert record per time window: `{"start", "end", "score"}`,
   `score` an anomaly score in `[0, 1]`.

3. Run the tests:
   ```
   pytest tests/
   ```
   `tests/test_03_end_to_end_capture.py` is skipped unless you point it at a
   real capture file:
   ```
   SAIQ_FORGE_TEST_CAPTURE=/path/to/a/real/capture.csv pytest tests/test_03_end_to_end_capture.py -v
   ```

## Writing your own config

Start from `config/config.example.yaml`. Fields:

- `project.workdir/datadir/logsdir` — absolute paths, real values only in
  your gitignored `config.yaml`.
- `dataset.name` — a label (`dataset_a`/`dataset_b`/`dataset_c` for now;
  benchmark datasets come with the next slice).
- `dataset.path` — path to a flow-record CSV. Expected columns (semicolon-
  delimited): `TIME;DURATION;SRC IP;SRC PORT;DST IP;DST PORT;DUAL;PROTOCOL;
  APPLICATION;SRC PACKETS;DST PACKETS;SRC BYTES;DST BYTES`, with `TIME`/
  `DURATION` in microseconds since epoch. This is the real schema of
  datasets A/B/C on `/scratch/<project>/pathfinder/data/`, not a generic
  pcap.
- `features.modalities` — list of active extractors. Only `T` and `B` exist
  right now; anything else is rejected at load time with a clear error.
- `features.window.width_sec` / `overlap` — sliding window width `w` and
  overlap `δ`; step is computed as `w * (1 - δ)`. Phase 1's locked defaults
  are `width_sec: 10`, `overlap: 0.5`.
- `detectors.active` — list of `{class, method, threshold, tier}`. Only
  `{class: statistical, method: zscore|iqr}` exists right now.
- `execution.backend` — currently only `local` is implemented; which Slurm
  template you submit with is what actually picks CPU vs GPU (see below),
  not this field.

Swapping `method: zscore` → `method: iqr`, or changing `width_sec`/`overlap`,
or dropping to `modalities: ["T"]` only, are all just config edits — no code
changes needed. Adding a whole new modality or detector class is not (see
the wiki's honest modularity notes).

## Submitting Slurm jobs on LUMI

Job scripts are in `jobs/`, following a `template_*` (committed, placeholder
account/paths) convention — copy one to `jobs/my_<name>.sh` (gitignored,
same as `config.yaml`) and fill in your real `#SBATCH --account=` before
submitting:

- **`template_00_smoke_test_cpu.sh`** — runs the import + windowing unit
  tests. `small` partition, minimal resources.
- **`template_01_phase1_baseline_cpu.sh`** — runs the actual pipeline.
  `small` partition (billed per-core, not per-node — this workload doesn't
  need a whole node).
- **`template_01_phase1_baseline_gpu.sh`** — identical pipeline, `dev-g`
  partition instead. The statistical detector doesn't benefit from a GPU;
  this exists only so you have a runnable option if that's the allocation
  you actually have available.

Each script reads `workdir`/`datadir`/`logsdir` out of your config file at
job start (`sbatch jobs/my_01_phase1_baseline_cpu.sh config/config.yaml`,
or edit the `CONFIG=` default at the top of the script) — no path is
hardcoded in the script itself.

I won't run `sbatch` for you (state-changing Slurm command) — copy the
template, fill in your account, and submit it yourself.
