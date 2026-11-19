# Scenario 2 - Dynamic Gamified FL - Flower vs Unity (10 paired runs, fixed roster)

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

### Implications for Scenario 2

In Scenario 2 `decide_participation()` is called and the reward is personalised by round, engagement, connectivity and history (see thesis, Section 3.8.4). The attributes affect participation through the same base score as in Scenario 1, but disadvantaged clients (low engagement, weak connectivity, no participation in the previous round) receive extra reward bonuses, which is expected to partly compensate for their lower participation in Scenario 1.

## Aggregate
- Pairs compared: 10
- Flower final accuracy: mean=0.8228, std=0.0199
- Unity final accuracy: mean=0.8352, std=0.0250
- Accuracy diff |Flower-Unity|: mean=0.0227, std=0.0154, min=0.0045, max=0.0545

## Per-Pair Detail

| Pair | Flower Acc | Unity Acc | Diff | Flower Selected | Unity Selected | Flower Samples | Unity Samples |
|---|---|---|---|---|---|---|---|
| 1 | 0.8370 | 0.8608 | 0.0238 | 379 | 371 | 39220 | 38386 |
| 2 | 0.8288 | 0.8021 | 0.0267 | 381 | 384 | 39615 | 40067 |
| 3 | 0.8248 | 0.8394 | 0.0146 | 381 | 370 | 39240 | 38860 |
| 4 | 0.8416 | 0.8168 | 0.0248 | 369 | 385 | 37441 | 40322 |
| 5 | 0.8267 | 0.8720 | 0.0452 | 382 | 373 | 39489 | 38215 |
| 6 | 0.7952 | 0.8496 | 0.0545 | 358 | 364 | 37375 | 37538 |
| 7 | 0.7827 | 0.7965 | 0.0138 | 375 | 368 | 39513 | 38118 |
| 8 | 0.8536 | 0.8647 | 0.0111 | 377 | 386 | 38973 | 40534 |
| 9 | 0.8179 | 0.8258 | 0.0079 | 377 | 380 | 38697 | 39978 |
| 10 | 0.8195 | 0.8240 | 0.0045 | 367 | 384 | 38370 | 40189 |

## Files
- Pair 1: `outputs\Flower\dynamic\flower_comparison_summary_dynamic_run01_seed101.json` <-> `outputs\Unity\dynamic\unity_comparison_summary_dynamic_20260808_152112.json`
- Pair 2: `outputs\Flower\dynamic\flower_comparison_summary_dynamic_run02_seed102.json` <-> `outputs\Unity\dynamic\unity_comparison_summary_dynamic_20260808_152124.json`
- Pair 3: `outputs\Flower\dynamic\flower_comparison_summary_dynamic_run03_seed103.json` <-> `outputs\Unity\dynamic\unity_comparison_summary_dynamic_20260808_152136.json`
- Pair 4: `outputs\Flower\dynamic\flower_comparison_summary_dynamic_run04_seed104.json` <-> `outputs\Unity\dynamic\unity_comparison_summary_dynamic_20260808_152147.json`
- Pair 5: `outputs\Flower\dynamic\flower_comparison_summary_dynamic_run05_seed105.json` <-> `outputs\Unity\dynamic\unity_comparison_summary_dynamic_20260808_152157.json`
- Pair 6: `outputs\Flower\dynamic\flower_comparison_summary_dynamic_run06_seed106.json` <-> `outputs\Unity\dynamic\unity_comparison_summary_dynamic_20260808_152208.json`
- Pair 7: `outputs\Flower\dynamic\flower_comparison_summary_dynamic_run07_seed107.json` <-> `outputs\Unity\dynamic\unity_comparison_summary_dynamic_20260808_152218.json`
- Pair 8: `outputs\Flower\dynamic\flower_comparison_summary_dynamic_run08_seed108.json` <-> `outputs\Unity\dynamic\unity_comparison_summary_dynamic_20260808_152238.json`
- Pair 9: `outputs\Flower\dynamic\flower_comparison_summary_dynamic_run09_seed109.json` <-> `outputs\Unity\dynamic\unity_comparison_summary_dynamic_20260808_152254.json`
- Pair 10: `outputs\Flower\dynamic\flower_comparison_summary_dynamic_run10_seed110.json` <-> `outputs\Unity\dynamic\unity_comparison_summary_dynamic_20260808_152306.json`
