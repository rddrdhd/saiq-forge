---
title: Experimental Phases (0–5)
category: Concepts
summary: The six sequential phases of the thesis's empirical plan, each with an objective, targeted research question(s), and an explicit success criterion.
tags: [concept, vocabulary, experimental-plan, phases]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# Experimental Phases (0–5)

## Description

The thesis structures all empirical work as six phases, each building on
its predecessor's outputs so later performance claims are always measured
against baselines evaluated under identical conditions.[^1] This is the
vocabulary that should anchor `Experiments`-category wiki pages once
phases are actually run in code — a phase's *definition* lives here; its
*results* belong in a separate Experiments-category page once produced.

**Phase 0 — Exploratory Analysis.** *Status: complete.* Rule-based
screening (IQR/Z-score/scanning heuristics) on three real-world captures
(datasets A/B/C) to establish data quality baselines and produce noisy
weak-label anomaly candidates, plus the graph/timelapse/volume
visualization infrastructure used throughout. No formal success criterion
beyond producing these outputs — it's foundational, not confirmatory.[^2]

**Phase 1 — Baseline Models.** *Status: in progress.* Statistical
screening, Isolation Forest, One-Class SVM, LOF, and (where labels exist)
Random Forest/XGBoost, evaluated under the fixed protocol that persists
through Phase 5. Targets RQ1. Success: ≥1 unsupervised baseline reaches
F1 ≥ 0.70 on CICIDS2017, and the Phase 0 flags get a manual precision
estimate.[^3]

**Phase 2 — Advanced Models and Ablation Study.** *Status: not started.*
LSTM/TCN autoencoders, a VAE, a static GNN detector, an IP-sequence
(Word2Vec) model, and multi-modal fusion, evaluated across seven feature
configurations (single-modality through all-four) — a 6×7 result matrix
per metric per dataset. This is the thesis's central empirical
contribution and directly targets RQ2. Success: the full four-modality
model beats the best single-modality baseline with statistical
significance (Wilcoxon + Benjamini–Hochberg FDR, q = 0.05), and a complete
per-modality contribution table is produced.[^4]

**Phase 3 — Real-Time Testing and HPC Benchmarking.** *Status: not
started.* Sweeps node count (1/8/32/128), window width w
({1,5,10,30,60}s), overlap δ ({0.25,0.5,0.75}), and model tier
(statistical / +classical-ML / full pipeline) on Karolina and LUMI.
Targets RQ1 and RQ4. Success: the full pipeline hits ≥10,000 pkt/s and
≤500ms mean / ≤2,000ms P99 latency on ≥8 nodes, with a
throughput-vs-node-count scaling curve for every tier.[^5]

**Phase 4 — Quantum Exploration.** *Status: preliminary pilot run,
reduced scale, not the formal protocol.* Compares a VQC classifier against
a matched classical MLP on a 16-feature binary task, sweeping circuit
depth to characterize barren-plateau onset. Targets RQ5, structured around
three falsifiable hypotheses (H1 comparable capability, H2 representational
benefit, H3 conditional-not-universal benefit). Success: a statistically
significant VQC improvement on ≥1 dataset — but a negative result is
explicitly treated as an equally valid, reportable outcome.[^6]

**Phase 5 — Combination and Tuning.** *Status: not started.* Synthesizes
Phases 1–4: sweeps feature combinations, single/ensemble model
combinations, aggregation strategies, and Pareto-optimal window
configurations from Phase 3, reporting a Pareto frontier in F1-vs-latency
space. Targets RQ3 and provides the final word on RQ1/RQ2 under real-time
constraints. Success: ≥5 distinct Pareto-frontier operating points
spanning ≥1 order of magnitude in latency, with the best point
significantly beating the best Phase 1 baseline.[^7]

## Appearances in Sources

- [[phd-thesis](pages/phd-thesis.md)] — defines all six phases in §Experimental Plan, and separately discusses expected results/challenges per phase in §Goals and Discussion

## Related Concepts

- [[research-questions](pages/research-questions.md)] — each phase targets specific RQs, listed above
- [[feature-modalities](pages/feature-modalities.md)] — the seven ablation configurations in Phase 2 are combinations of these four
- [[detector-classes](pages/detector-classes.md)] — Phase 1 covers statistical + some classical ML; Phase 2 adds deep learning and graph-based; Phase 4 is the quantum class
- [[datasets](pages/datasets.md)] — Phase 0 uses only real-world captures A/B/C; benchmarks (CICIDS2017/UNSW-NB15) enter from Phase 1
- [[three-stage-ground-truth-labeling](pages/three-stage-ground-truth-labeling.md)] — Stage 1 corresponds to Phase 0, Stage 2 to Phase 1, Stage 3 to Phase 2's red-team validation
- [[quantum-classical-matching-protocol](pages/quantum-classical-matching-protocol.md)] — the full Phase 4 protocol, as distinct from the preliminary reduced-scale pilot already run

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Experimental Plan L436-439 — "structured into six sequential phases. Each phase builds directly on the outputs of its predecessor... performance gains claimed by advanced models are always measured against well-established baselines evaluated under identical conditions"
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Phase 0: Exploratory Analysis [synthesis] L445-505 — objective, datasets, screening methodology, results
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Phase 1: Baseline Models [synthesis] L518-556 — objective, models list, success criteria
[^4]: [[phd-thesis](pages/phd-thesis.md)] §Phase 2: Advanced Models and Ablation Study [synthesis] L558-605 — objective, models, ablation design table, success criteria
[^5]: [[phd-thesis](pages/phd-thesis.md)] §Phase 3: Real-Time Testing and HPC Benchmarking [synthesis] L607-644 — swept variables, metrics, success criteria
[^6]: [[phd-thesis](pages/phd-thesis.md)] §Phase 4: Quantum Exploration [synthesis] L646-701 — hypotheses H1-H3, experimental setup, success criteria, preliminary pilot
[^7]: [[phd-thesis](pages/phd-thesis.md)] §Phase 5: Combination and Tuning [synthesis] L703-729 — configuration space, Pareto analysis, success criteria
