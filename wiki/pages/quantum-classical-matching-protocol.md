---
title: "Decision: Quantum-Classical Matching by Effective Dimension and Expressibility, Not Parameter Count"
category: Decisions
summary: RQ5's VQC-vs-MLP comparison matches models by effective dimension and circuit expressibility rather than raw parameter count, since parameter count isn't an equivalent capacity measure across paradigms.
tags: [decision, quantum-ml, evaluation-methodology, rq5]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# Decision: Quantum-Classical Matching by Effective Dimension and Expressibility, Not Parameter Count

## Description

**Decision (full Phase 4 protocol).** The classical MLP baseline for the
VQC comparison is matched by two criteria run in parallel, each reported
separately: (1) **effective dimension matching**, via the Fisher
information spectrum, so the MLP's effective capacity approximates the
VQC's at the evaluated circuit depth; and (2) **expressibility matching**,
where MLP width is chosen so its output-distribution KL divergence from a
reference matches the VQC's own expressibility score (KL divergence of
sampled circuit outputs from the Haar-random distribution). Raw parameter
count is recorded only as a secondary descriptor, explicitly *not* the
matching criterion.[^1]

**Why not just match parameter count?** The thesis is explicit that
parameter count "is not an equivalent measure of model capacity across
quantum and classical paradigms" — a VQC and an MLP with the same number
of trainable parameters can have very different effective expressive
power, so a parameter-count-matched comparison risks attributing a
performance gap to "quantum vs. classical" when it's really an artifact of
capacity mismatch. This is presented as a direct methodological fix to a
weakness the thesis identifies in prior QML-for-cybersecurity literature
(inconsistent evaluation protocols, incomparable dataset splits, no
capacity matching at all).[^2]

**The preliminary pilot deliberately did not use this protocol — this is
a known, stated simplification, not an inconsistency.** The reduced-scale
pilot already run matched by raw parameter count (13 vs. 12) instead, on
only 4 features instead of 16, with a single fixed circuit depth instead
of the depth sweep.[^3] Any code implementing "the" quantum comparison
should default to the full effective-dimension/expressibility protocol —
the pilot's parameter-count matching was a stated, temporary shortcut for
a first connectivity proof-of-concept, not the target design.

**Noise handling.** The full protocol uses a depolarizing noise model
calibrated to real IBMQ device error rates; the pilot used an
"illustrative (non-hardware-calibrated)" depolarizing condition instead —
again a stated simplification specific to the pilot, not the target.[^4]

## Appearances in Sources

- [[phd-thesis](pages/phd-thesis.md)] — §Experimental Configuration (Phase 4's full protocol), §Preliminary Pilot (Reduced Scale) (what was actually run first, and how it differs)

## Related Concepts

- [[research-questions](pages/research-questions.md)] — RQ5 is exactly what this matching protocol exists to make answerable without a capacity-mismatch confound
- [[detector-classes](pages/detector-classes.md)] — the quantum (VQC) class specifically
- [[experimental-phases](pages/experimental-phases.md)] — Phase 4, and its three hypotheses H1–H3

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Experimental Configuration L409 — "Rather than matching by raw parameter count, which is not an equivalent measure of model capacity across quantum and classical paradigms, two complementary matching criteria are adopted... Both matched baselines are evaluated in parallel; results are reported for each matching criterion separately"
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Positioning Against the State of the Art L232 — "This thesis addresses this by applying a fixed evaluation protocol and matching quantum and classical models by effective dimension and circuit expressibility rather than raw parameter count" (corrected during this ingest — see note below)
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Preliminary Pilot (Reduced Scale) L698 — "against a classical MLP with a roughly matched parameter count (13 vs. 12) rather than the effective-dimension/expressibility matching of the full protocol"
[^4]: [[phd-thesis](pages/phd-thesis.md)] §Preliminary Pilot (Reduced Scale) L698 — "under a noiseless and an illustrative (non-hardware-calibrated) depolarizing-noise condition"

## Note: internal inconsistency found and corrected during this ingest

§Positioning Against the State of the Art (L232) previously described the
thesis's own methodological fix as "matching quantum and classical models
by parameter count" — directly contradicting §Experimental Configuration
(L409), which explicitly rejects raw-parameter-count matching in favor of
effective-dimension/expressibility matching. L232 read as stale phrasing
left over from an earlier version of the design, not a second, deliberate
decision, since L409 is the more detailed and specific of the two and the
whole point of this page is that parameter-count matching was explicitly
rejected. L232 has been corrected in `a0_THESIS/Body.tex` to match L409 —
see that submodule's `git diff` to review the change.
