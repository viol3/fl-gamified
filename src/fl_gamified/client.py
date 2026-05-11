from dataclasses import dataclass, field
import random
from typing import Optional


@dataclass
class Client:
    client_id: int
    local_samples: int
    digit_focus: str
    cpu_power: float
    data_quality: float
    storage_capacity_gb: float
    battery_level: int
    connectivity: str
    engagement: float
    local_epochs: int = 1
    label_histogram: dict[int, int] = field(default_factory=dict)
    participation_streak: int = 0
    total_participations: int = 0
    previous_round_participated: bool = False
    fatigue: float = 0.0

    def _connectivity_drop_chance(self) -> float:
        if self.connectivity == "weak":
            return 0.35
        if self.connectivity == "medium":
            return 0.15
        return 0.05

    def _base_participation_score(self) -> float:
        return (
            0.45 * self.engagement
            + 0.25 * (self.battery_level / 100)
            + 0.15 * min(self.cpu_power / 4.0, 1.0)
            + 0.15 * self.data_quality
        )

    def decide_participation(
        self,
        reward_points: int = 0,
        rng: Optional[random.Random] = None,
    ) -> tuple[bool, dict[str, float | str]]:
        if rng is None:
            rng = random.Random()

        if self.battery_level < 20:
            return False, {
                "reason": "low_battery",
                "score": 0.0,
                "fatigue_penalty": 0.0,
                "reward_bonus": 0.0,
                "drop_chance": self._connectivity_drop_chance(),
            }

        drop_chance = self._connectivity_drop_chance()
        dropped = rng.random() < drop_chance
        if dropped:
            return False, {
                "reason": "connection_drop",
                "score": 0.0,
                "fatigue_penalty": 0.0,
                "reward_bonus": 0.0,
                "drop_chance": drop_chance,
            }

        fatigue_penalty = min(0.05 * self.participation_streak + 0.5 * self.fatigue, 0.35)
        reward_bonus = min(reward_points / 100.0, 0.25)

        score = self._base_participation_score() - fatigue_penalty + reward_bonus
        score = max(0.0, min(score, 0.98))

        participates = rng.random() < score
        reason = "accepted" if participates else "declined"

        return participates, {
            "reason": reason,
            "score": score,
            "fatigue_penalty": fatigue_penalty,
            "reward_bonus": reward_bonus,
            "drop_chance": drop_chance,
        }

    def apply_round_outcome(self, participated: bool) -> None:
        if participated:
            self.total_participations += 1
            self.participation_streak += 1
            self.fatigue = min(self.fatigue + 0.08, 1.0)
            self.battery_level = max(0, self.battery_level - 6)
        else:
            self.participation_streak = 0
            self.fatigue = max(self.fatigue - 0.12, 0.0)
            self.battery_level = min(100, self.battery_level + 3)

        self.previous_round_participated = participated

    def describe(self) -> str:
        histogram_text = ", ".join(f"{digit}:{count}" for digit, count in self.label_histogram.items())
        if not histogram_text:
            histogram_text = "none"

        return (
            f"Client {self.client_id} | "
            f"task=digits-classification | "
            f"samples={self.local_samples} | "
            f"focus={self.digit_focus} | "
            f"cpu={self.cpu_power:.1f} | "
            f"data_quality={self.data_quality:.2f} | "
            f"storage={self.storage_capacity_gb:.2f}GB | "
            f"battery={self.battery_level}% | "
            f"connectivity={self.connectivity} | "
            f"engagement={self.engagement:.2f} | "
            f"local_epochs={self.local_epochs} | "
            f"streak={self.participation_streak} | "
            f"fatigue={self.fatigue:.2f} | "
            f"labels={histogram_text}"
        )


def build_demo_clients() -> list[Client]:
    return [
        Client(
            client_id=1,
            local_samples=120,
            digit_focus="0/1/2",
            cpu_power=3.6,
            data_quality=0.91,
            storage_capacity_gb=0.25,
            battery_level=92,
            connectivity="strong",
            engagement=0.88,
            local_epochs=1,
            label_histogram={0: 46, 1: 38, 2: 36},
        ),
        Client(
            client_id=2,
            local_samples=95,
            digit_focus="3/4",
            cpu_power=2.4,
            data_quality=0.76,
            storage_capacity_gb=0.13,
            battery_level=67,
            connectivity="medium",
            engagement=0.73,
            local_epochs=2,
            label_histogram={3: 51, 4: 44},
        ),
        Client(
            client_id=3,
            local_samples=110,
            digit_focus="5/6",
            cpu_power=3.1,
            data_quality=0.84,
            storage_capacity_gb=0.19,
            battery_level=81,
            connectivity="strong",
            engagement=0.79,
            local_epochs=2,
            label_histogram={5: 58, 6: 52},
        ),
        Client(
            client_id=4,
            local_samples=78,
            digit_focus="7",
            cpu_power=1.8,
            data_quality=0.68,
            storage_capacity_gb=0.10,
            battery_level=54,
            connectivity="weak",
            engagement=0.61,
            local_epochs=1,
            label_histogram={7: 78},
        ),
        Client(
            client_id=5,
            local_samples=102,
            digit_focus="8/9",
            cpu_power=2.9,
            data_quality=0.88,
            storage_capacity_gb=0.16,
            battery_level=76,
            connectivity="medium",
            engagement=0.84,
            local_epochs=3,
            label_histogram={8: 49, 9: 53},
        ),
    ]
