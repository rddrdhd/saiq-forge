# SAIQ Forge
https://github.com/rddrdhd/saiq-forge

Statistical/AI/Quantum methods for network anomaly detection in HPC environment.

In development as a part of my PhD thesis.

## Repository structure & conventions

To keep account numbers, usernames, and other cluster-specific values out of the public repo,
every piece of config comes in two flavours:

| Suffix | Meaning | Tracked by git? |
|---|---|---|
| `*_template.*` / `jobs/template_NN_*.sh` | Public, placeholders only (`project_XXXXX`, `/path/to/...`) | Yes |
| `my_*` (any file/dir starting with `my_`) | Your personal copy, real values | No — matched by `.gitignore` |

**Workflow:** copy the template, fill in the placeholders, save it as `my_...`. Never put a real
account number, absolute path with your username, or token directly into a tracked (non-`my_`,
non-`config/default.yml`) file — `config/default_template.yml` and `jobs/template_*.sh` are the
only files anyone else cloning the repo will see.

The numbers in `/jobs` & `/tests` correspond (job `NN` exercises test `NN`).

```
config/default_template.yml   → copy to config/default.yml (gitignored) and edit
jobs/template_NN_*.sh         → copy to jobs/my_NN_*.sh (gitignored) and edit the TODOs
```

## Execution environments

Three separate, non-interchangeable runtimes are used on LUMI — don't mix them up:

1. **Project container** `saiq-forge.sif` — built by `scripts/build_container_lumi.sh` from
   `environment-container.yml` (conda-forge only, no `defaults` channel/Anaconda packages —
   licence restriction on LUMI). Used for pcap→parquet conversion and import smoke tests.
2. **`my_vlq_venv/`** — a venv on top of the `pytorch/2.4` module, built by
   `scripts/build_vlq_venv.sh`. Holds `py4lexis`, `quantum-as-a-service` (QaaS), `qiskit`,
   `iqm.qiskit_iqm`. The only environment that can reach the real **VLQ** quantum processor.
3. **Official CSC Qiskit container** `/appl/local/quantum/qiskit/qiskit_2.3.0_csc.sif` — not built
   by this repo, already installed on LUMI. Runs `qiskit-aer-gpu` (custom ROCm/HIP build for
   LUMI's AMD MI250X GPUs — the plain PyPI `qiskit-aer-gpu` wheel is CUDA-only and won't work
   here) for **local GPU simulation**, no VLQ hardware or LEXIS token involved. See
   [docs.csc.fi/apps/qiskit](https://docs.csc.fi/apps/qiskit/).

## How to

0. Copy `config/default_template.yml` → `config/default.yml`, and update the values.
1. Copy a template from `jobs/` → `jobs/my_NN_....sh`, edit the "TODO"s.
2. Submit it: `sbatch jobs/my_NN_....sh`.

Suggested order:

- **Container smoke test:** `sbatch jobs/my_01_test_container.sh`
- **Data profiling** (build the baseline JSON used everywhere else):
  `sbatch jobs/my_03_profile_data.sh` — see `PROFILE_DATA.md` for how to read the output.
- **Classical training** (autoencoder, per `config/default.yml`):
  `sbatch jobs/my_02_main.sh` — check progress in Tensorboard, easiest via
  https://www.lumi.csc.fi/pun/sys/dashboard/batch_connect/sys/ood-tensorboard/session_contexts/new
- **VLQ hardware connectivity check** (real quantum processor, needs a LEXIS token — see below):
  `sbatch jobs/my_04_vlq_example_ghz.sh`
- **Quantum simulator GHZ example** (no hardware/token needed, runs on LUMI's own GPUs):
  `sbatch jobs/my_05_vlq_example_ghz_simulator.sh` — this is the minimal example to get a
  quantum circuit running end-to-end on LUMI before attempting a hybrid/quantum autoencoder.

## Data
Apart from our internal datasets *24-01-classification*, *classification_2* & *generated_data_randomized*, let's work with benchmarking data too. Let's start with [*CICIDS2017*](https://www.unb.ca/cic/datasets/ids-2017.html), specifically with *Friday-WorkingHours.pcap*.
But to work the same, we want them in the same format as our data. Instead of treating every packet as a separate line, we group packets sharing the same 5-tuple (Src IP, Dst IP, Src Port, Dst Port, Protocol) into a single bidirectional flow, and store as parquet instead of pcap:
- `srun --account=project_XXXXXXXXX --partition=small-g --nodes=1 --ntasks=1 --cpus-per-task=16 --time=01:00:00 --pty bash` # let's not run this on login node
- `./scripts/build_container_lumi.sh` # build container if not built already
- `singularity exec --bind "/pfs,/scratch,/project" --pwd $PWD saiq-forge.sif python3 scripts/fast_pcap_to_parquet.py`

## VLQ access
Access to the VLQ quantum processor is gated by a LEXIS token, valid ~5 days. Get one by running
`./scripts/run_get_lexis_token.sh` — it prints a URL, click it and sign in. Re-run the same script
whenever `main_vlq_example_ghz.py` reports an expired/missing token.

## WIP
Both the LUMI classical/autoencoder path and the VLQ execution path work end-to-end, but as
separate programs. Next step: connect them into a single run (`main_vlq.py`) so classical and
quantum results can be produced under matched conditions.
