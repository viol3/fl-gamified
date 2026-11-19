# Scenario 1 - Static Incentive - Flower vs Unity (10 paired runs, fixed roster)

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

### Implications for Scenario 1

In Scenario 1 `decide_participation()` is called (see thesis, Section 3.8.3), so all attributes above enter the participation score directly: `base_score = 0.45*engagement + 0.25*(battery/100) + 0.15*min(cpu_power/4,1) + 0.15*data_quality`. Because the reward is fixed (`static_reward_points`), every client gets the same `reward_bonus`, so differences in participation between clients come **only from the differences within the roster**. In addition, both the server-side eligibility filter (thesis, Section 3.8.1) and the client-side second check (battery<20, disconnection probability: weak=0.35, medium=0.15, strong=0.05) put clients with weak or medium connectivity at a structural disadvantage. Unlike Scenario 0, attributes such as engagement and data_quality are expected to have a measurable effect on participation.

## Aggregate
- Pairs compared: 10
- Flower final accuracy: mean=0.8316, std=0.0091
- Unity final accuracy: mean=0.8279, std=0.0277
- Accuracy diff |Flower-Unity|: mean=0.0236, std=0.0211, min=0.0001, max=0.0623

## Per-Pair Detail

| Pair | Flower Acc | Unity Acc | Diff | Flower Selected | Unity Selected | Flower Samples | Unity Samples |
|---|---|---|---|---|---|---|---|
| 1 | 0.8359 | 0.8277 | 0.0081 | 316 | 331 | 33128 | 34704 |
| 2 | 0.8307 | 0.8405 | 0.0098 | 331 | 329 | 34355 | 34599 |
| 3 | 0.8380 | 0.7881 | 0.0499 | 337 | 323 | 35712 | 34140 |
| 4 | 0.8112 | 0.8113 | 0.0001 | 329 | 329 | 33123 | 34913 |
| 5 | 0.8249 | 0.8470 | 0.0221 | 333 | 330 | 34316 | 34918 |
| 6 | 0.8352 | 0.8414 | 0.0063 | 343 | 326 | 35793 | 34417 |
| 7 | 0.8474 | 0.7851 | 0.0623 | 333 | 328 | 35347 | 34900 |
| 8 | 0.8289 | 0.8796 | 0.0507 | 335 | 325 | 34659 | 33872 |
| 9 | 0.8277 | 0.8114 | 0.0164 | 343 | 332 | 36358 | 34497 |
| 10 | 0.8363 | 0.8466 | 0.0103 | 329 | 332 | 34689 | 34793 |

## Files
- Pair 1: `outputs\Flower\static\flower_comparison_summary_static_run01_seed101.json` <-> `outputs\Unity\static\unity_comparison_summary_static_20260808_110831.json`
- Pair 2: `outputs\Flower\static\flower_comparison_summary_static_run02_seed102.json` <-> `outputs\Unity\static\unity_comparison_summary_static_20260808_110843.json`
- Pair 3: `outputs\Flower\static\flower_comparison_summary_static_run03_seed103.json` <-> `outputs\Unity\static\unity_comparison_summary_static_20260808_110908.json`
- Pair 4: `outputs\Flower\static\flower_comparison_summary_static_run04_seed104.json` <-> `outputs\Unity\static\unity_comparison_summary_static_20260808_110919.json`
- Pair 5: `outputs\Flower\static\flower_comparison_summary_static_run05_seed105.json` <-> `outputs\Unity\static\unity_comparison_summary_static_20260808_110929.json`
- Pair 6: `outputs\Flower\static\flower_comparison_summary_static_run06_seed106.json` <-> `outputs\Unity\static\unity_comparison_summary_static_20260808_110939.json`
- Pair 7: `outputs\Flower\static\flower_comparison_summary_static_run07_seed107.json` <-> `outputs\Unity\static\unity_comparison_summary_static_20260808_110949.json`
- Pair 8: `outputs\Flower\static\flower_comparison_summary_static_run08_seed108.json` <-> `outputs\Unity\static\unity_comparison_summary_static_20260808_110959.json`
- Pair 9: `outputs\Flower\static\flower_comparison_summary_static_run09_seed109.json` <-> `outputs\Unity\static\unity_comparison_summary_static_20260808_111011.json`
- Pair 10: `outputs\Flower\static\flower_comparison_summary_static_run10_seed110.json` <-> `outputs\Unity\static\unity_comparison_summary_static_20260808_111027.json`
