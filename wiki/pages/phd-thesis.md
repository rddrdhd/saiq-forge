---
title: "PhD Thesis: Classification and identification of cyber threats using AI and quantum algorithms"
category: Sources
summary: The dissertation proposing SAIQ-Forge — a modular framework fusing four traffic feature modalities and five detector classes for real-time network anomaly detection, with an exploratory quantum component on VLQ.
tags: [thesis, source, network-anomaly-detection, quantum-ml, hpc]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# PhD Thesis: Classification and identification of cyber threats using AI and quantum algorithms

**Source:** raw/phd-thesis-body.tex (copied from `a0_THESIS/Body.tex` in the sibling private thesis submodule)
**Date ingested:** 2026-09-20
**Type:** thesis draft (working document, phases in progress)

## Summary

The thesis argues that existing network anomaly detection systems fail
along three axes at once: they read traffic through a single
representational lens (packet-level, flow-level, or structural, but rarely
combined), they are evaluated offline with no latency accounting, and they
rely on benchmark datasets whose labels don't reflect the ambiguity of
real captures.[^1] Its response is SAIQ-Forge, a framework that treats
feature extraction, detection, and evaluation as independently replaceable
modules so that four traffic feature modalities and five detector method
families can be combined and ablated within one real-time-capable
pipeline, deployed and benchmarked on LUMI and Karolina.[^2]

The empirical plan is organized as six sequential phases (0 through 5),
each with an explicit success criterion, moving from exploratory data
analysis through baseline models, an ablation study, HPC real-time
benchmarking, an exploratory quantum comparison, and a final
cost-effectiveness synthesis.[^3] As of ingestion, Phase 0 is complete,
Phase 1 is underway (a config-driven autoencoder pipeline is running on
LUMI, and a proof-of-concept LUMI→VLQ quantum execution path has been
verified end-to-end), and a small preliminary VQC-vs-MLP pilot has already
been run — deliberately reduced in scale from the full Phase 4 protocol,
and explicitly flagged by the thesis itself as too easy a task to be
informative about a quantum effect.[^4]

The quantum component's role in the thesis has shifted since the original
proposal: VLQ hardware access, initially scoped as an opportunistic
extension contingent on availability, arrived earlier than expected, and
the practical work of connecting to it (Slurm job orchestration, a
lightweight venv rather than the reference conda/Jupyter workflow, LEXIS
token lifecycle management) has become a genuine part of the thesis's
contribution rather than a footnote.[^5]

## Key Takeaways

- The framework's central design bet is **modular composability**: every
  feature extractor and detector exposes a uniform interface so that
  ablation (RQ2) and cross-method comparison (RQ3) become config variants
  instead of separate code paths.[^6]
- The **quantum component is explicitly scoped as exploratory**, not a
  production deliverable — its contribution is a methodologically matched
  comparison protocol (effective-dimension and expressibility matching,
  not raw parameter count) that the thesis argues is largely absent from
  prior QML-for-cybersecurity work.[^7]
- **Label scarcity for real-world captures is treated as a first-class
  experimental variable**, not an assumption to work around — a
  three-stage labeling strategy (heuristic screening, semi-supervised
  propagation under a strict temporal holdout, red-team validation)
  produces progressively higher-confidence labels, and results at each
  stage are reported separately.[^8]
- The **preliminary pilot's own numbers argue against over-interpreting
  it**: all three conditions (noiseless VQC, noisy VQC, matched MLP)
  scored above 0.95 on every metric on a 4-feature subsample, which the
  thesis reads as evidence the task was too linearly separable to say
  anything about a quantum effect — not as an early positive result.[^9]
- Three articles are planned around this thesis, of which the first
  (feasibility: framework design + first LUMI/VLQ instantiation) is
  drafted; the other two (a genuine classical-vs-quantum ablation on
  harder feature subsets, and a full real-time multi-modality throughput
  study) are not yet started.[^10]

## Entities & Concepts

- [[research-questions](pages/research-questions.md)] — the five RQs this thesis is structured to answer
- [[experimental-phases](pages/experimental-phases.md)] — the six-phase empirical plan
- [[feature-modalities](pages/feature-modalities.md)] — temporal, topological, geographical, behavioral
- [[detector-classes](pages/detector-classes.md)] — statistical, classical ML, deep learning, graph-based, quantum
- [[datasets](pages/datasets.md)] — real-world captures A/B/C and benchmarks CICIDS2017/UNSW-NB15
- [[anomaly-taxonomy](pages/anomaly-taxonomy.md)] — DoS/DDoS, Probe, R2L, U2R and their per-modality signatures
- [[saiq-forge-framework](pages/saiq-forge-framework.md)] — the framework this thesis proposes and implements
- [[config-driven-architecture](pages/config-driven-architecture.md)] — the central implementation decision
- [[sliding-window-overlap-strategy](pages/sliding-window-overlap-strategy.md)]
- [[three-stage-ground-truth-labeling](pages/three-stage-ground-truth-labeling.md)]
- [[tiered-statistical-then-dl-filtering](pages/tiered-statistical-then-dl-filtering.md)]
- [[quantum-classical-matching-protocol](pages/quantum-classical-matching-protocol.md)]

## Relation to Other Wiki Pages

This is the founding source of the wiki — all Concept and Decision pages
listed above are derived from this document and cite it directly. Future
ingests (cited SOTA papers, LUMI/IT4I operational docs, and eventually the
codebase itself as it's written on the `rewrite` branch) should link back
here and to the specific concept/decision pages rather than restating
thesis content.

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Introduction [synthesis] L2-13 — the three tensions (single-modality limitation, real-time/latency gap, benchmark-vs-real-world label validity) are laid out across the introduction's opening paragraphs
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Introduction L13 — "The framework integrates four distinct but interconnected feature aspects... within a unified processing pipeline that supports multiple detection methods and is explicitly optimized for HPC-scale deployment"
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Experimental Plan [synthesis] L436-444 — six phases, each mapped in Table phase_outputs to deliverables/metrics/RQs, Phase 0 marked complete
[^4]: [[phd-thesis](pages/phd-thesis.md)] §Preliminary Pilot (Reduced Scale) [synthesis] L695-700 — pilot description, results, and the thesis's own reading of them as inconclusive for a quantum effect
[^5]: [[phd-thesis](pages/phd-thesis.md)] §Implementation and Orchestration Architecture [synthesis] L414-430 — the shift from "opportunistic extension" framing to active orchestration engineering (Slurm, venv, LEXIS token handling)
[^6]: [[phd-thesis](pages/phd-thesis.md)] §Methodology L239 — "The overarching design principle is modular composability: each component exposes a well-defined interface so that feature extractors, detection models, and processing backends can be replaced or extended independently"
[^7]: [[phd-thesis](pages/phd-thesis.md)] §Quantum-Inspired Component [synthesis] L390-413 — VQC scoped as optional drop-in module, not replacing classical models; matching criteria described L408-409
[^8]: [[phd-thesis](pages/phd-thesis.md)] §Ground Truth Strategy L263-274 — three-stage strategy and the temporal-holdout anti-leakage design
[^9]: [[phd-thesis](pages/phd-thesis.md)] §Preliminary Pilot (Reduced Scale) L700 — "a sign that these four raw traffic-volume features make this particular binary task... close to linearly separable, not evidence of a quantum effect"
[^10]: [[phd-thesis](pages/phd-thesis.md)] §Publication Plan L862-881 — three publication directions listed, matching Papers A/B/C
