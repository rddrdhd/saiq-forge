---
title: Feature Modalities (Temporal, Topological, Geographical, Behavioral)
category: Concepts
summary: The four complementary representational axes SAIQ-Forge extracts from traffic, each independently swappable rather than a fixed preprocessing step.
tags: [concept, vocabulary, feature-engineering]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# Feature Modalities (Temporal, Topological, Geographical, Behavioral)

## Description

Network traffic is characterized along four axes, chosen because each
captures attack signatures invisible to the others.[^1] The framework's
central empirical bet ([[research-questions](pages/research-questions.md)]
RQ2) is that fusing all four beats any single one.

**Temporal (T)** — inter-arrival times, per-second byte/packet counts,
burst duration, periodic cycles. Detects deviations from expected rhythm:
off-hours transfers, sudden bursts, dropped keep-alives. Lineage from PCA
subspace decomposition of traffic matrices through to multi-scale
self-attention and Transformer-based sequence models.[^2]

**Topological (TO)** — traffic as a directed, weighted graph (IPs as
nodes, flows as edges). Detects structural signatures: port-scan star
topologies, IP sweeps, botnet C2 coordination — patterns not visible in
per-flow statistics alone. Static and dynamic (EvolveGCN-style) GNN
methods are the dominant current paradigm.[^3]

**Geographical (G)** — IP-to-location via geolocation DBs (e.g. MaxMind
GeoLite2) and ASN/routing metadata. Least-studied of the four, but
complementary: coordinated attacks cluster by AS/region, and a login from
a new country is only anomalous *relative to a host's own history* — this
modality is most informative combined with behavioral baselines, not
alone.[^4]

**Behavioral (B)** — per-host/host-pair aggregates over sliding windows:
packet counts, byte volumes, flow durations, flag ratios, inter-flow
intervals. The strongest single-modality signal in prior literature —
behavioral aggregates on KDD Cup 99 and CICIDS2017 both show large
accuracy/false-positive gains over raw packet headers, and this modality
is specifically what catches R2L/U2R attacks that are weak at the packet
level.[^5]

The thesis's own hypothesis for Phase 2, based on this same literature, is
that isolated modality strength decreases behavioral > temporal >
topological > geographical — a prediction the ablation study is designed
to test, not assume.[^6]

## Appearances in Sources

- [[phd-thesis](pages/phd-thesis.md)] — defined in §Anomaly Feature Modalities; re-appears as the axis of the [[experimental-phases](pages/experimental-phases.md)] Phase 2 ablation table and as the modality-signature columns of [[anomaly-taxonomy](pages/anomaly-taxonomy.md)]

## Related Concepts

- [[anomaly-taxonomy](pages/anomaly-taxonomy.md)] — each attack category (DoS/DDoS, Probe, R2L, U2R) has a distinct signature across these four modalities
- [[detector-classes](pages/detector-classes.md)] — specific detector families pair naturally with specific modalities (graph-based ↔ topological, sequence models ↔ temporal/behavioral)
- [[research-questions](pages/research-questions.md)] — RQ2 is precisely "does fusing all four beat any one"
- [[saiq-forge-framework](pages/saiq-forge-framework.md)] — each modality must be an independently swappable extractor module, not a fixed preprocessing stage

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Anomaly Feature Modalities L113 — "Each modality captures a distinct aspect of network behavior, and their combination enables the detection of attack patterns that are invisible to any single perspective"
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Temporal Features [synthesis] L115-117 — definition, PCA-to-Transformer lineage
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Topological Features [synthesis] L119-123 — graph representation, static/dynamic GNN methods
[^4]: [[phd-thesis](pages/phd-thesis.md)] §Geographical Features [synthesis] L125-127 — geolocation/ASN basis, complementarity with behavioral baselines
[^5]: [[phd-thesis](pages/phd-thesis.md)] §Behavioral Features [synthesis] L129-131 — definition, KDD/CICIDS2017 evidence, R2L/U2R relevance
[^6]: [[phd-thesis](pages/phd-thesis.md)] §Phase 2: Advanced Models and Ablation Study L759 — "behavioral > temporal > topological > geographical" hypothesized ordering
