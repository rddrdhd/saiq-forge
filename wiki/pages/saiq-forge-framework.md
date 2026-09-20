---
title: SAIQ-Forge (Framework Overview)
category: Concepts
summary: The modular, config-driven real-time network anomaly detection framework this thesis proposes and this repository implements.
tags: [concept, framework-overview, hub]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# SAIQ-Forge (Framework Overview)

## Description

SAIQ-Forge is the thesis's central artifact: a real-time anomaly detection
framework that fuses [[feature-modalities](pages/feature-modalities.md)]
(temporal, topological, geographical, behavioral) with
[[detector-classes](pages/detector-classes.md)] (statistical, classical
ML, deep learning, graph-based, quantum) inside one streaming pipeline,
optimized for HPC deployment.[^1] The framework's defining architectural
commitment is **modular composability**: every feature extractor and
every detector exposes a well-defined interface so pieces can be replaced
or extended independently, which is what turns
[[research-questions](pages/research-questions.md)] RQ2 (does fusion help)
and RQ3 (which combination is cost-effective) from bespoke experiments
into config variants of the same pipeline.[^2]

The name and public repository (`github.com/rddrdhd/saiq-forge`) are cited
directly in the thesis text — this wiki lives inside that same repository,
on its `rewrite` branch, documenting the framework as it's rebuilt from
scratch rather than the prior `danger`/`master` implementation.[^3]

Concretely, the framework is what makes each
[[experimental-phases](pages/experimental-phases.md)] phase executable:
Phase 1's classical baselines, Phase 2's ablation matrix, Phase 3's HPC
scaling sweep, and Phase 4's quantum comparison are all meant to be
expressible as configuration, not separate codebases. The
**config-driven model architecture** is called out in the thesis as the
implementation's central strength.[^4] See
[[config-driven-architecture](pages/config-driven-architecture.md)] for
the design rationale in full.

## Appearances in Sources

- [[phd-thesis](pages/phd-thesis.md)] — introduced §Introduction L13, elaborated as the implementation's architecture in §Implementation and Orchestration Architecture

## Related Concepts

- [[config-driven-architecture](pages/config-driven-architecture.md)] — the specific decision this page's "modular composability" claim cashes out to in code
- [[feature-modalities](pages/feature-modalities.md)] and [[detector-classes](pages/detector-classes.md)] — the two axes the framework combines
- [[research-questions](pages/research-questions.md)] and [[experimental-phases](pages/experimental-phases.md)] — what the framework exists to make measurable

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Introduction L13 — "a modular, multi-layer framework for real-time anomaly detection in network traffic. The framework integrates four distinct but interconnected feature aspects... within a unified processing pipeline that supports multiple detection methods and is explicitly optimized for HPC-scale deployment"
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Methodology L239 — modular composability principle, enabling RQ2/RQ3's ablation and cross-method comparison
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Scientific Contribution L69 — "A public, working implementation of this framework is released as SAIQ-Forge (github.com/rddrdhd/saiq-forge)"
[^4]: [[phd-thesis](pages/phd-thesis.md)] §Implementation and Orchestration Architecture L420 — "the framework lies in its config-driven model architecture. Detection models are instantiated from declarative configuration files rather than hard-coded architectures"
