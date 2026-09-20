---
title: "Decision: Sliding Window Width and Overlap as Tunable, Not Fixed"
category: Decisions
summary: Aggregated features use a sliding window of width w and step w(1-δ); both are treated as network-dependent tuning parameters swept empirically rather than fixed constants.
tags: [decision, windowing, streaming]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# Decision: Sliding Window Width and Overlap as Tunable, Not Fixed

## Description

**Decision.** Temporal, topological, and behavioral features (the ones
requiring aggregation) are computed over a sliding window of width `w`
with step `s = w(1 - δ)`, where δ ∈ (0,1) is the overlap fraction. The
overlap exists specifically so an anomaly near a window boundary is fully
captured in at least one window.[^1] Neither `w` nor `δ` is hard-coded:
Phase 1 defaults to w=10s, δ=0.5, and Phase 3 formally sweeps
w ∈ {1,5,10,30,60}s and δ ∈ {0.25,0.5,0.75}, reporting the result as a
latency-accuracy trade-off curve.[^2]

**Why.** Optimal window size is network-dependent and there's a genuine
trade-off, not a single right answer: high-throughput links need small
`w` to bound latency; sparse networks need large `w` to accumulate enough
statistical evidence per window. Small `w` also reduces the evidence
available specifically for behavioral/topological features, while large
`w` raises memory and latency.[^3] This is directly why
[[detector-classes](pages/detector-classes.md)]' Local Outlier Factor is
flagged as an *offline-only* upper-bound reference in Phase 1 rather than
a streaming candidate — LOF doesn't support streaming inference at all,
which windowing choices can't fix.[^4]

**A concrete lesson already learned (Phase 0), worth carrying into code.**
The topological scanning heuristic (>5 unique destination IPs or >10
unique destination ports) is *not* comparable across windows of different
length without normalization: it flagged 90/91 candidate flows on a
5-minute capture (Dataset A) purely from normal DNS/browsing behavior, but
was calibrated against a 5-hour capture (Dataset C) where the same
absolute threshold is far more permissive. The fix decided in the thesis
is to express topological features as **rates** (contacts per unit time),
not raw counts — this should be a hard requirement on any topological
feature extractor implementation, not an optional refinement.[^5]

**Consequence for the rewrite.** Window width/overlap should be a runtime
parameter from day one (not something bolted on before Phase 3), and any
count-based feature (especially topological) should be designed to
normalize by window length from the start, given Phase 0 already
demonstrated what goes wrong otherwise.

## Appearances in Sources

- [[phd-thesis](pages/phd-thesis.md)] — §Sliding Window and Overlap Strategy (design), §Window Size Calibration (the Phase 3 sweep procedure), §Results and Observations / §Phase 0 Limitations (the Dataset A/C normalization lesson)

## Related Concepts

- [[feature-modalities](pages/feature-modalities.md)] — temporal, topological, and behavioral modalities all depend on this windowing; geographical does not
- [[experimental-phases](pages/experimental-phases.md)] — Phase 0 surfaced the normalization problem; Phase 1 sets the working default; Phase 3 formally sweeps it
- [[datasets](pages/datasets.md)] — Dataset A vs. Dataset C is the concrete evidence for why this decision matters

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Sliding Window and Overlap Strategy L257-259 — window/step definition and the boundary-anomaly rationale for overlap
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Window Size Calibration L381-383 — Phase 3 sweep values and Pareto-frontier reporting
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Window Size Calibration L381-383 [synthesis] — the latency/evidence-quality trade-off argument
[^4]: [[phd-thesis](pages/phd-thesis.md)] §Models (Phase 1) L546 — "Local Outlier Factor: ... evaluated offline (LOF does not support streaming inference and serves as an offline upper-bound reference)"
[^5]: [[phd-thesis](pages/phd-thesis.md)] §Results and Observations / §Phase 0 Limitations and Forward Actions [synthesis] L473-474, L502 — the Dataset A false-flag finding and "topological features must be expressed as rates... rather than absolute counts"
