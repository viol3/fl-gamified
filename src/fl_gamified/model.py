from __future__ import annotations

from typing import List

import numpy as np
from sklearn.linear_model import SGDClassifier


def create_model(seed: int) -> SGDClassifier:
    return SGDClassifier(
        loss="log_loss",
        max_iter=1,
        learning_rate="optimal",
        tol=None,
        random_state=seed,
    )


def initialize_model(model: SGDClassifier, n_features: int, classes: np.ndarray) -> None:
    dummy_x = np.zeros((len(classes), n_features), dtype=np.float32)
    dummy_y = classes.astype(np.int64)
    model.partial_fit(dummy_x, dummy_y, classes=classes)


def get_parameters(model: SGDClassifier) -> List[np.ndarray]:
    return [model.coef_.copy(), model.intercept_.copy()]


def set_parameters(model: SGDClassifier, parameters: List[np.ndarray]) -> None:
    model.coef_ = parameters[0].copy()
    model.intercept_ = parameters[1].copy()
    model.classes_ = np.arange(model.coef_.shape[0])
