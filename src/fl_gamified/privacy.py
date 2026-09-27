"""Differential Privacy yardımcıları (DP-FedAvg, McMahan et al. 2018).

- Her istemci güncellemesinin farkı (yerel - global) L2 normunda `clip_norm` ile kırpılır.
- Sunucu, ağırlıkları min(n_k / n_max, 1) ile sınırlanmış kırpılmış farkların toplamına
  N(0, (noise_multiplier * clip_norm)^2) Gauss gürültüsü ekler ve sabit bir paydaya böler.
- Gizlilik kaybı Gauss mekanizmasının Rényi DP (RDP) bileşimiyle hesaplanır. Alt örnekleme
  (subsampling) kazancı hesaba katılmaz; katılım davranışsal olduğundan Poisson örnekleme
  varsayımı sağlanmaz. Bu nedenle raporlanan epsilon bir üst sınırdır.
"""
import math

import numpy as np

# DP gürültüsü, katılım kararlarını süren RNG'den ayrı bir akıştan üretilir;
# böylece DP açık/kapalı olsa da seçim ve katılım dizisi değişmez.
DP_SEED_OFFSET = 1_000_003

RDP_ORDERS = [1.0 + x / 10.0 for x in range(1, 100)] + [float(a) for a in range(11, 257)]


def clip_delta(delta: dict, clip_norm: float) -> tuple[dict, float, bool]:
    """Güncelleme farkını L2 normunda kırp. (kırpılmış fark, orijinal norm, kırpıldı mı) döner."""
    norm = float(np.sqrt(np.sum(np.square(delta["coef"])) + np.sum(np.square(delta["intercept"]))))
    if norm <= clip_norm or norm == 0.0:
        return delta, norm, False
    scale = clip_norm / norm
    return {"coef": delta["coef"] * scale, "intercept": delta["intercept"] * scale}, norm, True


def compute_epsilon(noise_multiplier: float, steps: int, delta: float) -> float:
    """`steps` adet Gauss mekanizması yayınından sonraki (epsilon, delta)-DP epsilon değeri."""
    if steps <= 0:
        return 0.0
    if noise_multiplier <= 0:
        return math.inf
    best = math.inf
    for alpha in RDP_ORDERS:
        rdp = steps * alpha / (2.0 * noise_multiplier ** 2)
        # RDP -> (eps, delta) dönüşümü (Balle et al. 2020; Opacus ile aynı formül)
        eps = rdp + math.log((alpha - 1.0) / alpha) - (math.log(delta) + math.log(alpha)) / (alpha - 1.0)
        best = min(best, eps)
    return max(best, 0.0)
