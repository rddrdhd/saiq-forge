---
title: "Decision: Tiered Statistical-then-DL Filtering Pipeline"
category: Decisions
summary: Cheap statistical detectors run on every record on CPU first; expensive ML/DL detectors on GPU only see the fraction that survives the statistical filter.
tags: [decision, real-time-pipeline, cost-effectiveness]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# Decision: Tiered Statistical-then-DL Filtering Pipeline

## Description

**Decision.** Statistical models (Z-score/IQR/entropy) run on the CPU as
the first pass over *all* traffic; ML and DL models run on the GPU as a
second, lower-throughput pass applied only to the candidate anomalies that
survive the statistical filter, scored in batches via GPU-accelerated
forward passes.[^1]

**Why.** This is a direct, structural answer to
[[research-questions](pages/research-questions.md)] RQ3 (cost-effectiveness)
rather than a generic performance optimization: the thesis states plainly
that this "ensures that the expensive DL models process only a small
fraction of total traffic in cases where getting GPU resources might be
expensive" — the tiering exists because GPU time on shared HPC allocations
is a cost to be economized, not just a latency concern.[^2] It's also what
makes the RQ1 latency target (≤500ms mean alert latency) plausible at all:
the thesis's own expectation is that DL models alone would add 200–500ms
per batch, putting the full pipeline "near the boundary of the latency
target" if DL saw *all* traffic — the tiered architecture is explicitly
named as the mitigation if that boundary is crossed.[^3]

**Consequence for the rewrite.** The statistical tier isn't a discardable
"first draft" baseline to be replaced once ML models exist — it's a
permanent architectural component even in the target system, since its
job (bulk-filtering to protect GPU/DL cost) doesn't go away once better
models are added. Any detector interface design should treat "does this
record even reach me" as a first-class routing decision, not assume every
detector sees every record.

## Appearances in Sources

- [[phd-thesis](pages/phd-thesis.md)] — §Parallelization Strategy (the tiering itself), §Real-Time Testing (the expected DL latency cost this tiering is meant to absorb)

## Related Concepts

- [[detector-classes](pages/detector-classes.md)] — statistical vs. classical-ML/deep-learning/graph-based is exactly the tier boundary
- [[research-questions](pages/research-questions.md)] — RQ1 (latency target) and RQ3 (cost-effectiveness) both depend on this decision
- [[experimental-phases](pages/experimental-phases.md)] — Phase 3 sweeps "model tier" (statistical only / +classical ML / full pipeline) as one of its explicit variables, directly testing this decision's effect

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Parallelization Strategy L379 — "Statistical models execute on the CPU in the first filtering layer; ML and DL models execute on the GPU in a second, lower-throughput layer applied only to candidate anomalies that survive the statistical filter"
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Parallelization Strategy L379 — "This tiered architecture ensures that the expensive DL models process only a small fraction of total traffic in cases, where getting GPU resources might be expensive"
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Phase 3: Real-Time Testing L769 — "Deep learning models are expected to introduce additional latency of 200–500ms per batch... placing the full pipeline near the boundary of the latency target. If this target is not met, the tiered filtering architecture... is expected to reduce the fraction of flows reaching the DL layer"
