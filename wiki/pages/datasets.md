---
title: "Datasets: A/B/C and CICIDS2017/UNSW-NB15"
category: Concepts
summary: The three real-world captures (A/B/C) and two public benchmarks (CICIDS2017, UNSW-NB15) used across the thesis's experimental plan.
tags: [concept, vocabulary, datasets]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# Datasets: A/B/C and CICIDS2017/UNSW-NB15

## Description

Three datasets in the plan, of two kinds: two labeled public benchmarks
enabling comparison with prior work, and real-world captures providing
ecological validity that benchmarks structurally can't.[^1]

**Dataset A** — 107 packets, 5-minute window. Phase 0 flagged 91 flows,
90 of them topological; manual review found this was mostly normal
DNS/browsing behavior falsely flagged because the short window makes the
scanning threshold (5 unique destination IPs) oversensitive — a finding
that directly motivated normalizing topological thresholds by window
length in Phase 1.[^2]

**Dataset B** — 134 packets, 17-minute window. Zero flows flagged by any
Phase 0 criterion — a quiet, uniform, low-volume period. Earmarked as the
clean normal-traffic reference for unsupervised model calibration in
Phase 1.[^3]

**Dataset C** — 22,529 packets, ~5-hour window. 16,730 flows flagged
(16,551 topological — again a window-length artifact, expected and not
treated as a problem since it maximizes recall for manual review). The
more robust signals are the 3,558 behavioral and 305 temporal candidates,
including a pronounced byte-volume burst near the capture start and a
one-to-many star topology cluster consistent with exfiltration or C2
activity.[^4]

**CICIDS2017** — the standard public benchmark for learning-based IDS
evaluation; used from Phase 1 onward wherever labeled data is needed
(supervised upper bounds, the Phase 4 quantum pilot). The thesis is
explicit that models trained exclusively on it suffer dataset bias and
limited real-world generalization — this is exactly the gap real-world
datasets A–C exist to expose.[^5]

**UNSW-NB15** — the second public benchmark, used alongside CICIDS2017
in ablation experiments (Phase 2) so a multi-modal fusion result isn't an
artifact of one dataset's quirks.[^6]

A potential **Dataset D** is anticipated in Phase 2: synthetic attack
traffic (SYN flood, port scan, SSH brute-force, exfiltration; via Scapy,
labeled by construction) injected into a clean real capture segment, for
a verified evaluation set red-team review alone can't fully provide.[^7]

## Appearances in Sources

- [[phd-thesis](pages/phd-thesis.md)] — table in §Data Representation and Feature Extraction; A/B/C results detailed in §Phase 0; CICIDS2017/UNSW-NB15 used from §Phase 1 onward

## Related Concepts

- [[experimental-phases](pages/experimental-phases.md)] — Phase 0 uses only A/B/C; benchmarks enter at Phase 1; Dataset D is a Phase 2 red-team construct
- [[three-stage-ground-truth-labeling](pages/three-stage-ground-truth-labeling.md)] — the labeling strategy that makes A/B/C usable despite having no ground truth
- [[anomaly-taxonomy](pages/anomaly-taxonomy.md)] — CICIDS2017/UNSW-NB15 both follow this taxonomy's attack categories

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Datasets L245-246 — "Two are well-established public benchmarks... The third consists of real-world traffic captures... providing ecological validity beyond controlled laboratory conditions"
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Results and Observations (Dataset A) L473-474 — flag counts and the window-length-sensitivity finding
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Results and Observations (Dataset B) L476 — zero flags, earmarked as clean baseline
[^4]: [[phd-thesis](pages/phd-thesis.md)] §Results and Observations (Dataset C) [synthesis] L478-488 — flag counts, the three specific Phase 1 follow-up observations
[^5]: [[phd-thesis](pages/phd-thesis.md)] §Introduction L9 — "models trained exclusively on such data suffer from dataset bias and limited generalization when deployed in operational environments"
[^6]: [[phd-thesis](pages/phd-thesis.md)] §Ablation Design L581-592 — CICIDS2017/UNSW-NB15 both used across the seven ablation configurations
[^7]: [[phd-thesis](pages/phd-thesis.md)] §Red-Team Validation L598-600 — dataset D construction via synthetic injection, four attack types
