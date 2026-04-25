from __future__ import annotations

import random
from typing import Dict

import numpy as np
from sklearn.metrics import accuracy_score, log_loss

from .behavior import ClientBehaviorState
from .bridge import UnityEventPublisher
from .client import SimulatedClient
from .config import ExperimentConfig, Scenario
from .data import load_partitioned_digits
from .gamification import GamificationEngine
from .model import create_model, get_parameters, initialize_model, set_parameters


def _aggregate_weighted(client_results):
    total_examples = sum(num_examples for _, num_examples, _ in client_results)
    if total_examples == 0:
        return None

    num_layers = len(client_results[0][0])
    agg = []
    for layer_idx in range(num_layers):
        weighted_sum = sum(
            params[layer_idx] * (num_examples / total_examples)
            for params, num_examples, _ in client_results
        )
        agg.append(weighted_sum)
    return agg


def run_experiment(config: ExperimentConfig) -> None:
    rng = random.Random(config.random_seed)
    np.random.seed(config.random_seed)

    datasets = load_partitioned_digits(
        num_clients=config.num_clients,
        alpha=config.dirichlet_alpha,
        seed=config.random_seed,
    )
    global_test = datasets["_global_test"]

    behavior_states: Dict[str, ClientBehaviorState] = {
        str(cid): ClientBehaviorState.random_state(rng) for cid in range(config.num_clients)
    }
    gamification = GamificationEngine(scenario=config.scenario)
    publisher = UnityEventPublisher(output_path=config.unity_event_path)

    clients: Dict[str, SimulatedClient] = {}
    all_classes = np.arange(10)
    for cid in range(config.num_clients):
        cid_str = str(cid)
        clients[cid_str] = SimulatedClient(
            client_id=cid_str,
            dataset=datasets[cid_str],
            behavior_state=behavior_states[cid_str],
            gamification=gamification,
            seed=config.random_seed + cid,
            local_epochs=config.local_epochs,
            all_classes=all_classes,
        )

    eval_model = create_model(seed=config.random_seed)
    classes = np.unique(global_test.y_train)
    initialize_model(eval_model, global_test.x_train.shape[1], classes)

    # Use one initialized client as global parameter template.
    global_parameters = get_parameters(clients["0"].model)

    if config.scenario == Scenario.BASELINE:
        publisher.publish({"type": "scenario", "name": "baseline"})
    elif config.scenario == Scenario.STATIC:
        publisher.publish({"type": "scenario", "name": "static"})
    else:
        publisher.publish({"type": "scenario", "name": "gamified"})

    for server_round in range(1, config.num_rounds + 1):
        desired = max(config.min_fit_clients, int(config.fraction_fit * config.num_clients))
        candidates = []
        for cid, state in behavior_states.items():
            if state.churned:
                continue
            boost = gamification.participation_boost(cid)
            if rng.random() < state.participation_probability(boost=boost):
                candidates.append(cid)

        if len(candidates) < config.min_fit_clients:
            fallback = [cid for cid, state in behavior_states.items() if not state.churned]
            rng.shuffle(fallback)
            candidates = fallback[: max(config.min_fit_clients, min(desired, len(fallback)))]

        rng.shuffle(candidates)
        selected = candidates[: min(desired, len(candidates))]

        round_results = []
        for cid in selected:
            client = clients[cid]
            params, num_examples, metrics = client.fit(global_parameters, {})
            round_results.append((params, num_examples, metrics))

        if round_results:
            aggregated = _aggregate_weighted(round_results)
            if aggregated is not None:
                global_parameters = aggregated

        for cid, state in behavior_states.items():
            if not state.churned and cid not in selected:
                state.update_after_round(was_selected=False, local_loss=None, reward_points=0.0)

        client_updates = []
        for cid, (_, _, metrics) in zip(selected, round_results):
            points = gamification.award_points(cid, metrics)
            state = behavior_states[cid]
            loss = float(metrics.get("train_loss", 1.5))
            state.update_after_round(was_selected=True, local_loss=loss, reward_points=points)
            client_updates.append(
                {
                    "client_id": cid,
                    "train_accuracy": float(metrics.get("train_accuracy", 0.0)),
                    "train_loss": loss,
                    "points_awarded": points,
                    "total_points": gamification.points.get(cid, 0.0),
                    "level": gamification.get_level(cid),
                    "churned": state.churned,
                    "battery": state.battery,
                    "engagement": state.engagement,
                }
            )

        active_clients = sum(1 for s in behavior_states.values() if not s.churned)
        publisher.publish(
            {
                "type": "round_summary",
                "round": server_round,
                "selected_clients": selected,
                "active_clients": active_clients,
                "leaderboard": gamification.leaderboard(10),
                "client_updates": client_updates,
            }
        )

        set_parameters(eval_model, global_parameters)
        y_pred = eval_model.predict(global_test.x_val)
        y_proba = eval_model.predict_proba(global_test.x_val)
        loss = float(log_loss(global_test.y_val, y_proba, labels=eval_model.classes_))
        acc = float(accuracy_score(global_test.y_val, y_pred))
        publisher.publish(
            {
                "type": "global_eval",
                "round": server_round,
                "loss": loss,
                "metrics": {"global_accuracy": acc},
            }
        )

    publisher.publish(
        {
            "type": "final_summary",
            "leaderboard": gamification.leaderboard(20),
            "remaining_active_clients": sum(1 for s in behavior_states.values() if not s.churned),
        }
    )
