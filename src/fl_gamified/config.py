from dataclasses import dataclass
from enum import Enum


class Scenario(str, Enum):
    BASELINE = "baseline"
    STATIC = "static"
    GAMIFIED = "gamified"


@dataclass
class ExperimentConfig:
    num_clients: int = 20
    num_rounds: int = 15
    fraction_fit: float = 0.4
    min_fit_clients: int = 4
    min_available_clients: int = 20
    local_epochs: int = 1
    random_seed: int = 42
    dirichlet_alpha: float = 0.5
    scenario: Scenario = Scenario.GAMIFIED
    unity_event_path: str = "outputs/unity_events.jsonl"
