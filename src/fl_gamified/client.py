from __future__ import annotations

from typing import Dict

import flwr as fl
import numpy as np
from sklearn.metrics import accuracy_score, log_loss

from .behavior import ClientBehaviorState
from .data import ClientDataset
from .gamification import GamificationEngine
from .model import create_model, get_parameters, initialize_model, set_parameters


class SimulatedClient(fl.client.NumPyClient):
    def __init__(
        self,
        client_id: str,
        dataset: ClientDataset,
        behavior_state: ClientBehaviorState,
        gamification: GamificationEngine,
        seed: int,
        local_epochs: int,
        all_classes: np.ndarray | None = None,
    ) -> None:
        self.client_id = client_id
        self.dataset = dataset
        self.behavior_state = behavior_state
        self.gamification = gamification
        self.local_epochs = local_epochs

        self.model = create_model(seed=seed)
        classes = all_classes if all_classes is not None else np.arange(10)
        initialize_model(self.model, dataset.x_train.shape[1], classes)

    def get_parameters(self, config: Dict[str, str]):
        return get_parameters(self.model)

    def fit(self, parameters, config):
        set_parameters(self.model, parameters)

        for _ in range(self.local_epochs):
            self.model.partial_fit(self.dataset.x_train, self.dataset.y_train)

        y_pred = self.model.predict(self.dataset.x_train)
        y_proba = self.model.predict_proba(self.dataset.x_train)
        train_acc = float(accuracy_score(self.dataset.y_train, y_pred))
        train_loss = float(log_loss(self.dataset.y_train, y_proba, labels=self.model.classes_))

        level = self.gamification.get_level(self.client_id)
        metrics = {
            "train_accuracy": train_acc,
            "train_loss": train_loss,
            "battery": float(self.behavior_state.battery),
            "engagement": float(self.behavior_state.engagement),
            "level": float(level),
            "num_examples": float(len(self.dataset.y_train)),
        }

        return get_parameters(self.model), len(self.dataset.y_train), metrics

    def evaluate(self, parameters, config):
        set_parameters(self.model, parameters)

        y_pred = self.model.predict(self.dataset.x_val)
        y_proba = self.model.predict_proba(self.dataset.x_val)
        loss = float(log_loss(self.dataset.y_val, y_proba, labels=self.model.classes_))
        acc = float(accuracy_score(self.dataset.y_val, y_pred))
        return loss, len(self.dataset.y_val), {"val_accuracy": acc}
