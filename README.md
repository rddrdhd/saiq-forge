# SAIQ Forge
https://github.com/rddrdhd/saiq-forge

Statistical/AI/Quantum methods for network anomaly detection in HPC environment.

In development as a part of my [PhD thesis](https://www.overleaf.com/project/69b27d1754e1e94ecea885e8).

## Plan/Overview

### 1. Data

Working with traffic data within the network. For testing phase, I have few un-labeled datasets with this format (in csv/parquet files):

```TIME; DURATION; SRC IP; SRC PORT; DST IP; DST PORT; DUAL; PROTOCOL; APPLICATION; SRC PACKETS; DST PACKETS; SRC BYTES; DST BYTES;```

- Time is a nanosecond epoch - needs to be normalized first
- Duration is in microseconds 
- DUAL is if this record is bidirectional (to not double-count bytes) {0,1}
- Application inludes NDS, SSL, ..., UNKNOWN - not every record have this label
- Ratio features can be derivable: bytes-per-packet, duration-per-packet, src/dst byte assymetry ratio...

I also want to work on both - already collected data & the live streaming. That's why I'll use a "batching" strategy, which can be fine-tuned per network/availible hardware resources. The parameters to tune should be the size of sliding window & the size of overlap. Still thinking if it should be traffic-time related, or by the number of data in each window
```
|-- window 1 ---|
          |-- window 2 ---|
                    |-- window 3 ---|
```


### 2. Anomaly taxonomy

- Point anomaly = per-flow outlier - anomaly detectable from a sigle record (like extremely high values, weird combinations of specific attributes).
    - Detection using Z-score, IQR
- Contextual anomaly = per-batch behavioral/temporal outlier - anomaly dectable per sliding window (batch/set) of several records (like port scanning etc)
    - Detection using sliding window aggregation counters + EWMA baseline + threshold
- Collective anomaly = per-cluster suspicious patters - visible after grouping (like coordinated probing)
    - Detection using DBSCAN/Isolation Forest on flagged subsets produced by the contextual stage

### 3. Planned architecture
Something like this (Claude AI proposed this, I kinda like it.)

```
saiq-forge/
├── config/
│   ├── default.yaml             # global config (paths, thresholds, window sizes)
│   └── hpc.yaml                 # cluster-specific overrides (node count, SLURM params)
│
├── ingestion/
│   ├── __init__.py
│   ├── loader.py                # read parquet/csv → Polars/Pandas DataFrame
│   ├── schema.py                # dtype coercions, TIME normalization, ratio features
│   └── batcher.py               # overlapping window batching logic
│
├── core/
│   ├── __init__.py
│   ├── registry.py              # module registry — swap stat/DL/quantum detectors
│   ├── pipeline.py              # orchestrates: ingest → detect → inspect → output
│   └── flag_store.py            # in-memory + on-disk flag accumulator
│
├── modules/
│   ├── statistical/             # Phase 1 (this document)
│   │   ├── __init__.py
│   │   ├── feature_eng.py       # derive ratios, per-group stats
│   │   ├── point_detector.py    # Z-score, IQR, Mahalanobis per flow
│   │   ├── contextual_detector.py  # sliding window counters + EWMA
│   │   └── cluster_inspector.py # DBSCAN / Isolation Forest on flagged set
│   │
│   ├── deep_learning/           # Phase 2 (stub)
│   │   └── __init__.py          # CNN-LSTM, Autoencoder — to be implemented
│   │
│   └── quantum/                 # Phase 3 (stub)
│       └── __init__.py          # QML / quantum-inspired SVM — research module
│
├── hpc/
│   ├── slurm_submit.py          # generate + submit SLURM job arrays
│   ├── dask_cluster.py          # dask-jobqueue SLURMCluster setup
│   └── job_template.sh          # SBATCH template
│
├── visualization/
│   ├── __init__.py
│   ├── overview_plots.py        # traffic summary: flows/time, byte distribution
│   ├── flag_plots.py            # flag timeline, flag-rate heatmap (src→dst)
│   └── cluster_plots.py        # UMAP/t-SNE of flagged clusters, DBSCAN scatter
│
├── output/
│   ├── writer.py                # structured output writer (see Section 6)
│   └── report.py                # generate per-batch markdown/HTML summary
│
├── tests/
│   ├── test_batcher.py
│   ├── test_point_detector.py
│   └── test_contextual_detector.py
│
├── main.py                      # CLI entry point
└── environment.yml              # conda env spec
```
Design principles:

- Every detector module is a class implementing a common Detector interface with .fit(df) and .transform(df) → FlaggedDF methods.
- The registry.py maps a string key ("statistical", "autoencoder", "quantum_svm") to a detector class, loaded by config. Swapping modules = changing one config line.
- No module directly touches I/O — that is the pipeline's job. Modules receive DataFrames and return DataFrames with appended flag columns.

## MVP

I want to start with parallelized statistical methods to work with the already collected datasets to find some statistical outliers. So my TODOs are:

- [ ] Feature engineering - compute per-batch
- [ ] Point Anomaly Detector - compute per record (Z-score, IQR fence, Mahanobis, ...) 
- [ ] Contextual detector - just group by DST_IP/SRC_IP etc... to scanning/burst patterns and similar
- [ ] Cluster inspector - isolation forest, DBSCAN, cluster characterisation
- [ ] Visualizations & reports
- [ ] SLURM strategy

### Proposed plan (Claude.ai)
Sprint 1 — Foundation (1–2 days)

 - [ ] schema.py: TIME normalization, ratio features, dtype coercions
 - [ ] loader.py: read parquet with Polars lazy scan
 - [ ] batcher.py: overlapping window generator
 - [ ] Write test_batcher.py with a synthetic 1000-row fixture

Sprint 2 — Point Detection (2–3 days)

 - [ ] feature_eng.py: per-group baselines
 - [ ] point_detector.py: Z-score + IQR + Mahalanobis
 - [ ] writer.py: write flags.parquet with appended columns
 - [ ] overview_plots.py: byte/packet distribution visualizations

Sprint 3 — Contextual Detection (2–3 days)

 - [ ] contextual_detector.py: fan-in, port scan, EWMA burst, DNS burst
 - [ ] Persist EWMA state across batches (baseline_stats.json)
 - [ ] flag_plots.py: flag timeline, SRC→DST heatmap

Sprint 4 — Cluster Inspection (2–3 days)

 - [ ] cluster_inspector.py: Isolation Forest + DBSCAN + characterization
 - [ ] cluster_plots.py: UMAP scatter, cluster radar
 - [ ] report.py: per-batch HTML summary

Sprint 5 — HPC Integration (2 days)

 - [ ] slurm_submit.py + job_template.sh
 - [ ] dask_cluster.py for interactive mode
 - [ ] Validate on a real parquet file across 2+ nodes

Sprint 6 — Polish + Hooks (1–2 days)

 - [ ] registry.py: module registry pattern
 - [ ] Stub deep_learning/__init__.py and quantum/__init__.py with the same Detector interface
 - [ ] run_comparison.png generator
 - [ ] README.md and environment.yml


 ## Key design decisions (Claude.ai)
 |Decision | Rationale |
 |---|---|
 Polars as primary DataFrame engine | 5–10× faster than Pandas for the aggregation-heavy feature engineering required; lazy evaluation avoids loading full parquet into memory
 Overlapping windows (50% overlap default) | Prevents boundary artifacts; validated in patent literature (US11128648) and standard practice for streaming anomaly detection
 Two-stage flagging: statistical → cluster | Running DBSCAN on full batches is expensive and noisy; running it only on flagged subsets reduces cost and increases signal-to-noise
 EWMA for burst detection, not raw thresholdsE | WMA adapts to time-of-day and day-of-week traffic patterns; a static threshold would generate excessive false positives during legitimate traffic peaks
 Isolation Forest before DBSCAN | Isolation Forest produces a continuous anomaly score that can be used to filter before DBSCAN, reducing DBSCAN's sensitivity to the eps / min_samples hyperparameters
 Structured output with metadata JSON | Enables reproducibility and cross-module comparison; critical for the DL and quantum phases where you want identical batch conditions
 Detector interface pattern | Allows statistical, DL, and quantum modules to be evaluated on the same data pipeline without architectural changes — the core research need