"""Differential privacy helpers (DP-FedAvg, McMahan et al. 2018).

- Each client update (local - global) is clipped to L2 norm `clip_norm`.
- The server adds Gaussian noise N(0, (noise_multiplier * clip_norm)^2) to the sum of the
  clipped updates, weighted by min(n_k / n_max, 1), and divides by a fixed denominator.
- The privacy loss is computed with Renyi DP (RDP) composition of the Gaussian mechanism.
  No amplification by subsampling is assumed, because participation is behavioural and the
  Poisson sampling assumption does not hold. The reported epsilon is therefore an upper bound.
"""
import math

import numpy as np

# DP noise comes from a separate RNG stream than the participation decisions,
# so turning DP on or off does not change the selection and participation sequence.
DP_SEED_OFFSET = 1_000_003

RDP_ORDERS = [1.0 + x / 10.0 for x in range(1, 100)] + [float(a) for a in range(11, 257)]


def clip_delta(delta: dict, clip_norm: float) -> tuple[dict, float, bool]:
    """Clip an update to the given L2 norm. Returns (clipped update, original norm, was_clipped)."""
    norm = float(np.sqrt(np.sum(np.square(delta["coef"])) + np.sum(np.square(delta["intercept"]))))
    if norm <= clip_norm or norm == 0.0:
        return delta, norm, False
    scale = clip_norm / norm
    return {"coef": delta["coef"] * scale, "intercept": delta["intercept"] * scale}, norm, True


def compute_epsilon(noise_multiplier: float, steps: int, delta: float) -> float:
    """Epsilon of (epsilon, delta)-DP after `steps` releases of the Gaussian mechanism."""
    if steps <= 0:
        return 0.0
    if noise_multiplier <= 0:
        return math.inf
    best = math.inf
    for alpha in RDP_ORDERS:
        rdp = steps * alpha / (2.0 * noise_multiplier ** 2)
        # RDP to (eps, delta) conversion (Balle et al. 2020; same formula as Opacus)
        eps = rdp + math.log((alpha - 1.0) / alpha) - (math.log(delta) + math.log(alpha)) / (alpha - 1.0)
        best = min(best, eps)
    return max(best, 0.0)
