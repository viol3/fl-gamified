# Scenario 2 — Dinamik Oyunlaştırılmış FL — Flower vs Unity (10 paired runs, fixed roster)

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

### Senaryo 2 İçin Çıkarım

Senaryo 2'de `decide_participation()` çağrılır ve ödül artık round/bağlılık/bağlantı/geçmişe duyarlı biçimde kişiselleştirilir (bkz. `senaryo_modlari.md` Bölüm 5). Roster'daki özelliklerin katılım üzerindeki etkisi Senaryo 1'deki taban skor mekanizmasıyla aynıdır, ancak dezavantajlı client'lar (düşük engagement, zayıf bağlantı, önceki round'a katılmama) ek ödül bonusları alır — bu da Senaryo 1'e kıyasla dezavantajlı client'ların katılımını kısmen telafi etmesi beklenen bir mekanizmadır.

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
