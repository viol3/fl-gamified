# Scenario 1 — Statik Teşvik — Flower vs Unity (10 paired runs, fixed roster)

## 0. Client Roster Profili

Sabit roster: 10 client, toplam 1042 sample (ort. 104.2/client).

### Özellik Dağılımı

| Özellik | Min | Max | Ortalama | Std | Varyasyon Katsayısı (CV) |
|---|---|---|---|---|---|
| Engagement | 0.59 | 0.78 | 0.657 | 0.050 | 0.076 |
| Battery Level | 60 | 91 | 77.100 | 11.631 | 0.151 |
| CPU Power | 1.5 | 3.6 | 2.530 | 0.766 | 0.303 |
| Data Quality | 0.51 | 0.99 | 0.736 | 0.170 | 0.231 |
| Storage (GB) | 0.15 | 0.59 | 0.352 | 0.166 | 0.470 |
| Local Samples | 51 | 191 | 104.200 | 40.524 | 0.389 |
| Local Epochs | 1 | 4 | 2.800 | 1.077 | 0.385 |

**Ön plana çıkan özellik:** CV (std/mean) bazında en fazla farklılaşan özellik **Storage (GB)** (CV=0.470) — client'lar arasında en çok bu boyutta ayrışıyorlar. En homojen özellik ise **Engagement** (CV=0.076) — engagement değerleri client'lar arasında görece dar bir bantta (0.59-0.78) toplanmış, yani roster'da 'aşırı motivasyonsuz' ya da 'aşırı motivasyonlu' bir uç client yok.

### Connectivity Dağılımı

- strong: 3 client
- medium: 4 client
- weak: 3 client

### Veri (Digit) Kapsamı

- Roster'ın kapsadığı rakamlar: [0, 1, 2, 3, 4, 6, 7]
- **Hiç örneği olmayan rakamlar: [5, 8, 9]** — bu roster'da hiçbir client'ın local_samples'ında [5, 8, 9] rakamlarına ait tek bir örnek yok (Dirichlet/non-IID dağılımın rastgele bir sonucu). Bu, hangi senaryo çalışırsa çalışsın (0/1/2 fark etmez) global modelin bu rakamları hiç görmeden eğitileceği anlamına gelir — mevcut accuracy simülasyonu rakam-bazlı değil toplu bir formül kullandığı için sayısal sonucu etkilemiyor, ama gerçek bir sınıflandırma deneyinde bu ciddi bir kapsam boşluğu olarak raporlanmalı.

### Senaryo 1 İçin Çıkarım

Senaryo 1'de `decide_participation()` çağrıldığı için (bkz. `senaryo_modlari.md` Bölüm 4), yukarıdaki özelliklerin tamamı katılım skoruna doğrudan girer: `base_score = 0.45*engagement + 0.25*(battery/100) + 0.15*min(cpu_power/4,1) + 0.15*data_quality`. Ödül sabit olduğu için (`static_reward_points`) tüm client'lara aynı `reward_bonus` eklenir — dolayısıyla client'lar arası katılım farkı artık **yalnızca roster'daki içsel farklılıklardan** kaynaklanır. Buna ek olarak, hem sunucu tarafı uygunluk filtresi (Bölüm 2) hem de istemci içi ikinci kademe kontrol (batarya<20, bağlantı kopma olasılığı: weak=0.35, medium=0.15, strong=0.05) weak/medium connectivity client'ları yapısal olarak dezavantajlı kılar. Senaryo 0'ın aksine burada engagement ve data_quality gibi özelliklerin katılım üzerinde ölçülebilir bir etkisi beklenir.

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
