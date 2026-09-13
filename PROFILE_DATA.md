# Network Baseline Profile Analysis Guide

This guide provides a step-by-step workflow for interpreting the generated `baseline_profile_xxx.json` artifact with the `jobs/my_03_profile_data.sh` file. By following these checks, you can quickly understand the core characteristics of an unlabelled network capture, identify structural or volumetric anomalies, and uncover potential security threats (like scanning, DDoS, or exfiltration).

---

## Step 1: Identify Volumetric Heavy Hitters (Data Bursts / DDoS)
Network traffic typically follows a heavy-tailed distribution. We evaluate the distance between the robust median ($50^{\text{th}}$ percentile) and the extreme tail ($99^{\text{th}}$ and $99.9^{\text{th}}$ percentiles) under `"numerical_profiles"`.

1. **Check Packet Counts (`SRC PACKETS` & `DST PACKETS`):**
   * If the `median` is low (e.g., `1.0`) but the `max` or `p999` is in the hundreds or thousands, you have an extreme, isolated bulk transfer or a network flood event.
2. **Check Byte Quantiles (`SRC BYTES` & `DST BYTES`):**
   * Compare the `median` directly against the `p99` and `p999`. 
   * If `p95` is close to the median but `p99` suddenly balloons by orders of magnitude, it confirms that less than 1% of your database records are driving the entire network's volume (consistent with your thesis observation of a pronounced byte-volume burst).

---

## Step 2: Spot Reconnaissance & Scanning (Topological Fan-Out)
A single host communicating with a massive number of unique endpoints over a short period is a classic indicator of malicious reconnaissance or aggressive asset discovery.

1. Navigate to the `"structural_limits"` block.
2. Read `"max_unique_dst_ips_per_src"` and `"p95_unique_dst_ips_per_src"`.
3. **Analysis:** * If a single source IP contacts a high number of destination IPs relative to the overall size of the dataset (e.g., 17 unique destinations out of only 107 total flows), that host is creating a **one-to-many star topology**.
   * **Contextualizing Threshold Sensitivity:** If your file timespan is short (under 5 minutes), a high unique destination count often flags normal, sensitive browser operations (DNS lookups, content delivery networks). If the file spans hours, unnormalized high counts indicate systemic horizontal scanning.

---

## Step 3: Detect Data Exfiltration & Channel Asymmetry
Analyzing the directional flow of bytes allows you to distinguish normal consumer web browsing from suspicious outbound staging or data exfiltration.

1. Navigate to `"ratio_profiles" -> "SRC_TO_DST_BYTES_ASYMMETRY"`.
2. **Evaluate the Median:** A median near `0.0` indicates standard download-heavy patterns (the client sends small requests, the server returns large payloads).
3. **Evaluate the Extreme Tail (`p99` / `p999`):** * If the $99^{\text{th}}$ percentile spikes drastically into the thousands (e.g., `23,982.0`), it reveals an elite subset of anomalous flows where a client is uploading massive amounts of data while receiving virtually zero response payloads back. 
   * Target these specific high-asymmetry flows for deep forensic inspection.

---

## Step 4: Catch Malware Tunneling (Application-to-Port Auditing)
Attackers frequently run malicious protocols (like interactive Command-and-Control channels or BitTorrent) over standard open ports like HTTP (80), HTTPS (443), or DNS (53) to slip past firewalls.

1. Navigate to `"categorical_baselines" -> "probabilistic_port_applications"`.
2. Note the strictly established profiles. This section maps a destination port to an application *only* if that pairing has a high conditional probability ($P(\text{Application} \mid \text{Port}) \ge 0.30$) and ignores "UNKNOWN" ambient noise.
3. **How to Flag Incoming Records:**
   * Look up the destination port of any newly inspected flow record against this dictionary.
   * If a record uses `DST PORT: 53` but its identified application is something other than `["DNS"]` (or whatever is explicitly listed in your baseline dictionary), flag that record immediately for **Application Masquerading**.

---

## Quick Reference: Threat Triage Cheat Sheet

| Indicator | JSON Metric Location | What a High Value Means |
| :--- | :--- | :--- |
| **DDoS / Flood Burst** | `numerical_profiles -> * -> max / p999` | Sudden heavy-hitter volumetric spikes far outside normal system standard deviations. |
| **Network Scanning** | `structural_limits -> max_unique_dst_ips_per_src` | A single internal host is systematically probing multiple network addresses. |
| **Data Exfiltration** | `ratio_profiles -> SRC_TO_DST_BYTES_ASYMMETRY -> p99` | Massive outbound data push with negligible download confirmation payloads. |
| **Protocol Tunneling** | `categorical_baselines -> probabilistic_port_applications` | An active application is operating on an unexpected, baseline-violating destination port. |
| **System Uniformity Check**| `global_entropy -> *` | Low entropy values reveal highly predictable, uniform, or heavily automated traffic (perfect for clean baseline model training). |