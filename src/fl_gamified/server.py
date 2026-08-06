from dataclasses import asdict, dataclass, field
import json
import os
import numpy as np
import random
from typing import Optional
from .config import SimulationConfig
from .logger import EventLogger
from .client import Client


@dataclass
class Server:
    """Federated Learning sunucusu - global modeli ve client'ları yönetir."""
    
    all_clients: list[Client] = field(default_factory=list)
    active_clients: list[Client] = field(default_factory=list)  # Bu roundda aktif clientlar
    config: SimulationConfig = field(default_factory=SimulationConfig)
    model_weights: dict = field(default_factory=dict)
    selected_clients: list[Client] = field(default_factory=list)
    round_number: int = 0
    aggregation_history: list[dict] = field(default_factory=list)
    last_model_accuracy: float = 0.5
    rng: Optional[random.Random] = field(default=None, repr=False)
    logger: Optional[EventLogger] = field(default=None, repr=False)

    def __post_init__(self):
        if self.rng is None:
            self.rng = random.Random(self.config.seed)

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
        """Model ağırlıklarını initialize et (sklearn LogisticRegression için)."""
        self.model_weights = {
            'coef': np.random.randn(num_classes, input_dim) * 0.01,
            'intercept': np.zeros(num_classes),
        }
        print(f"✓ Model initialized | coef shape: {self.model_weights['coef'].shape}")

    def register_clients(self, clients: list[Client]):
        """Tüm client'ları server'a kaydet. İlk round'da hepsi aktif olur."""
        self.all_clients.extend(clients)
        self.active_clients.extend(clients)
        print(f"✓ Registered {len(clients)} new clients | Total: {len(self.all_clients)} | Active: {len(self.active_clients)}")
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
        """Yeni clientları mid-simulation'da ekle (örn. Round 3'de)."""
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
        """Belirli clientları aktif listeden kaldır (ayrılış, disconnect, vb.)."""
        for client_id in client_ids:
            self.active_clients = [c for c in self.active_clients if c.client_id != client_id]
            print(f"  - Removed Client {client_id} from active list")
            if self.logger:
                self.logger.log_event("client_left", {"round": self.round_number, "client_id": client_id})
    
    def get_active_clients_summary(self) -> str:
        """Aktif clientların durumunu özet olarak göster."""
        if not self.active_clients:
            return "No active clients"
        
        client_ids = [c.client_id for c in self.active_clients]
        avg_battery = np.mean([c.battery_level for c in self.active_clients])
        avg_engagement = np.mean([c.engagement for c in self.active_clients])
        return f"Active: {client_ids} | Avg Battery: {avg_battery:.1f}% | Avg Engagement: {avg_engagement:.2f}"

    def select_clients(self, selection_rate: float = 0.6) -> list[Client]:
        """
        Client seçimi - tüm active clientlara reward teklif et, 
        onların katılım kararını sor.
        
        - Bağlantı: 'weak' olanlar %50 ihtimalle, diğerleri %100
        - Batarya: %50 altındaysa %30 ihtimalle
        - Reward: Temel reward + katılımcı özellikleri
        """
        self.selected_clients = []
        
        for client in self.active_clients:
            # Temel uygunluk kontrolü
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
                if self.logger:
                    self.logger.log_event("client_skipped", {
                        "round": self.round_number,
                        "client_id": client.client_id,
                        "connection_ok": connection_ok,
                        "battery_ok": battery_ok,
                    })
                continue

            # Reward hesapla
            reward_offer = self._compute_reward_offer(client)

            # Client'a katılma kararı soralım
            participates, details = client.decide_participation(
                reward_points=reward_offer, 
                rng=self.rng
            )

            # simulate submission latency for later replay (seconds)
            simulated_latency = float(self.rng.uniform(0.2, 5.0))

            # Detailed per-client decision log
            if self.logger:
                self.logger.log_event("client_decision", {
                    "round": self.round_number,
                    **self._client_ref(client),
                    "connection_ok": connection_ok,
                    "battery_ok": battery_ok,
                    "reward_offer": reward_offer,
                    "decision": details,
                    "simulated_submission_latency": simulated_latency,
                })

            if participates:
                if self.rng.random() < selection_rate:
                    self.selected_clients.append(client)
        
        return self.selected_clients
    
    def _compute_reward_offer(self, client: Client) -> int:
        """
        Client'a teklif etmek için reward miktarını hesapla.
        
        - Base: round number + 4
        - Low engagement: +3
        - Weak connectivity: +2
        - Didn't participate last round: +2
        - Max: 15
        """
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
        Federated Averaging (FedAvg) - ağırlıklı ortalamayla birleştir.
        
        Args:
            client_updates: Her client'ın güncellenen ağırlıkları
            client_sample_counts: Her client'ın örnek sayısı (ağırlıklandırma için)
        """
        total_samples = sum(client_sample_counts)
        
        # Ağırlıkları sıfırla
        aggregated_weights = {
            'coef': np.zeros_like(self.model_weights['coef']),
            'intercept': np.zeros_like(self.model_weights['intercept']),
        }
        
        # Ağırlıklı ortalamayla birleştir
        for client_update, sample_count in zip(client_updates, client_sample_counts):
            weight = sample_count / total_samples
            aggregated_weights['coef'] += weight * client_update['coef']
            aggregated_weights['intercept'] += weight * client_update['intercept']
        
        return aggregated_weights

    def update_model(self, aggregated_weights: dict, learning_rate: float = 1.0):
        """Global modeli yeni ağırlıklarla güncelle."""
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
        """Tek bir FL round'ını simulate et."""
        self.round_number += 1
        if self.logger:
            self.logger.log_event("round_start", {
                "round": self.round_number,
                "active_client_ids": [c.client_id for c in self.active_clients],
                "active_count": len(self.active_clients),
            })
        
        # Önceki roundtan katılanları apply_round_outcome ile güncelle
        for client in self.selected_clients:
            client.apply_round_outcome(participated=True)
        
        # Katılmayan active clientları güncelle
        for client in self.active_clients:
            if client not in self.selected_clients:
                client.apply_round_outcome(participated=False)
        
        # Bu roundda katılacak clientları seç
        selected = self.select_clients(selection_rate or self.config.selection_rate)
        
        # Dummy: Her client lokal güncellemeler yapıyor
        client_updates = []
        sample_counts = []
        
        for client in selected:
            # Basit simülasyon: her client ağırlıklara küçük noise ekliyor
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
        
        # Aggregasyon
        if client_updates:
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
        
        # History'e kaydet
        round_info = {
            'round': self.round_number,
            'active_clients': len(self.active_clients),
            'selected_count': len(selected),
            'trained_count': len(client_updates),
            'total_samples': sum(sample_counts) if sample_counts else 0,
            'selected_client_ids': [c.client_id for c in selected],
            'trained_client_ids': [c.client_id for c in selected],
            'model_accuracy': self.last_model_accuracy,
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
        }

    def export_comparison_summary(self, path: str = "outputs/flower_comparison_summary.json") -> str:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.build_comparison_summary(), handle, ensure_ascii=False, indent=2)
        return path

    def describe(self) -> str:
        """Server durumunu açıkla."""
        return (
            f"Server Round {self.round_number} | "
            f"total_clients: {len(self.all_clients)} | "
            f"active_clients: {len(self.active_clients)} | "
            f"selected_clients: {len(self.selected_clients)} | "
            f"model_shape: {self.model_weights['coef'].shape if self.model_weights else 'N/A'} | "
            f"aggregation_rounds: {len(self.aggregation_history)}"
        )
