---
title: Research Questions (RQ1–RQ5)
category: Concepts
summary: The five falsifiable research questions structuring the thesis, each with an explicit pass/fail criterion.
tags: [concept, vocabulary, research-questions]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# Research Questions (RQ1–RQ5)

## Description

Five research questions structure the thesis and, by extension, what
SAIQ-Forge as a codebase needs to be able to measure. Each is paired with
an explicit criterion for when it counts as answered — not just a
direction of inquiry.[^1]

**RQ1 — Real-time anomaly detection.** Can the framework detect and
classify anomalies in real time, and at what quality under realistic
throughput? Criterion: ≥10,000 packets/sec sustained, F1 ≥ 0.85 on the
CICIDS2017 test split, mean alert latency < 500 ms.[^2]

**RQ2 — Multi-layer feature contribution.** Does combining all four
[[feature-modalities](pages/feature-modalities.md)] improve detection over
any single modality? Criterion: a statistically significant improvement
(paired Wilcoxon signed-rank test, Benjamini–Hochberg FDR correction at
q = 0.05) of the fused model's F1/ROC-AUC over the best single-modality
baseline, sustained across ≥2 of 3 evaluated datasets.[^3]

**RQ3 — Method cost-effectiveness.** Which combination of
[[detector-classes](pages/detector-classes.md)] gives the best
quality-vs-cost trade-off under real-time limits? Defined as F1 divided by
mean per-batch inference latency; answered via a Pareto-optimal trade-off
curve rather than a single winner.[^4]

**RQ4 — HPC scalability.** How much does HPC parallelization reduce
latency and raise throughput vs. single-node execution? Measured as
throughput, mean and P99 alert latency, and memory use across 1/8/32/128
nodes on Karolina and LUMI; a positive result requires super-linear
throughput scaling with node count.[^5]

**RQ5 — Quantum-assisted detection.** Can VQCs or quantum kernel methods
measurably improve over classical models of matched capacity? Answered by
comparing a VQC classifier against a classical MLP matched by parameter
count on a 16-feature binary task; a statistically significant
improvement, or comparable performance under noise, both count as
reportable outcomes — so does a negative result, analyzed against barren
plateau effects and feature expressivity limits.[^6]

## Appearances in Sources

- [[phd-thesis](pages/phd-thesis.md)] — defines all five, §Research Questions and Scientific Contribution, and revisits them throughout: the [[experimental-phases](pages/experimental-phases.md)] each target specific RQs, and the [[detector-classes](pages/detector-classes.md)]/[[feature-modalities](pages/feature-modalities.md)] pages exist specifically to be ablated against RQ2/RQ3.

## Related Concepts

- [[experimental-phases](pages/experimental-phases.md)] — Phase 1→RQ1, Phase 2→RQ2, Phase 3→RQ1/RQ4, Phase 4→RQ5, Phase 5→RQ3 (and the final word on RQ1/RQ2 under real-time constraints)
- [[saiq-forge-framework](pages/saiq-forge-framework.md)] — the framework whose config-driven design exists specifically to make RQ2/RQ3 answerable as config variants rather than separate implementations
- [[quantum-classical-matching-protocol](pages/quantum-classical-matching-protocol.md)] — the matching methodology RQ5 depends on

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Research Questions and Scientific Contribution L36 — "Each question is accompanied by an explicit set of criteria that specifies the conditions under which it will be considered answered"
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Research Questions and Scientific Contribution L40-42 — RQ1 statement and criteria
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Research Questions and Scientific Contribution L44-46 — RQ2 statement and criteria
[^4]: [[phd-thesis](pages/phd-thesis.md)] §Research Questions and Scientific Contribution L48-50 — RQ3 statement and criteria
[^5]: [[phd-thesis](pages/phd-thesis.md)] §Research Questions and Scientific Contribution L52-54 — RQ4 statement and criteria
[^6]: [[phd-thesis](pages/phd-thesis.md)] §Research Questions and Scientific Contribution L56-58 — RQ5 statement and criteria
