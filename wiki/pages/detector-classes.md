---
title: Detector Classes (Statistical, Classical ML, Deep Learning, Graph-Based, Quantum)
category: Concepts
summary: The five detection method families SAIQ-Forge supports, all consuming the same feature representation and emitting a scalar anomaly score in [0,1].
tags: [concept, vocabulary, detection-methods]
sources: [phd-thesis]
created: 2026-09-20
updated: 2026-09-20
---

# Detector Classes (Statistical, Classical ML, Deep Learning, Graph-Based, Quantum)

## Description

Five detection paradigms span the interpretability/expressivity and
latency/accuracy trade-off space. All consume the framework's unified
feature representation and output a scalar anomaly score in [0, 1],
which is what makes cross-method comparison and ensembling
possible.[^1]

**Statistical** — Z-score/IQR thresholding and sliding-window Shannon
entropy monitoring (source/destination IP, port, protocol distributions;
entropy drops indicate scanning, spikes indicate flooding). Lowest
latency, most interpretable, assumes stationarity. Used as the first
filtering layer — see [[tiered-statistical-then-dl-filtering](pages/tiered-statistical-then-dl-filtering.md)].[^2]

**Classical ML** — unsupervised Isolation Forest, One-Class SVM, Local
Outlier Factor as primary baselines (label scarcity is the norm in
operational data); Random Forest/XGBoost as supervised upper bounds where
labels exist. Isolation Forest is favored for streaming settings due to
sub-linear training and incremental-update support. All are sensitive to
distribution drift and need periodic retraining.[^3]

**Deep Learning** — LSTM autoencoder (sequential dependencies in flow
records), TCN autoencoder (cheaper, larger receptive field via dilation),
VAE (probabilistic anomaly score via ELBO, explicit uncertainty
quantification). Trained exclusively on normal traffic, so applicable to
unlabeled real-world captures. High training cost and low interpretability
are the tradeoffs.[^4]

**Graph-Based** — a static GNN graph-autoencoder per window, plus a
Word2Vec-embedded IP-sequence model (destination-contact sequences as
"documents"; low-density embedding regions flag reconnaissance). Expressive
for structurally-encoded attacks (port scanning, botnet C2) but with
non-trivial graph construction/maintenance cost — see
[[experimental-phases](pages/experimental-phases.md)] Phase 3's graph
scalability concern.[^5]

**Quantum (VQC)** — a Variational Quantum Circuit using a data
re-uploading scheme (features re-encoded as rotation angles at every
circuit layer) with parameterized entangling layers, measured via Pauli-Z
expectation values into a classical softmax. Explicitly an optional,
exploratory drop-in module, not a production detector — see
[[quantum-classical-matching-protocol](pages/quantum-classical-matching-protocol.md)]
for how it's compared to classical baselines.[^6]

Default score aggregation across active detectors is **maximum** (favors
recall, conservative); weighted averaging and a learned meta-classifier
are evaluated later, in Phase 5.[^7]

## Appearances in Sources

- [[phd-thesis](pages/phd-thesis.md)] — defined in §Methods for Anomaly Detection (survey) and §Anomaly Detectors (the framework's own implementation choices); evaluated progressively across [[experimental-phases](pages/experimental-phases.md)] Phase 1 (statistical/classical ML) → Phase 2 (deep learning/graph-based/fusion) → Phase 4 (quantum)

## Related Concepts

- [[feature-modalities](pages/feature-modalities.md)] — each detector class consumes some or all of the four modalities as its feature vector
- [[tiered-statistical-then-dl-filtering](pages/tiered-statistical-then-dl-filtering.md)] — how statistical and the more expensive classes are composed in the real-time pipeline, not just evaluated in isolation
- [[quantum-classical-matching-protocol](pages/quantum-classical-matching-protocol.md)] — the evaluation protocol specific to the quantum class
- [[research-questions](pages/research-questions.md)] — RQ3 (cost-effectiveness) and RQ5 (quantum-vs-classical) are both about comparing these classes, not any one in isolation

[^1]: [[phd-thesis](pages/phd-thesis.md)] §Anomaly Detectors L281 — "All modules consume the same unified feature representation... and produce a scalar anomaly score a ∈ [0, 1] per input record, enabling consistent comparison and ensemble combination"
[^2]: [[phd-thesis](pages/phd-thesis.md)] §Statistical Methods / §Statistical Baselines [synthesis] L167-170, L283-285
[^3]: [[phd-thesis](pages/phd-thesis.md)] §Classical Machine Learning [synthesis] L172-174, L287-289
[^4]: [[phd-thesis](pages/phd-thesis.md)] §Deep Learning [synthesis] L176-178, L291-293
[^5]: [[phd-thesis](pages/phd-thesis.md)] §Graph-Based Methods [synthesis] L180-182, L295-297
[^6]: [[phd-thesis](pages/phd-thesis.md)] §Architecture (Quantum-Inspired Component) [synthesis] L396-400 — data re-uploading scheme, entangling layers, Pauli-Z measurement
[^7]: [[phd-thesis](pages/phd-thesis.md)] §Ensemble Combination L299-302 — maximum aggregation default, weighted averaging evaluated in Phase 5
