# Scenario 0 — Flower vs Unity (10 paired runs, fixed roster)

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

### Senaryo 0 İçin Çıkarım

Senaryo 0'da `decide_participation()` hiç çağrılmadığı için (bkz. `senaryo_modlari.md` Bölüm 3), yukarıdaki özelliklerden yalnızca **connectivity** ve **battery_level** katılım üzerinde gerçek bir etkiye sahip (sunucu tarafı uygunluk filtresi üzerinden — weak connectivity ve düşük batarya elenme riskini artırır). **Engagement, cpu_power, data_quality ve storage_capacity_gb bu senaryoda katılım kararını hiç etkilemiyor** — roster'da bu özelliklerde büyük varyasyon (özellikle data_quality: 0.51-0.99 ve local_samples: 51-191) olsa bile, kimin seçileceği bundan bağımsız, salt `selection_rate=0.6` olasılıklı bir örnekleme. Bölüm 3'teki client-bazlı tabloda da bunu doğruladık: en yüksek engagement'a sahip client'lardan biri (Client 7, engagement=0.70) en az katılan client çıktı — beklenen davranış tam olarak bu. Bu roster, Senaryo 1/2 ile kıyaslandığında asıl farkı ortaya koyacak: aynı roster'da bu sefer engagement/data_quality'nin katılımı gerçekten etkileyip etkilemediğini göreceğiz.

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
- Pair 1: `outputs/Flower\flower_comparison_summary_standart_run01_seed101.json` <-> `outputs/Unity\unity_comparison_summary_standart_20260807_113634.json`
- Pair 2: `outputs/Flower\flower_comparison_summary_standart_run02_seed102.json` <-> `outputs/Unity\unity_comparison_summary_standart_20260807_113703.json`
- Pair 3: `outputs/Flower\flower_comparison_summary_standart_run03_seed103.json` <-> `outputs/Unity\unity_comparison_summary_standart_20260807_113714.json`
- Pair 4: `outputs/Flower\flower_comparison_summary_standart_run04_seed104.json` <-> `outputs/Unity\unity_comparison_summary_standart_20260807_113725.json`
- Pair 5: `outputs/Flower\flower_comparison_summary_standart_run05_seed105.json` <-> `outputs/Unity\unity_comparison_summary_standart_20260807_113738.json`
- Pair 6: `outputs/Flower\flower_comparison_summary_standart_run06_seed106.json` <-> `outputs/Unity\unity_comparison_summary_standart_20260807_113749.json`
- Pair 7: `outputs/Flower\flower_comparison_summary_standart_run07_seed107.json` <-> `outputs/Unity\unity_comparison_summary_standart_20260807_113800.json`
- Pair 8: `outputs/Flower\flower_comparison_summary_standart_run08_seed108.json` <-> `outputs/Unity\unity_comparison_summary_standart_20260807_113814.json`
- Pair 9: `outputs/Flower\flower_comparison_summary_standart_run09_seed109.json` <-> `outputs/Unity\unity_comparison_summary_standart_20260807_113826.json`
- Pair 10: `outputs/Flower\flower_comparison_summary_standart_run10_seed110.json` <-> `outputs/Unity\unity_comparison_summary_standart_20260807_113839.json`
