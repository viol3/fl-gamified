from dataclasses import dataclass, field
import numpy as np
import random
from typing import Optional
from .config import SimulationConfig
from client import Client


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
    rng: Optional[random.Random] = field(default=None, repr=False)

    def __post_init__(self):
        if self.rng is None:
            self.rng = random.Random(self.config.seed)
    
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
    
    def add_clients(self, new_clients: list[Client]):
        """Yeni clientları mid-simulation'da ekle (örn. Round 3'de)."""
        for client in new_clients:
            if client not in self.all_clients:
                self.all_clients.append(client)
                self.active_clients.append(client)
                print(f"  + Added Client {client.client_id} (battery={client.battery_level}%, engagement={client.engagement:.2f})")
    
    def remove_clients(self, client_ids: list[int]):
        """Belirli clientları aktif listeden kaldır (ayrılış, disconnect, vb.)."""
        for client_id in client_ids:
            self.active_clients = [c for c in self.active_clients if c.client_id != client_id]
            print(f"  - Removed Client {client_id} from active list")
    
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
                if self.rng.random() >= self.config.weak_connection_skip_prob:
                    connection_ok = False

            battery_ok = True
            if client.battery_level < self.config.low_battery_threshold:
                if self.rng.random() > self.config.low_battery_pass_prob:
                    battery_ok = False

            if not (connection_ok and battery_ok):
                continue

            # Reward hesapla
            reward_offer = self._compute_reward_offer(client)

            # Client'a katılma kararı soralım
            participates, details = client.decide_participation(
                reward_points=reward_offer, 
                rng=self.rng
            )

            if participates:
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

    def simulate_round(self, selection_rate: float = 0.6) -> dict:
        """Tek bir FL round'ını simulate et."""
        self.round_number += 1
        
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
        
        # Aggregasyon
        if client_updates:
            aggregated = self.aggregate_weights(client_updates, sample_counts)
            self.update_model(aggregated)
        
        # History'e kaydet
        round_info = {
            'round': self.round_number,
            'active_clients': len(self.active_clients),
            'selected_count': len(selected),
            'total_samples': sum(sample_counts) if sample_counts else 0,
            'selected_client_ids': [c.client_id for c in selected],
        }
        self.aggregation_history.append(round_info)
        
        return round_info

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
