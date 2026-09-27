from dataclasses import dataclass


@dataclass
class SimulationConfig:
    # Random seed
    seed: int = 42

    # Scenario mode
    # 0 = base FL, 1 = static incentive, 2 = dynamic gamified FL
    mode: int = 2

    # Model
    input_dim: int = 64
    num_classes: int = 10
    min_accuracy: float = 0.50
    max_accuracy: float = 0.95
    accuracy_reward_scale: float = 10.0

    # Selection / environment
    selection_rate: float = 0.6
    weak_connection_skip_prob: float = 0.1
    low_battery_threshold: int = 20
    low_battery_pass_prob: float = 0.1

    # Reward parameters
    base_reward_offset: int = 7
    static_reward_points: int = 8
    engagement_threshold: float = 0.65
    engagement_bonus: int = 3
    weak_connectivity_bonus: int = 5
    previous_participation_bonus: int = 2
    max_reward: int = 40
    reward_bonus_cap: float = 0.40

    # Differential Privacy (DP-FedAvg: güncelleme kırpma + Gauss gürültüsü, bkz. privacy.py)
    dp_enabled: bool = True
    dp_clip_norm: float = 0.25
    dp_noise_multiplier: float = 1.0
    dp_delta: float = 1e-5

    # Simulation runtime
    rounds: int = 10

    # Other tunables
    battery_drain_per_round: int = 6
    battery_recharge_idle: int = 3

    def __post_init__(self):
        # validate simple invariants
        if self.mode not in (0, 1, 2):
            self.mode = 2
        if self.max_reward < 0:
            self.max_reward = 40
        if self.dp_clip_norm <= 0:
            self.dp_clip_norm = 0.25
        if self.dp_noise_multiplier < 0:
            self.dp_noise_multiplier = 1.0
        if self.min_accuracy > self.max_accuracy:
            self.min_accuracy = 0.50
            self.max_accuracy = 0.95
