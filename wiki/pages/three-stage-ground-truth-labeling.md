---
title: "Decision: Three-Stage Ground-Truth Labeling with Temporal Holdout"
category: Decisions
summary: Real-world captures get labeled through heuristic screening, then temporally-partitioned semi-supervised propagation, then red-team validation — label uncertainty is reported as a variable, not hidden.
tags: [decision, labeling, ground-truth, evaluation-methodology]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# Decision: Three-Stage Ground-Truth Labeling with Temporal Holdout

## Description

**Decision.** Real-world captures (datasets A/B/C) have no verified
labels, so the thesis builds them up in three stages of increasing
confidence, and — critically — reports results *separately per stage*
rather than treating the final label set as ground truth throughout.[^1]

1. **Heuristic screening** (Phase 0): IQR/Z-score/scanning rules produce
   noisy weak-label candidates — explicitly not treated as truth.[^2]
2. **Semi-supervised propagation** (Phase 1): candidates seed a label
   propagation pass over the flow graph, extending labels to structurally
   or feature-similar flows.[^3]
3. **Red-team validation** (Phase 2): a manual-review subset plus
   Scapy-injected synthetic attacks (labeled by construction) produce a
   genuinely verified evaluation set for at least a sample.[^4]

**The anti-leakage design is the part worth being careful about in code.**
Label propagation runs *only* on the first 70% of each capture by
timestamp; the remaining 30% is held out and receives no propagated
labels at all — evaluation flows are scored purely by trained models, with
zero access to propagation outputs. The propagation graph itself is built
solely from training-partition flows, so no structural information from
the held-out partition can leak into seed assignment or neighborhood
scores.[^5] This is a stricter requirement than a typical train/test split:
it's not just "don't train on test rows," it's "don't let the *labeling
process itself* see the test partition's structure."

**Why.** Benchmark datasets have labels but not real-world fidelity; real
captures have fidelity but no labels. Rather than picking one horn, the
thesis treats the resulting label uncertainty as an explicit experimental
variable — results on heuristic, semi-supervised, and verified labels are
reported side by side, so the framework's measured performance is never
silently contingent on an unstated labeling assumption.[^6]

## Appearances in Sources

- [[phd-thesis](pages/phd-thesis.md)] — §Ground Truth Strategy (the three stages and the anti-leakage protocol), §Label Scarcity and Noise (why this matters, confidence-interval reporting)

## Related Concepts

- [[experimental-phases](pages/experimental-phases.md)] — Stage 1↔Phase 0, Stage 2↔Phase 1, Stage 3↔Phase 2's red-team validation
- [[datasets](pages/datasets.md)] — this is specifically about datasets A/B/C (and the synthetic Dataset D), not CICIDS2017/UNSW-NB15 which already have labels

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Ground Truth Strategy L263-265 — "A central methodological challenge for real-world datasets A–C is the absence of verified ground-truth labels. The following three-stage labeling strategy is adopted"
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Ground Truth Strategy L267 — "Stage 1 (Heuristic screening, Phase 0)... treated as noisy weak labels, not ground truth"
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Ground Truth Strategy L269-270 — Stage 2 semi-supervised propagation description
[^4]: [[phd-thesis](pages/phd-thesis.md)] §Ground Truth Strategy L272 — Stage 3 red-team review and synthetic injection
[^5]: [[phd-thesis](pages/phd-thesis.md)] §Ground Truth Strategy [synthesis] L270 — the 70/30 temporal holdout, propagation-graph-from-training-only design
[^6]: [[phd-thesis](pages/phd-thesis.md)] §Ground Truth Strategy L274 — "The uncertainty introduced at each stage is treated as an explicit experimental variable: detection results on heuristically labeled data, semi-supervised data, and verified data will be reported separately"
