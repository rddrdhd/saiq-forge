---
title: "Decision: Config-Driven Model Architecture"
category: Decisions
summary: Detection models and feature extractors are instantiated from declarative config rather than hard-coded, so ablation and cross-method comparison become config variants instead of separate code paths.
tags: [decision, architecture, config-driven]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# Decision: Config-Driven Model Architecture

## Description

**Decision.** A single configuration file specifies which feature
modalities are active, which model class to use (statistical / classical
ML / autoencoder / graph-based / quantum), its hyperparameters, and the
target execution backend — models are instantiated from that declaration,
not from hard-coded per-experiment scripts.[^1]

**Why.** This is what makes
[[research-questions](pages/research-questions.md)] RQ2's ablation
configurations and RQ3's model-tier comparisons expressible as
configuration variants of one pipeline, rather than N separate
implementations that would need to be kept in sync by hand and would
undermine the "fair cross-method comparison" the thesis claims as a
contribution.[^2] It's also explicitly framed as the thing that makes the
[[saiq-forge-framework](pages/saiq-forge-framework.md)]'s modular
composability principle *executable* rather than purely conceptual.[^3]

**Where it's already load-bearing.** The classical autoencoder MVP
deployed on LUMI and the quantum-access module (job submission,
authentication, feature encoding, circuit execution) both already use this
same configuration mechanism for batch size, windowing parameters, and GPU
allocation — the thesis treats this as validation that the pattern
generalizes across very different backends (classical GPU training vs.
quantum job orchestration), not just a plan.[^4]

**Consequence for the rewrite.** Because both prior implementations
(`danger`/`master`) already validated this pattern works end-to-end, the
`rewrite` branch's redesign should keep the config-driven contract even
while restructuring everything else — this is one of the few things from
the prior implementation worth deliberately carrying forward rather than
reconsidering from scratch.

## Appearances in Sources

- [[phd-thesis](pages/phd-thesis.md)] — §Implementation and Orchestration Architecture, the thesis's own description of "the strength of the framework"

## Related Concepts

- [[saiq-forge-framework](pages/saiq-forge-framework.md)] — the framework this decision is the load-bearing architectural choice for
- [[research-questions](pages/research-questions.md)] — RQ2 and RQ3 specifically, which this decision exists to make answerable
- [[experimental-phases](pages/experimental-phases.md)] — Phase 2's ablation matrix and Phase 5's configuration-space sweep both assume this

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Implementation and Orchestration Architecture L420 — "A single configuration specifies the feature modalities to include, the model class... its hyperparameters, and the target execution backend"
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Implementation and Orchestration Architecture L420 — "This allows the ablation configurations required by RQ2 and the model-tier comparisons required by RQ3 to be expressed as configuration variants rather than separate code paths"
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Implementation and Orchestration Architecture L418 — "structured to make the modularity described in Figure... directly executable rather than purely conceptual"
[^4]: [[phd-thesis](pages/phd-thesis.md)] §HPC-scalable autoencoder pipeline L426 — "a scalable autoencoder-based detector whose training and inference batch size, windowing parameters, and GPU allocation are all controlled through the same configuration mechanism as the quantum module"
