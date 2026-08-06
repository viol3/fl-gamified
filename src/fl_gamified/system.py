from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import os
from time import perf_counter
from typing import Optional

import numpy as np

from .client import Client
from .config import SimulationConfig
from .server import Server


class FLPhase(Enum):
    Idle = 0
    ClientSelection = 1
    LocalTraining = 2
    Aggregation = 3
    ModelEvaluation = 4
    RoundComplete = 5


@dataclass
class RoundPhaseReport:
    current_phase: FLPhase = FLPhase.Idle
    next_phase: FLPhase = FLPhase.Idle
    success: bool = False
    message: str = ""
    round: int = 0
    selected_client_ids: list[int] = field(default_factory=list)
    selected_count: int = 0
    participating_client_ids: list[int] = field(default_factory=list)
    trained_client_ids: list[int] = field(default_factory=list)
    trained_count: int = 0
    total_training_samples: int = 0
    aggregated_accuracy: float = 0.0
    aggregated_samples: int = 0
    execution_time_ms: float = 0.0


@dataclass
class FLSystem:
    config: Optional[SimulationConfig] = None
    server: Optional[Server] = None
    simulation_initialized: bool = False
    current_phase: FLPhase = FLPhase.Idle
    _current_round_client_updates: list[dict] = field(default_factory=list, init=False, repr=False)
    _current_round_sample_counts: list[int] = field(default_factory=list, init=False, repr=False)
    _current_round_trained_clients: list[Client] = field(default_factory=list, init=False, repr=False)
    _selection_rate_override: Optional[float] = field(default=None, init=False, repr=False)

    def start(self) -> None:
        if self.config is None:
            self.config = SimulationConfig(seed=42, rounds=100)

    def initialize_simulation(self) -> None:
        if self.config is None:
            self.config = SimulationConfig(seed=42, rounds=100)

        print("=" + "=" * 88)
        print("Scenario: Digits Classification - Federated Learning with Gamified Incentives")
        print("=" + "=" * 88)
        print()

        self.server = Server(config=self.config)
        self.server.initialize_model(input_dim=self.config.input_dim, num_classes=self.config.num_classes)
        self.server.last_model_accuracy = self.config.min_accuracy
        self.current_phase = FLPhase.Idle
        self.simulation_initialized = True
        print("\n✓ Simülasyon hazır. run_one_phase() çağrısı yaparak başlayabilirsiniz.\n")

    def get_server(self) -> Optional[Server]:
        return self.server

    def get_client_by_index(self, index: int) -> Optional[Client]:
        if self.server is None:
            print("Server henüz initialize edilmemiş. Önce initialize_simulation() çağırın.")
            return None

        if index < 0 or index >= len(self.server.all_clients):
            print(f"Geçersiz index: {index}. Toplam client sayısı: {len(self.server.all_clients)}")
            return None

        return self.server.all_clients[index]

    def add_client(self, client: Client) -> None:
        if self.server is None:
            print("Server henüz initialize edilmemiş. initialize_simulation çağrısından sonra add_client çağırın.")
            return

        if client is None:
            print("Null client eklenemez.")
            return

        self.server.add_clients([client])
        print(f"✓ Client {client.client_id} sisteme eklendi.")

    def remove_client(self, index: int) -> None:
        if self.server is None:
            print("Server henüz initialize edilmemiş.")
            return

        if index < 0 or index >= len(self.server.all_clients):
            print(f"Geçersiz index: {index}. Toplam client sayısı: {len(self.server.all_clients)}")
            return

        client_to_remove = self.server.all_clients[index]
        self.server.remove_clients([client_to_remove.client_id])
        self.server.all_clients.pop(index)
        print(f"✓ Client {client_to_remove.client_id} (index {index}) silindi.")

    def get_client_count(self) -> int:
        if self.server is None:
            return 0
        return len(self.server.all_clients)

    def get_all_clients(self) -> list[Client]:
        if self.server is None:
            return []
        return self.server.all_clients

    def run_one_phase(self) -> RoundPhaseReport:
        if not self.simulation_initialized or self.server is None:
            print("Simülasyon henüz initialize edilmedi. Önce initialize_simulation() çağırın.")
            return RoundPhaseReport(success=False, message="Simülasyon initialize edilmedi.")

        start_time = perf_counter()
        report = RoundPhaseReport(current_phase=self.current_phase, round=self.server.round_number)

        if self.current_phase == FLPhase.Idle:
            self._execute_phase_idle(report)
        elif self.current_phase == FLPhase.ClientSelection:
            self._execute_phase_client_selection(report)
        elif self.current_phase == FLPhase.LocalTraining:
            self._execute_phase_local_training(report)
        elif self.current_phase == FLPhase.Aggregation:
            self._execute_phase_aggregation(report)
        elif self.current_phase == FLPhase.ModelEvaluation:
            self._execute_phase_model_evaluation(report)
        elif self.current_phase == FLPhase.RoundComplete:
            self._execute_phase_round_complete(report)
        else:
            report.success = False
            report.message = "Unknown phase"

        report.next_phase = self.current_phase
        report.execution_time_ms = (perf_counter() - start_time) * 1000.0
        return report

    def simulate_round(self, selection_rate: float = 0.6) -> dict:
        self._selection_rate_override = selection_rate
        start_round = self.server.round_number if self.server is not None else 0

        while True:
            report = self.run_one_phase()
            if self.server is not None and self.current_phase == FLPhase.Idle and self.server.round_number > start_round:
                break

        if self.server is None or not self.server.aggregation_history:
            return {
                "round": start_round + 1,
                "active_clients": 0,
                "selected_count": 0,
                "total_samples": 0,
                "selected_client_ids": [],
                "model_accuracy": 0.0,
            }

        return self.server.aggregation_history[-1]

    def _execute_phase_idle(self, report: RoundPhaseReport) -> None:
        try:
            self.server.round_number += 1
            print(f"\n{'─' * 90}")
            print(f"ROUND {self.server.round_number}")
            print(f"{'─' * 90}")
            print(f"\nServer: {self.server.describe()}")
            print(f"Status: {self.server.get_active_clients_summary()}")
            self.current_phase = FLPhase.ClientSelection
            report.success = True
            report.message = f"Round {self.server.round_number} hazırlandı. Client seçimi başlayacak."
        except Exception as exc:
            report.success = False
            report.message = f"Idle phase hatası: {exc}"

    def _execute_phase_client_selection(self, report: RoundPhaseReport) -> None:
        try:
            print("\n--- Client Selection Phase ---")
            self.server.select_clients(self._selection_rate_override if self._selection_rate_override is not None else self.config.selection_rate)
            report.success = True
            report.selected_count = len(self.server.selected_clients)
            report.selected_client_ids = [client.client_id for client in self.server.selected_clients]
            report.message = f"{report.selected_count} client seçildi: {', '.join(map(str, report.selected_client_ids))}"
            print(f"\n✓ Client Selection:")
            print(f"  - Seçilen: {report.selected_count}")
            print(f"  - Client IDs: {', '.join(map(str, report.selected_client_ids))}")
            self.current_phase = FLPhase.LocalTraining
        except Exception as exc:
            report.success = False
            report.message = f"Client seçimi hatası: {exc}"

    def _execute_phase_local_training(self, report: RoundPhaseReport) -> None:
        try:
            print("\n--- Local Training Phase ---")
            self._current_round_client_updates.clear()
            self._current_round_sample_counts.clear()
            self._current_round_trained_clients.clear()

            for client in self.server.selected_clients:
                self._current_round_trained_clients.append(client)
                local_update = {
                    "coef": self.server.model_weights["coef"] + np.random.randn(*self.server.model_weights["coef"].shape) * 0.01,
                    "intercept": self.server.model_weights["intercept"] + np.random.randn(*self.server.model_weights["intercept"].shape) * 0.01,
                }
                self._current_round_client_updates.append(local_update)
                self._current_round_sample_counts.append(client.local_samples)
                self._calculate_client_local_accuracy(client)
                print(
                    f"  Client {client.client_id}: {client.local_samples} samples, "
                    f"epochs={client.local_epochs}, battery={client.battery_level}%, "
                    f"local_accuracy={client.local_model_accuracy:.3f}"
                )

            report.success = True
            report.participating_client_ids = [client.client_id for client in self.server.selected_clients]
            report.trained_client_ids = [client.client_id for client in self._current_round_trained_clients]
            report.selected_count = len(self._current_round_client_updates)
            report.trained_count = len(self._current_round_client_updates)
            report.total_training_samples = sum(self._current_round_sample_counts)
            report.message = f"{len(self._current_round_client_updates)} client training tamamladı. Toplam {report.total_training_samples} sample aggregasyona gidiyor."
            print(f"\n✓ Local Training Tamamlandı:")
            print(f"  - Training yapan: {len(self._current_round_client_updates)}")
            print(f"  - Toplam samples: {report.total_training_samples}")
            self.current_phase = FLPhase.Aggregation
        except Exception as exc:
            report.success = False
            report.message = f"Local training hatası: {exc}"

    def _execute_phase_aggregation(self, report: RoundPhaseReport) -> None:
        try:
            print("\n--- Aggregation (FedAvg) Phase ---")
            if not self._current_round_client_updates:
                self.current_phase = FLPhase.ModelEvaluation
                report.success = True
                report.message = "Aggregasyon için client update yok."
                return

            aggregated = self.server.aggregate_weights(self._current_round_client_updates, self._current_round_sample_counts)
            self.server.update_model(aggregated)

            print("\n  Client Local Accuracies:")
            for client in self._current_round_trained_clients:
                print(f"    Client {client.client_id}: {client.local_model_accuracy:.3f} ({client.local_model_accuracy * 100:.1f}%)")

            report.success = True
            report.aggregated_samples = sum(self._current_round_sample_counts)
            report.message = f"Weights aggregated. {len(self._current_round_client_updates)} client'ın {report.aggregated_samples} sample'ı server modelinde merge edildi."

            print(f"\n✓ Aggregation Tamamlandı:")
            print(f"  - {len(self._current_round_client_updates)} client update merged")
            print(f"  - Sample weighted average: {report.aggregated_samples}")
            self.current_phase = FLPhase.ModelEvaluation
        except Exception as exc:
            report.success = False
            report.message = f"Aggregation hatası: {exc}"

    def _execute_phase_model_evaluation(self, report: RoundPhaseReport) -> None:
        try:
            print("\n--- Model Evaluation Phase ---")
            self._evaluate_model(self._current_round_trained_clients)
            report.success = True
            report.aggregated_accuracy = self.server.last_model_accuracy
            report.message = f"Model accuracy evaluated: {self.server.last_model_accuracy:.3f} ({self.server.last_model_accuracy * 100:.1f}%)"
            self.current_phase = FLPhase.RoundComplete
        except Exception as exc:
            report.success = False
            report.message = f"Model evaluation hatası: {exc}"

    def _execute_phase_round_complete(self, report: RoundPhaseReport) -> None:
        try:
            print("\n--- Round Complete Phase ---")

            for client in self.server.selected_clients:
                client.apply_round_outcome(participated=True)

            for client in self.server.active_clients:
                if client not in self.server.selected_clients:
                    client.apply_round_outcome(participated=False)

            round_info = {
                "round": self.server.round_number,
                "active_clients": len(self.server.active_clients),
                "selected_count": len(self.server.selected_clients),
                "trained_count": len(self._current_round_trained_clients),
                "total_samples": sum(self._current_round_sample_counts),
                "selected_client_ids": [client.client_id for client in self.server.selected_clients],
                "trained_client_ids": [client.client_id for client in self._current_round_trained_clients],
                "model_accuracy": self.server.last_model_accuracy,
            }
            self.server.aggregation_history.append(round_info)

            self._current_round_client_updates.clear()
            self._current_round_sample_counts.clear()
            self._current_round_trained_clients.clear()
            self._selection_rate_override = None
            self.current_phase = FLPhase.Idle

            report.success = True
            report.message = f"Round {self.server.round_number} tamamlandı. Sonraki round için hazır."

            print(f"\n✓ Round {self.server.round_number} Summary:")
            print(f"  - Active clients: {len(self.server.active_clients)}")
            print(f"  - Selected: {len(self.server.selected_clients)}")
            print(f"  - Total samples: {round_info['total_samples']}")
            print(f"  - Model Accuracy: {self.server.last_model_accuracy:.3f}")
            print(f"\n  Client States:")
            for client in self._current_round_trained_clients:
                print(
                    f"    Client {client.client_id}: "
                    f"local_acc={client.local_model_accuracy:.3f}, "
                    f"battery={client.battery_level}%, "
                    f"fatigue={client.fatigue:.2f}, "
                    f"streak={client.participation_streak}"
                )
        except Exception as exc:
            report.success = False
            report.message = f"Round complete hatası: {exc}"

    def _calculate_weight_magnitude(self) -> float:
        if self.server is None or not self.server.model_weights:
            return 0.0

        coef = self.server.model_weights["coef"]
        intercept = self.server.model_weights["intercept"]
        return float(np.sqrt(np.sum(np.square(coef)) + np.sum(np.square(intercept))))

    def _calculate_label_diversity_bonus(self, client: Client) -> float:
        if not client.label_histogram:
            return 0.10
        return min(len(client.label_histogram) / 10.0, 1.0) * 0.20

    def _calculate_client_local_accuracy(self, client: Client) -> None:
        base_accuracy = 0.5
        weight_magnitude = self._calculate_weight_magnitude()
        num_weights = int(np.size(self.server.model_weights["coef"])) if self.server and self.server.model_weights else 1
        convergence_bonus = min(weight_magnitude / (num_weights * 0.5), 1.0) * 0.30
        data_quality_bonus = client.data_quality * 0.25
        diversity_bonus = self._calculate_label_diversity_bonus(client)
        sample_bonus = min(client.local_samples / 200.0, 1.0) * 0.15
        fatigue_penalty = client.fatigue * 0.10
        variance = (self.server.rng.random() - 0.5) * 0.02

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
        if self.server is None:
            return

        if not tested_clients:
            self.server.last_model_accuracy = max(self.config.min_accuracy, self.server.last_model_accuracy - 0.02)
            print(f"  ⚠ No training this round. Accuracy penalty: {self.server.last_model_accuracy:.3f} ({self.server.last_model_accuracy * 100:.1f}%)")
            return

        weight_magnitude = self._calculate_weight_magnitude()
        num_weights = int(np.size(self.server.model_weights["coef"])) if self.server.model_weights else 1
        initial_magnitude = num_weights * 0.05
        convergence_bonus = min((weight_magnitude - initial_magnitude) / (num_weights * 0.5), 0.35)
        convergence_bonus = max(0.0, convergence_bonus)

        avg_data_quality = float(np.mean([client.data_quality for client in tested_clients]))
        avg_engagement = float(np.mean([client.engagement for client in tested_clients]))
        quality_bonus = avg_data_quality * 0.12 + avg_engagement * 0.08
        round_bonus = min(self.server.round_number * 0.025, 0.15)
        participation_bonus = min(len(tested_clients) / 10.0 * 0.1, 0.1)

        self.server.last_model_accuracy = self.config.min_accuracy + convergence_bonus + quality_bonus + round_bonus + participation_bonus
        self.server.last_model_accuracy += (self.server.rng.random() - 0.5) * 0.02
        self.server.last_model_accuracy = max(self.config.min_accuracy, min(self.server.last_model_accuracy, self.config.max_accuracy))

        print(
            f"  ✓ Model Accuracy: {self.server.last_model_accuracy:.3f} ({self.server.last_model_accuracy * 100:.1f}%) "
            f"[conv={convergence_bonus:.3f} + qual={quality_bonus:.3f} + round={round_bonus:.3f} + part={participation_bonus:.3f}]"
        )

    def build_comparison_summary(self) -> dict:
        if self.server is None:
            return {
                "config": asdict(self.config) if self.config is not None else {},
                "rounds": [],
                "final_clients": [],
                "final_model_accuracy": 0.0,
            }

        return {
            "config": asdict(self.config),
            "rounds": self.server.aggregation_history,
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
                for client in self.server.all_clients
            ],
            "final_model_accuracy": self.server.last_model_accuracy,
        }

    def export_comparison_summary(self, path: str = "outputs/flower_comparison_summary.json") -> str:
        summary = self.build_comparison_summary()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(summary, handle, ensure_ascii=False, indent=2)
        return path