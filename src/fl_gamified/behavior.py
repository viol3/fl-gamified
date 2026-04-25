from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass
class ClientBehaviorState:
    battery: float
    connectivity: float
    free_time: float
    engagement: float
    churned: bool = False

    @staticmethod
    def random_state(rng: random.Random) -> "ClientBehaviorState":
        return ClientBehaviorState(
            battery=rng.uniform(0.35, 1.0),
            connectivity=rng.uniform(0.3, 1.0),
            free_time=rng.uniform(0.25, 1.0),
            engagement=rng.uniform(0.3, 0.9),
        )

    def participation_probability(self, boost: float = 0.0) -> float:
        if self.churned:
            return 0.0
        base = 0.15 + 0.25 * self.battery + 0.25 * self.connectivity + 0.2 * self.free_time + 0.15 * self.engagement
        p = max(0.02, min(0.98, base + boost))
        return p

    def update_after_round(self, was_selected: bool, local_loss: float | None, reward_points: float) -> None:
        if self.churned:
            return

        if was_selected:
            self.battery = max(0.0, self.battery - random.uniform(0.02, 0.08))
            self.free_time = max(0.0, self.free_time - random.uniform(0.01, 0.05))
            if local_loss is not None:
                self.engagement += 0.03 if local_loss < 1.0 else -0.02
            self.engagement += min(0.06, reward_points / 500.0)
        else:
            self.battery = min(1.0, self.battery + random.uniform(0.01, 0.04))
            self.free_time = min(1.0, self.free_time + random.uniform(0.0, 0.03))
            self.engagement -= 0.01

        self.connectivity = min(1.0, max(0.0, self.connectivity + random.uniform(-0.05, 0.05)))
        self.engagement = min(1.0, max(0.0, self.engagement))

        churn_score = 0.7 * (1.0 - self.engagement) + 0.2 * (1.0 - self.battery) + 0.1 * (1.0 - self.connectivity)
        churn_probability = max(0.0, min(0.45, churn_score - 0.4))
        if random.random() < churn_probability:
            self.churned = True
