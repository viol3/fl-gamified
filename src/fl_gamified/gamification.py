from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .config import Scenario


@dataclass
class GamificationEngine:
    scenario: Scenario
    points: Dict[str, float] = field(default_factory=dict)
    streaks: Dict[str, int] = field(default_factory=dict)

    def award_points(self, client_id: str, metrics: dict) -> float:
        if self.scenario == Scenario.BASELINE:
            points = 0.0
        elif self.scenario == Scenario.STATIC:
            points = 10.0
        else:
            acc = float(metrics.get("train_accuracy", 0.0))
            examples = float(metrics.get("num_examples", 1.0))
            points = 5.0 + 20.0 * acc + min(15.0, examples / 20.0)

        self.points[client_id] = self.points.get(client_id, 0.0) + points
        if points > 0:
            self.streaks[client_id] = self.streaks.get(client_id, 0) + 1
        else:
            self.streaks[client_id] = 0
        return points

    def get_level(self, client_id: str) -> int:
        p = self.points.get(client_id, 0.0)
        if p >= 300:
            return 4
        if p >= 200:
            return 3
        if p >= 100:
            return 2
        if p >= 40:
            return 1
        return 0

    def participation_boost(self, client_id: str) -> float:
        if self.scenario == Scenario.BASELINE:
            return 0.0
        if self.scenario == Scenario.STATIC:
            return 0.05
        level = self.get_level(client_id)
        streak = self.streaks.get(client_id, 0)
        return min(0.22, 0.03 * level + 0.01 * min(streak, 5))

    def leaderboard(self, top_k: int = 10) -> List[Tuple[str, float]]:
        ranked = sorted(self.points.items(), key=lambda item: item[1], reverse=True)
        return ranked[:top_k]
