# Scenario 0 - Baseline FL - Flower vs Unity (10 paired runs, fixed roster)

## 0. Client Roster Profile

Fixed roster: 10 clients, 1042 samples in total (mean 104.2 per client).

### Attribute Distribution

| Attribute | Min | Max | Mean | Std | Coefficient of Variation (CV) |
|---|---|---|---|---|---|
| Engagement | 0.59 | 0.78 | 0.657 | 0.050 | 0.076 |
| Battery Level | 60 | 91 | 77.100 | 11.631 | 0.151 |
| CPU Power | 1.5 | 3.6 | 2.530 | 0.766 | 0.303 |
| Data Quality | 0.51 | 0.99 | 0.736 | 0.170 | 0.231 |
| Storage (GB) | 0.15 | 0.59 | 0.352 | 0.166 | 0.470 |
| Local Samples | 51 | 191 | 104.200 | 40.524 | 0.389 |
| Local Epochs | 1 | 4 | 2.800 | 1.077 | 0.385 |

**Most varied attribute:** by CV (std/mean), clients differ most in **Storage (GB)** (CV=0.470). The most homogeneous attribute is **Engagement** (CV=0.076): engagement values lie in a fairly narrow band (0.59-0.78), so the roster has no extremely unmotivated or extremely motivated client.

### Connectivity Distribution

- strong: 3 clients
- medium: 4 clients
- weak: 3 clients

### Data (Digit) Coverage

- Digits covered by the roster: [0, 1, 2, 3, 4, 6, 7]
- **Digits with no samples: [5, 8, 9]**. No client in this roster has a single sample of digits [5, 8, 9] in its local data (a random outcome of the Dirichlet/non-IID split). Whatever the scenario (0, 1 or 2), the global model is trained without ever seeing these digits. The current accuracy simulation uses an aggregate formula rather than per-digit accuracy, so the numbers are not affected, but in a real classification experiment this would be a serious coverage gap.

### Implications for Scenario 0

In Scenario 0 `decide_participation()` is never called (see thesis, Section 3.8.2), so of the attributes above only **connectivity** and **battery_level** have a real effect on participation, through the server-side eligibility filter (weak connectivity and low battery raise the risk of being filtered out). **Engagement, cpu_power, data_quality and storage_capacity_gb do not affect the participation decision in this scenario.** Even though the roster varies widely in these attributes (for example data_quality: 0.51-0.99 and local_samples: 51-191), who is selected is independent of them and follows a plain random draw with `selection_rate=0.6`. Comparing this roster with Scenarios 1 and 2 shows whether engagement and data_quality start to affect participation.

## Aggregate
- Pairs compared: 10
- Flower final accuracy: mean=0.8239, std=0.0164
- Unity final accuracy: mean=0.8238, std=0.0142
- Accuracy diff |Flower-Unity|: mean=0.0123, std=0.0156, min=0.0000, max=0.0504

## Per-Pair Detail

| Pair | Flower Acc | Unity Acc | Diff | Flower Selected | Unity Selected | Flower Samples | Unity Samples |
|---|---|---|---|---|---|---|---|
| 1 | 0.8402 | 0.8318 | 0.0083 | 400 | 395 | 41647 | 41068 |
| 2 | 0.8362 | 0.8078 | 0.0284 | 400 | 392 | 41593 | 40499 |
| 3 | 0.7934 | 0.8439 | 0.0504 | 399 | 395 | 41489 | 41128 |
| 4 | 0.8253 | 0.8271 | 0.0018 | 401 | 396 | 41632 | 41197 |
| 5 | 0.8261 | 0.8292 | 0.0031 | 399 | 392 | 41360 | 40748 |
| 6 | 0.8298 | 0.8083 | 0.0215 | 399 | 394 | 41449 | 40950 |
| 7 | 0.8263 | 0.8228 | 0.0035 | 402 | 395 | 41776 | 41080 |
| 8 | 0.7917 | 0.7965 | 0.0048 | 401 | 391 | 41472 | 40652 |
| 9 | 0.8368 | 0.8377 | 0.0009 | 395 | 391 | 41071 | 40746 |
| 10 | 0.8329 | 0.8329 | 0.0000 | 396 | 393 | 41274 | 40869 |

## Files
- Pair 1: `outputs\Flower\standard\flower_comparison_summary_standard_run01_seed101.json` <-> `outputs\Unity\standard\unity_comparison_summary_standard_20260807_113634.json`
- Pair 2: `outputs\Flower\standard\flower_comparison_summary_standard_run02_seed102.json` <-> `outputs\Unity\standard\unity_comparison_summary_standard_20260807_113703.json`
- Pair 3: `outputs\Flower\standard\flower_comparison_summary_standard_run03_seed103.json` <-> `outputs\Unity\standard\unity_comparison_summary_standard_20260807_113714.json`
- Pair 4: `outputs\Flower\standard\flower_comparison_summary_standard_run04_seed104.json` <-> `outputs\Unity\standard\unity_comparison_summary_standard_20260807_113725.json`
- Pair 5: `outputs\Flower\standard\flower_comparison_summary_standard_run05_seed105.json` <-> `outputs\Unity\standard\unity_comparison_summary_standard_20260807_113738.json`
- Pair 6: `outputs\Flower\standard\flower_comparison_summary_standard_run06_seed106.json` <-> `outputs\Unity\standard\unity_comparison_summary_standard_20260807_113749.json`
- Pair 7: `outputs\Flower\standard\flower_comparison_summary_standard_run07_seed107.json` <-> `outputs\Unity\standard\unity_comparison_summary_standard_20260807_113800.json`
- Pair 8: `outputs\Flower\standard\flower_comparison_summary_standard_run08_seed108.json` <-> `outputs\Unity\standard\unity_comparison_summary_standard_20260807_113814.json`
- Pair 9: `outputs\Flower\standard\flower_comparison_summary_standard_run09_seed109.json` <-> `outputs\Unity\standard\unity_comparison_summary_standard_20260807_113826.json`
- Pair 10: `outputs\Flower\standard\flower_comparison_summary_standard_run10_seed110.json` <-> `outputs\Unity\standard\unity_comparison_summary_standard_20260807_113839.json`
