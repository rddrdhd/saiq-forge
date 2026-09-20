---
title: Overview
tags: [overview, synthesis]
sources: [phd-thesis]
updated: 2026-09-20
---

# SAIQ-Forge — Overview

> Evolving synthesis of everything in the wiki. Updated by wiki-ingest when sources shift the understanding.

## Current Understanding

The wiki's vocabulary and design rationale are seeded from the PhD thesis
([[phd-thesis](pages/phd-thesis.md)]) that proposes and specifies
SAIQ-Forge: a config-driven framework fusing four
[[feature-modalities](pages/feature-modalities.md)] (temporal, topological,
geographical, behavioral) with five [[detector-classes](pages/detector-classes.md)]
(statistical, classical ML, deep learning, graph-based, quantum/VQC),
evaluated against five [[research-questions](pages/research-questions.md)]
across a six-stage [[experimental-phases](pages/experimental-phases.md)]
plan (0 complete, 1 in progress, 2–5 not started).

Five [[Decisions](pages/config-driven-architecture.md)]-category pages
capture the design rationale most load-bearing for the codebase being
(re)written on this repo's `rewrite` branch: the config-driven
architecture itself, the sliding-window/overlap strategy (with a concrete
lesson already learned in Phase 0 about normalizing topological features
by window length), the three-stage ground-truth labeling protocol (with
its temporal-holdout anti-leakage design), the tiered
statistical-then-DL filtering pipeline (a cost-effectiveness answer, not
just a performance one), and the quantum-classical matching protocol for
RQ5 (effective-dimension/expressibility, not raw parameter count).

This repo (`saiq-forge`, currently on an intentionally emptied `rewrite`
branch) is where these decisions become code. The prior implementation on
`danger`/`master` is a reference, not yet ingested — the point of the
rewrite is deliberate redesign, not documenting the old structure (see
`../CLAUDE.md`).

**One internal inconsistency was found in the thesis during this ingest
and corrected at the source** (not just noted in the wiki): §Positioning
Against the State of the Art (`a0_THESIS/Body.tex`) described the RQ5
matching protocol as "parameter count," contradicting the more detailed
and specific §Experimental Configuration, which explicitly rejects
parameter-count matching. See
[[quantum-classical-matching-protocol](pages/quantum-classical-matching-protocol.md)]'s
closing note. Four unrelated typos/grammar issues were also fixed
directly in the thesis (an/a, availible/available, fuctionality/
functionality, verfied/verified, LUMU/LUMI, analyzes/analyses).

## Open Questions

- The codebase itself (Modules-category pages) doesn't exist yet — will
  populate as `rewrite` gets real implementation.
- No `Experiments`-category pages yet either — those should appear once a
  phase is actually run (not just planned), separate from this ingest's
  `Concepts`-category phase *definitions*.
- Whether to ingest the `danger` branch's prior implementation at all, or
  treat it purely as ad-hoc reference material outside the wiki (current
  lean: the latter, per `../CLAUDE.md`'s "deliberate redesign" framing).
- A bounded state-of-the-art verification pass (recent quantum-ML-for-IDS
  and multi-modal fusion literature beyond what the thesis already cites)
  hasn't been done yet — flagged as a natural follow-up ingest.

## Key Entities / Concepts

- [[saiq-forge-framework](pages/saiq-forge-framework.md)] — hub/overview concept
- [[research-questions](pages/research-questions.md)], [[experimental-phases](pages/experimental-phases.md)] — the thesis's evaluative structure
- [[feature-modalities](pages/feature-modalities.md)], [[detector-classes](pages/detector-classes.md)], [[anomaly-taxonomy](pages/anomaly-taxonomy.md)], [[datasets](pages/datasets.md)] — the vocabulary of what's being detected, how, and on what data
- [[config-driven-architecture](pages/config-driven-architecture.md)], [[sliding-window-overlap-strategy](pages/sliding-window-overlap-strategy.md)], [[three-stage-ground-truth-labeling](pages/three-stage-ground-truth-labeling.md)], [[tiered-statistical-then-dl-filtering](pages/tiered-statistical-then-dl-filtering.md)], [[quantum-classical-matching-protocol](pages/quantum-classical-matching-protocol.md)] — the design decisions most relevant to implementation
