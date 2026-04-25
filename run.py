from __future__ import annotations

import argparse

from src.fl_gamified.config import ExperimentConfig, Scenario
from src.fl_gamified.simulation import run_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Gamified Federated Learning Thesis Starter")
    parser.add_argument("--scenario", type=str, default="gamified", choices=["baseline", "static", "gamified"])
    parser.add_argument("--rounds", type=int, default=15)
    parser.add_argument("--clients", type=int, default=20)
    parser.add_argument("--fraction-fit", type=float, default=0.4)
    parser.add_argument("--min-fit-clients", type=int, default=4)
    parser.add_argument("--local-epochs", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--alpha", type=float, default=0.5, help="Dirichlet alpha for heterogeneity")
    parser.add_argument("--unity-events", type=str, default="outputs/unity_events.jsonl")

    args = parser.parse_args()

    config = ExperimentConfig(
        num_clients=args.clients,
        num_rounds=args.rounds,
        fraction_fit=args.fraction_fit,
        min_fit_clients=args.min_fit_clients,
        min_available_clients=args.clients,
        local_epochs=args.local_epochs,
        random_seed=args.seed,
        dirichlet_alpha=args.alpha,
        scenario=Scenario(args.scenario),
        unity_event_path=args.unity_events,
    )

    run_experiment(config)


if __name__ == "__main__":
    main()
