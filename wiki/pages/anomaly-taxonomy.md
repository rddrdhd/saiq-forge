---
title: Network Anomaly Taxonomy (DoS/DDoS, Probe, R2L, U2R)
category: Concepts
summary: The four standard intrusion categories the thesis adopts, each with a distinct signature across the four feature modalities.
tags: [concept, vocabulary, anomaly-taxonomy]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# Network Anomaly Taxonomy (DoS/DDoS, Probe, R2L, U2R)

## Description

The thesis follows the KDD Cup 99 / CICIDS classification scheme, which
groups intrusions into four categories, each legible through a different
mix of the four [[feature-modalities](pages/feature-modalities.md)].[^1]

**Denial-of-Service / Distributed DoS.** Resource exhaustion via flooding.
Temporal: sudden sustained volume spikes. Topological: many flows
converge on one destination (many-to-one star). Behavioral: abnormal
packet rates, incomplete TCP handshakes. DDoS adds geographic dispersion
(botnet nodes). Volume-based detectors catch high-rate floods easily;
low-rate/application-layer variants are hard to distinguish from flash
crowds.[^2]

**Probe / Reconnaissance.** Systematic scanning for vulnerabilities.
Topological signature is the clearest: one source, brief connections to
many destinations/ports (one-to-many star, thin edges). May be
rate-limited temporally to evade thresholds. Sequential and graph-based
methods are the most effective detection approach here specifically
because the anomaly lives in connection-attempt structure, not any single
flow.[^3]

**Remote-to-Local (R2L).** External actor gaining unauthorized local
access (credential brute-forcing, protocol exploitation, injection).
Network-observable signals are subtle and resemble legitimate user error —
repeated failed logins, unusual service requests. Behavioral aggregates
(login failure rates, port sequences) plus semi-supervised models on
normal user profiles are the most effective approach.[^4]

**User-to-Root (U2R).** Local privilege escalation. Nearly indistinguishable
from normal traffic at the network layer — requires host-based telemetry
(syscall traces, file integrity) that a network-only framework doesn't
have. Consistently the highest false-negative category in the literature,
and is **explicitly out of scope** for this thesis's network-only
framework.[^5]

## Appearances in Sources

- [[phd-thesis](pages/phd-thesis.md)] — §Taxonomy of Network Anomalies; also underlies Phase 2's red-team injection design (SYN flood=DoS, port scan=Probe, SSH brute-force=R2L) via [[datasets](pages/datasets.md)]'s Dataset D

## Related Concepts

- [[feature-modalities](pages/feature-modalities.md)] — the per-category signature descriptions above are literally "which modality lights up for this attack type"
- [[detector-classes](pages/detector-classes.md)] — Probe/DoS favor graph-based and statistical detectors respectively; R2L favors behavioral+semi-supervised; U2R is out of scope for all of them here
- [[datasets](pages/datasets.md)] — Dataset D's four injected attack types map directly onto DoS/Probe/R2L (U2R excluded, consistent with scope)

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Taxonomy of Network Anomalies L134-138 — "organize network intrusions into four categories. Each category exhibits distinct signatures across the four feature modalities"
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Denial-of-Service (DoS) and Distributed DoS (DDoS) [synthesis] L148-149
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Probe and Reconnaissance [synthesis] L151-152
[^4]: [[phd-thesis](pages/phd-thesis.md)] §Remote-to-Local (R2L) [synthesis] L154-155
[^5]: [[phd-thesis](pages/phd-thesis.md)] §User-to-Root (U2R) L157-158 — "accordingly treated as out of scope for the network-only framework proposed in this thesis"
