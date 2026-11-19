from dataclasses import asdict, dataclass, field
import json
import os
import numpy as np
import random
from typing import Optional
from .config import SimulationConfig
from .logger import EventLogger
from .client import Client
from .privacy import DP_SEED_OFFSET, clip_delta, compute_epsilon


@dataclass
class Server:
    """Federated learning server: manages the global model and the clients."""
    
    all_clients: list[Client] = field(default_factory=list)
    active_clients: list[Client] = field(default_factory=list)  # clients active in this round
    config: SimulationConfig = field(default_factory=SimulationConfig)
    model_weights: dict = field(default_factory=dict)
    selected_clients: list[Client] = field(default_factory=list)
    round_number: int = 0
    aggregation_history: list[dict] = field(default_factory=list)
    last_selection_details: list[dict] = field(default_factory=list)
    last_model_accuracy: float = 0.5
    rng: Optional[random.Random] = field(default=None, repr=False)
    logger: Optional[EventLogger] = field(default=None, repr=False)
    dp_releases: int = 0
    dp_clipped_updates: int = 0
    dp_total_updates: int = 0

    def __post_init__(self):
        if self.rng is None:
            self.rng = random.Random(self.config.seed)
        self.dp_rng = np.random.default_rng(self.config.seed + DP_SEED_OFFSET)

    def _client_snapshot(self, client: Client) -> dict:
        return {
            "client_id": client.client_id,
            "local_samples": client.local_samples,
            "digit_focus": client.digit_focus,
            "cpu_power": client.cpu_power,
            "data_quality": client.data_quality,
            "storage_capacity_gb": client.storage_capacity_gb,
            "battery_level": client.battery_level,
            "connectivity": client.connectivity,
            "engagement": client.engagement,
            "local_epochs": client.local_epochs,
            "label_histogram": client.label_histogram,
            "participation_streak": client.participation_streak,
            "total_participations": client.total_participations,
            "previous_round_participated": client.previous_round_participated,
            "fatigue": client.fatigue,
        }

    def _client_ref(self, client: Client) -> dict:
        return {
            "client_id": client.client_id,
        }
    
    def initialize_model(self, input_dim: int = 64, num_classes: int = 10):
        """Initialise the model weights (in the shape of an sklearn LogisticRegression)."""
        self.model_weights = {
            'coef': np.random.randn(num_classes, input_dim) * 0.01,
            'intercept': np.zeros(num_classes),
        }
        print(f"Model initialized | coef shape: {self.model_weights['coef'].shape}")

    def register_clients(self, clients: list[Client]):
        """Register all clients with the server. All of them are active in the first round."""
        self.all_clients.extend(clients)
        self.active_clients.extend(clients)
        print(f"Registered {len(clients)} new clients | Total: {len(self.all_clients)} | Active: {len(self.active_clients)}")
        if self.logger:
            self.logger.log_event("initial_client_roster", {
                "round": self.round_number,
                "clients": [self._client_snapshot(c) for c in clients],
            })
            for c in clients:
                self.logger.log_event("client_registered", {
                    "round": self.round_number,
                    **self._client_ref(c),
                })
    
    def add_clients(self, new_clients: list[Client]):
        """Add new clients during the simulation (for example in round 3)."""
        for client in new_clients:
            if client not in self.all_clients:
                self.all_clients.append(client)
                self.active_clients.append(client)
                print(f"  + Added Client {client.client_id} (battery={client.battery_level}%, engagement={client.engagement:.2f})")
                if self.logger:
                    self.logger.log_event("client_joined", {
                        "round": self.round_number,
                        **self._client_ref(client),
                    })
    
    def remove_clients(self, client_ids: list[int]):
        """Remove the given clients from the active list (dropout, disconnect, etc.)."""
        for client_id in client_ids:
            self.active_clients = [c for c in self.active_clients if c.client_id != client_id]
            print(f"  - Removed Client {client_id} from active list")
            if self.logger:
                self.logger.log_event("client_left", {"round": self.round_number, "client_id": client_id})
    
    def get_active_clients_summary(self) -> str:
        """Return a short summary of the active clients."""
        if not self.active_clients:
            return "No active clients"
        
        client_ids = [c.client_id for c in self.active_clients]
        avg_battery = np.mean([c.battery_level for c in self.active_clients])
        avg_engagement = np.mean([c.engagement for c in self.active_clients])
        return f"Active: {client_ids} | Avg Battery: {avg_battery:.1f}% | Avg Engagement: {avg_engagement:.2f}"

    def select_clients(self, selection_rate: float = 0.6) -> list[Client]:
        """
        Client selection: offer a reward to every eligible active client and
        ask for its participation decision.

        - Eligibility depends on connectivity and battery level (see config.py).
        - The reward offer depends on the scenario mode (see _compute_reward_offer).
        """
        self.selected_clients = []
        self.last_selection_details = []

        selection_rate = max(0.0, min(selection_rate, 1.0))
        
        for client in self.active_clients:
            # Basic eligibility check
            connection_ok = True
            if client.connectivity == "weak":
                if self.rng.random() < self.config.weak_connection_skip_prob:
                    connection_ok = False

            battery_ok = True
            if client.battery_level < self.config.low_battery_threshold:
                if self.rng.random() > self.config.low_battery_pass_prob:
                    battery_ok = False

            if not (connection_ok and battery_ok):
                # Log why client was skipped
                decision_details = {
                    "reason": "ineligible",
                    "score": 0.0,
                    "fatigue_penalty": 0.0,
                    "reward_bonus": 0.0,
                    "drop_chance": 0.0,
                }
                selection_record = {
                    "round": self.round_number,
                    **self._client_ref(client),
                    "mode": self.config.mode,
                    "connection_ok": connection_ok,
                    "battery_ok": battery_ok,
                    "reward_offer": 0,
                    "decision": decision_details,
                    "selected": False,
                    "selection_rate": selection_rate,
                }
                self.last_selection_details.append(selection_record)
                if self.logger:
                    self.logger.log_event("client_skipped", selection_record)
                continue

            if self.config.mode == 0:
                reward_offer = 0
                participates = self.rng.random() < selection_rate
                details = {
                    "reason": "base_selection",
                    "score": selection_rate,
                    "fatigue_penalty": 0.0,
                    "reward_bonus": 0.0,
                    "drop_chance": 0.0,
                }
            else:
                reward_offer = self._compute_reward_offer(client)

                # Ask the client whether it will participate
                participates, details = client.decide_participation(
                    reward_points=reward_offer,
                    rng=self.rng,
                    reward_bonus_cap=self.config.reward_bonus_cap,
                )

                if participates:
                    participates = self.rng.random() < selection_rate

            # simulate submission latency for later replay (seconds)
            simulated_latency = float(self.rng.uniform(0.2, 5.0))

            selection_record = {
                "round": self.round_number,
                **self._client_ref(client),
                "mode": self.config.mode,
                "connection_ok": connection_ok,
                "battery_ok": battery_ok,
                "reward_offer": reward_offer,
                "decision": details,
                "selected": participates,
                "selection_rate": selection_rate,
                "simulated_submission_latency": simulated_latency,
            }
            self.last_selection_details.append(selection_record)

            # Detailed per-client decision log
            if self.logger:
                self.logger.log_event("client_decision", selection_record)

            if participates:
                self.selected_clients.append(client)
        
        return self.selected_clients
    
    def _compute_reward_offer(self, client: Client) -> int:
        """
        Compute the reward offered to a client (see config.py).

        - Mode 1: fixed reward (static_reward_points, capped at max_reward)
        - Mode 2: base_reward_offset + round number + client-specific bonuses
          (engagement_bonus, weak_connectivity_bonus, previous_participation_bonus),
          capped at max_reward
        """
        if self.config.mode == 1:
            return min(self.config.static_reward_points, self.config.max_reward)

        reward = self.config.base_reward_offset + self.round_number
        if client.engagement < self.config.engagement_threshold:
            reward += self.config.engagement_bonus
        if client.connectivity == "weak":
            reward += self.config.weak_connectivity_bonus
        if not client.previous_round_participated:
            reward += self.config.previous_participation_bonus
        return min(reward, self.config.max_reward)

    def aggregate_weights(self, client_updates: list[dict], client_sample_counts: list[int]) -> dict:
        """
        Federated Averaging (FedAvg): combine the updates with a weighted average.
        
        Args:
            client_updates: updated weights of each client
            client_sample_counts: number of samples of each client (used as weights)
        """
        total_samples = sum(client_sample_counts)
        
        # Start from zero weights
        aggregated_weights = {
            'coef': np.zeros_like(self.model_weights['coef']),
            'intercept': np.zeros_like(self.model_weights['intercept']),
        }
        
        # Weighted average
        for client_update, sample_count in zip(client_updates, client_sample_counts):
            weight = sample_count / total_samples
            aggregated_weights['coef'] += weight * client_update['coef']
            aggregated_weights['intercept'] += weight * client_update['intercept']

        return aggregated_weights

    def aggregate_weights_dp(self, client_updates: list[dict], client_sample_counts: list[int]) -> dict:
        """
        DP-FedAvg (McMahan et al. 2018): noisy weighted average of the clipped updates.

        The weights are bounded by w_k = min(n_k / n_max, 1), so a single client can change
        the sum by at most dp_clip_norm (sensitivity). The denominator is a constant that does
        not depend on which clients were selected: selection_rate * sum(w_k over all clients).
        """
        clip_norm = self.config.dp_clip_norm
        max_samples = max(c.local_samples for c in self.all_clients)
        fixed_denominator = self.config.selection_rate * sum(
            min(c.local_samples / max_samples, 1.0) for c in self.all_clients
        )

        delta_sum = {
            'coef': np.zeros_like(self.model_weights['coef']),
            'intercept': np.zeros_like(self.model_weights['intercept']),
        }
        for client_update, sample_count in zip(client_updates, client_sample_counts):
            delta = {
                'coef': client_update['coef'] - self.model_weights['coef'],
                'intercept': client_update['intercept'] - self.model_weights['intercept'],
            }
            clipped, _, was_clipped = clip_delta(delta, clip_norm)
            self.dp_clipped_updates += int(was_clipped)
            self.dp_total_updates += 1
            weight = min(sample_count / max_samples, 1.0)
            delta_sum['coef'] += weight * clipped['coef']
            delta_sum['intercept'] += weight * clipped['intercept']

        noise_std = self.config.dp_noise_multiplier * clip_norm
        delta_sum['coef'] += self.dp_rng.normal(0.0, noise_std, size=delta_sum['coef'].shape)
        delta_sum['intercept'] += self.dp_rng.normal(0.0, noise_std, size=delta_sum['intercept'].shape)
        self.dp_releases += 1

        return {
            'coef': self.model_weights['coef'] + delta_sum['coef'] / fixed_denominator,
            'intercept': self.model_weights['intercept'] + delta_sum['intercept'] / fixed_denominator,
        }

    def dp_epsilon(self) -> float:
        if not self.config.dp_enabled:
            return 0.0
        return compute_epsilon(self.config.dp_noise_multiplier, self.dp_releases, self.config.dp_delta)

    def update_model(self, aggregated_weights: dict, learning_rate: float = 1.0):
        """Update the global model with the new weights."""
        self.model_weights['coef'] = aggregated_weights['coef'] * learning_rate + \
                                      self.model_weights['coef'] * (1 - learning_rate)
        self.model_weights['intercept'] = aggregated_weights['intercept'] * learning_rate + \
                                          self.model_weights['intercept'] * (1 - learning_rate)

    def _calculate_weight_magnitude(self) -> float:
        if not self.model_weights:
            return 0.0

        coef = self.model_weights["coef"]
        intercept = self.model_weights["intercept"]
        return float(np.sqrt(np.sum(np.square(coef)) + np.sum(np.square(intercept))))

    def _calculate_label_diversity_bonus(self, client: Client) -> float:
        if not client.label_histogram:
            return 0.10
        return min(len(client.label_histogram) / 10.0, 1.0) * 0.20

    def _calculate_client_local_accuracy(self, client: Client) -> None:
        base_accuracy = 0.5
        weight_magnitude = self._calculate_weight_magnitude()
        num_weights = int(np.size(self.model_weights["coef"])) if self.model_weights else 1
        convergence_bonus = min(weight_magnitude / (num_weights * 0.5), 1.0) * 0.30
        data_quality_bonus = client.data_quality * 0.25
        diversity_bonus = self._calculate_label_diversity_bonus(client)
        sample_bonus = min(client.local_samples / 200.0, 1.0) * 0.15
        fatigue_penalty = client.fatigue * 0.10
        variance = (self.rng.random() - 0.5) * 0.02

        client.local_model_accuracy = max(
            0.30,
            min(
                base_accuracy
                + convergence_bonus
                + data_quality_bonus
                + diversity_bonus
                + sample_bonus
                - fatigue_penalty
                + variance,
                0.95,
            ),
        )

    def _evaluate_model(self, tested_clients: list[Client]) -> None:
        if not tested_clients:
            self.last_model_accuracy = max(self.config.min_accuracy, self.last_model_accuracy - 0.02)
            return

        weight_magnitude = self._calculate_weight_magnitude()
        num_weights = int(np.size(self.model_weights["coef"])) if self.model_weights else 1
        initial_magnitude = num_weights * 0.05
        convergence_bonus = min((weight_magnitude - initial_magnitude) / (num_weights * 0.5), 0.35)
        convergence_bonus = max(0.0, convergence_bonus)

        avg_data_quality = float(np.mean([client.data_quality for client in tested_clients]))
        avg_engagement = float(np.mean([client.engagement for client in tested_clients]))
        quality_bonus = avg_data_quality * 0.12 + avg_engagement * 0.08
        round_bonus = min(self.round_number * 0.025, 0.15)
        participation_bonus = min(len(tested_clients) / 10.0 * 0.1, 0.1)

        self.last_model_accuracy = self.config.min_accuracy + convergence_bonus + quality_bonus + round_bonus + participation_bonus
        self.last_model_accuracy += (self.rng.random() - 0.5) * 0.02
        self.last_model_accuracy = max(self.config.min_accuracy, min(self.last_model_accuracy, self.config.max_accuracy))

    def simulate_round(self, selection_rate: float = 0.6) -> dict:
        """Simulate a single FL round."""
        self.round_number += 1
        if self.logger:
            self.logger.log_event("round_start", {
                "round": self.round_number,
                "active_client_ids": [c.client_id for c in self.active_clients],
                "active_count": len(self.active_clients),
            })
        
        # Update the clients that took part in the previous round
        for client in self.selected_clients:
            client.apply_round_outcome(participated=True)
        
        # Update the active clients that did not take part
        for client in self.active_clients:
            if client not in self.selected_clients:
                client.apply_round_outcome(participated=False)
        
        # Select the clients for this round
        selected = self.select_clients(selection_rate or self.config.selection_rate)
        
        # Simulated local training: each selected client produces an update
        client_updates = []
        sample_counts = []
        
        for client in selected:
            # Simple simulation: each client adds small noise to the weights
            local_update = {
                'coef': self.model_weights['coef'] + np.random.randn(*self.model_weights['coef'].shape) * 0.01,
                'intercept': self.model_weights['intercept'] + np.random.randn(*self.model_weights['intercept'].shape) * 0.01,
            }
            client_updates.append(local_update)
            sample_counts.append(client.local_samples)
            self._calculate_client_local_accuracy(client)
            if self.logger:
                # Log summary statistics of the local update (not full arrays)
                coef_mean = float(np.mean(local_update['coef']))
                coef_std = float(np.std(local_update['coef']))
                intercept_mean = float(np.mean(local_update['intercept']))
                intercept_std = float(np.std(local_update['intercept']))
                self.logger.log_event("local_update", {
                    "round": self.round_number,
                    "client_id": client.client_id,
                    "local_samples": client.local_samples,
                    "coef_mean": coef_mean,
                    "coef_std": coef_std,
                    "intercept_mean": intercept_mean,
                    "intercept_std": intercept_std,
                })
        
        # Aggregation
        if client_updates:
            if self.config.dp_enabled:
                aggregated = self.aggregate_weights_dp(client_updates, sample_counts)
            else:
                aggregated = self.aggregate_weights(client_updates, sample_counts)
            self.update_model(aggregated)
            self._evaluate_model(selected)
            if self.logger:
                # Aggregation summary (avoid dumping large arrays)
                agg_coef_mean = float(np.mean(aggregated['coef']))
                agg_coef_std = float(np.std(aggregated['coef']))
                agg_intercept_mean = float(np.mean(aggregated['intercept']))
                agg_intercept_std = float(np.std(aggregated['intercept']))
                self.logger.log_event("aggregation", {
                    "round": self.round_number,
                    "selected_count": len(selected),
                    "total_samples": sum(sample_counts),
                    "agg_coef_mean": agg_coef_mean,
                    "agg_coef_std": agg_coef_std,
                    "agg_intercept_mean": agg_intercept_mean,
                    "agg_intercept_std": agg_intercept_std,
                })
        
        # Save to history
        round_info = {
            'round': self.round_number,
            'active_clients': len(self.active_clients),
            'selected_count': len(selected),
            'trained_count': len(client_updates),
            'total_samples': sum(sample_counts) if sample_counts else 0,
            'selected_client_ids': [c.client_id for c in selected],
            'trained_client_ids': [c.client_id for c in selected],
            'model_accuracy': self.last_model_accuracy,
            'weight_norm': self._calculate_weight_magnitude(),
            'dp_epsilon': self.dp_epsilon(),
        }
        self.aggregation_history.append(round_info)

        if self.logger:
            self.logger.log_event("round_end", {"round": self.round_number, "round_info": round_info})

        return round_info

    def build_comparison_summary(self) -> dict:
        return {
            "config": asdict(self.config),
            "rounds": self.aggregation_history,
            "final_clients": [
                {
                    "client_id": client.client_id,
                    "battery_level": client.battery_level,
                    "engagement": client.engagement,
                    "participation_streak": client.participation_streak,
                    "total_participations": client.total_participations,
                    "fatigue": client.fatigue,
                    "local_model_accuracy": client.local_model_accuracy,
                }
                for client in self.all_clients
            ],
            "final_model_accuracy": self.last_model_accuracy,
            "dp": {
                "enabled": self.config.dp_enabled,
                "clip_norm": self.config.dp_clip_norm,
                "noise_multiplier": self.config.dp_noise_multiplier,
                "delta": self.config.dp_delta,
                "releases": self.dp_releases,
                "clipped_updates": self.dp_clipped_updates,
                "total_updates": self.dp_total_updates,
                "epsilon": self.dp_epsilon(),
            },
        }

    def export_comparison_summary(self, path: str = "outputs/flower_comparison_summary.json") -> str:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.build_comparison_summary(), handle, ensure_ascii=False, indent=2)
        return path

    def describe(self) -> str:
        """Describe the server state."""
        return (
            f"Server Round {self.round_number} | "
            f"total_clients: {len(self.all_clients)} | "
            f"active_clients: {len(self.active_clients)} | "
            f"selected_clients: {len(self.selected_clients)} | "
            f"model_shape: {self.model_weights['coef'].shape if self.model_weights else 'N/A'} | "
            f"aggregation_rounds: {len(self.aggregation_history)}"
        )
