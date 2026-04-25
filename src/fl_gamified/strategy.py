from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import random

import flwr as fl

from .behavior import ClientBehaviorState
from .bridge import UnityEventPublisher
from .gamification import GamificationEngine


class GamifiedFedAvg(fl.server.strategy.FedAvg):
    def __init__(
        self,
        behavior_states: Dict[str, ClientBehaviorState],
        gamification: GamificationEngine,
        publisher: UnityEventPublisher,
        rng: random.Random,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.behavior_states = behavior_states
        self.gamification = gamification
        self.publisher = publisher
        self.rng = rng
        self.last_selected: List[str] = []

    def configure_fit(self, server_round, parameters, client_manager):
        fit_configurations: List[Tuple[fl.server.client_proxy.ClientProxy, fl.common.FitIns]] = []
        all_clients = list(client_manager.all().values())
        if not all_clients:
            return fit_configurations

        desired = max(self.min_fit_clients, int(self.fraction_fit * len(all_clients)))
        fit_ins = fl.common.FitIns(parameters, {})

        candidates = []
        for proxy in all_clients:
            state = self.behavior_states.get(proxy.cid)
            if state is None or state.churned:
                continue
            boost = self.gamification.participation_boost(proxy.cid)
            p = state.participation_probability(boost=boost)
            if self.rng.random() < p:
                candidates.append(proxy)

        if len(candidates) < self.min_fit_clients:
            fallback = [c for c in all_clients if not self.behavior_states.get(c.cid, ClientBehaviorState(0, 0, 0, 0)).churned]
            self.rng.shuffle(fallback)
            candidates = fallback[: max(self.min_fit_clients, min(desired, len(fallback)))]

        self.rng.shuffle(candidates)
        selected = candidates[: min(desired, len(candidates))]
        self.last_selected = [c.cid for c in selected]

        for client in selected:
            fit_configurations.append((client, fit_ins))

        return fit_configurations

    def aggregate_fit(self, server_round, results, failures):
        for cid, state in self.behavior_states.items():
            if state.churned:
                continue
            was_selected = cid in self.last_selected
            if not was_selected:
                state.update_after_round(was_selected=False, local_loss=None, reward_points=0.0)

        client_updates = []
        for proxy, fit_res in results:
            metrics = dict(fit_res.metrics) if fit_res.metrics else {}
            metrics["num_examples"] = float(fit_res.num_examples)
            points = self.gamification.award_points(proxy.cid, metrics)

            state = self.behavior_states[proxy.cid]
            loss = float(metrics.get("train_loss", 1.5))
            state.update_after_round(was_selected=True, local_loss=loss, reward_points=points)

            client_updates.append(
                {
                    "client_id": proxy.cid,
                    "train_accuracy": float(metrics.get("train_accuracy", 0.0)),
                    "train_loss": loss,
                    "points_awarded": points,
                    "total_points": self.gamification.points.get(proxy.cid, 0.0),
                    "level": self.gamification.get_level(proxy.cid),
                    "churned": state.churned,
                    "battery": state.battery,
                    "engagement": state.engagement,
                }
            )

        active_clients = sum(1 for s in self.behavior_states.values() if not s.churned)
        self.publisher.publish(
            {
                "type": "round_summary",
                "round": server_round,
                "selected_clients": self.last_selected,
                "active_clients": active_clients,
                "leaderboard": self.gamification.leaderboard(10),
                "client_updates": client_updates,
            }
        )

        return super().aggregate_fit(server_round, results, failures)

    def aggregate_evaluate(self, server_round, results, failures):
        aggregated = super().aggregate_evaluate(server_round, results, failures)
        loss, metrics = (None, {}) if aggregated is None else aggregated
        self.publisher.publish(
            {
                "type": "global_eval",
                "round": server_round,
                "loss": float(loss) if loss is not None else None,
                "metrics": metrics or {},
            }
        )
        return aggregated
