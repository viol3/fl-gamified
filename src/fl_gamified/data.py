from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split


@dataclass
class ClientDataset:
    x_train: np.ndarray
    y_train: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray


def load_partitioned_digits(num_clients: int, alpha: float, seed: int) -> Dict[str, ClientDataset]:
    digits = load_digits()
    x = digits.data.astype(np.float32) / 16.0
    y = digits.target.astype(np.int64)

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=seed,
        stratify=y,
    )

    rng = np.random.default_rng(seed)
    num_classes = len(np.unique(y_train))
    indices_by_class = {c: np.where(y_train == c)[0] for c in range(num_classes)}
    for c in indices_by_class:
        rng.shuffle(indices_by_class[c])

    client_indices = {str(i): [] for i in range(num_clients)}

    for c in range(num_classes):
        class_indices = indices_by_class[c]
        proportions = rng.dirichlet(alpha=np.repeat(alpha, num_clients))
        proportions = (proportions / proportions.sum())
        split_points = (np.cumsum(proportions) * len(class_indices)).astype(int)[:-1]
        chunks = np.split(class_indices, split_points)
        for cid, chunk in enumerate(chunks):
            client_indices[str(cid)].extend(chunk.tolist())

    datasets: Dict[str, ClientDataset] = {}
    for cid, idxs in client_indices.items():
        if not idxs:
            idxs = rng.choice(len(x_train), size=25, replace=False).tolist()
        c_x = x_train[idxs]
        c_y = y_train[idxs]

        unique_vals, counts = np.unique(c_y, return_counts=True)
        can_stratify = len(unique_vals) > 1 and np.all(counts >= 2) and len(c_y) >= 10

        if len(c_y) < 5:
            perm = rng.permutation(len(c_y))
            val_count = 1
            val_idx = perm[:val_count]
            train_idx = perm[val_count:]
            if len(train_idx) == 0:
                train_idx = val_idx
            cx_train, cx_val = c_x[train_idx], c_x[val_idx]
            cy_train, cy_val = c_y[train_idx], c_y[val_idx]
        else:
            cx_train, cx_val, cy_train, cy_val = train_test_split(
                c_x,
                c_y,
                test_size=0.2,
                random_state=seed,
                stratify=c_y if can_stratify else None,
            )
        datasets[cid] = ClientDataset(cx_train, cy_train, cx_val, cy_val)

    datasets["_global_test"] = ClientDataset(x_test, y_test, x_test, y_test)
    return datasets
