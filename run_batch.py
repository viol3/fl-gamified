"""Run a scenario N times on the SAME fixed client roster, varying only the round/decision
RNG seed, and export one summary per run.

The client roster is loaded fresh (pristine round-0 state) from a JSON file for every run,
so all trials start from identical client populations. Only the Server's RNG stream (which
drives round-to-round selection and participation randomness) differs between runs. This
isolates the effect of stochastic participation decisions from population variance, which is
what a fair Scenario 0 vs 1 vs 2 comparison needs.

An index file records the seed -> output path -> final accuracy mapping so results can be
aggregated for the thesis report.
"""
import argparse
import json
import os

from src.fl_gamified.client import load_clients_from_json
from src.fl_gamified.server import Server
from src.fl_gamified.config import SimulationConfig

MODE_TAGS = {0: "standard", 1: "static", 2: "dynamic"}


def run_single(mode: int, seed: int, run_index: int, rounds: int, selection_rate: float, out_dir: str, roster_path: str, config_overrides: dict) -> dict:
    config = SimulationConfig(seed=seed, rounds=rounds, mode=mode, **config_overrides)
    server = Server(config=config)
    server.initialize_model(input_dim=config.input_dim, num_classes=config.num_classes)

    clients = load_clients_from_json(roster_path)
    server.register_clients(clients)

    for _ in range(config.rounds):
        server.simulate_round(selection_rate=selection_rate)

    mode_tag = MODE_TAGS[mode]
    summary_path = os.path.join(out_dir, f"flower_comparison_summary_{mode_tag}_run{run_index:02d}_seed{seed}.json")
    server.export_comparison_summary(summary_path)

    total_selected = sum(r["selected_count"] for r in server.aggregation_history)
    return {
        "run": run_index,
        "seed": seed,
        "mode": mode,
        "final_accuracy": server.last_model_accuracy,
        "total_selected": total_selected,
        "dp_epsilon": server.dp_epsilon(),
        "path": summary_path,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run N repeated trials of a scenario on a fixed roster, exporting one summary per run.")
    parser.add_argument("--mode", type=int, default=0, choices=[0, 1, 2], help="0=base, 1=static, 2=dynamic")
    parser.add_argument("--runs", type=int, default=10, help="Number of independent trials")
    parser.add_argument("--rounds", type=int, default=100, help="Rounds per trial")
    parser.add_argument("--selection-rate", type=float, default=0.6, help="Selection rate per round")
    parser.add_argument("--seed-start", type=int, default=101, help="First decision-RNG seed; increments by 1 per run")
    parser.add_argument("--roster", default="outputs/initial_clients.json", help="Fixed client roster JSON (same clients used in every run)")
    parser.add_argument("--out-dir", default="outputs/Flower", help="Base output directory; results are written to <out-dir>/<mode_tag>/ so scenarios never mix")
    parser.add_argument("--dp", action=argparse.BooleanOptionalAction, default=None, help="Enable/disable DP-FedAvg (default: config.py)")
    parser.add_argument("--dp-noise", type=float, default=None, help="DP noise multiplier (sigma)")
    parser.add_argument("--dp-clip", type=float, default=None, help="DP L2 clipping norm (C)")
    parser.add_argument("--static-reward", type=int, default=None, help="Mode 1 fixed reward points (default: config.py static_reward_points)")
    args = parser.parse_args()

    config_overrides = {}
    if args.dp is not None:
        config_overrides["dp_enabled"] = args.dp
    if args.dp_noise is not None:
        config_overrides["dp_noise_multiplier"] = args.dp_noise
    if args.dp_clip is not None:
        config_overrides["dp_clip_norm"] = args.dp_clip
    if args.static_reward is not None:
        config_overrides["static_reward_points"] = args.static_reward
    dp_config = SimulationConfig(**config_overrides)

    if not os.path.exists(args.roster):
        raise SystemExit(f"Roster file not found: {args.roster}. Generate a fixed roster first.")

    mode_out_dir = os.path.join(args.out_dir, MODE_TAGS[args.mode])
    os.makedirs(mode_out_dir, exist_ok=True)

    results = []
    print(f"Running {args.runs} trials | mode={args.mode} ({MODE_TAGS[args.mode]}) | rounds={args.rounds} | roster={args.roster}")
    print(f"Decision-RNG seeds: {args.seed_start}..{args.seed_start + args.runs - 1} (client roster fixed across all runs)")
    print(f"Output dir: {mode_out_dir}")
    print(f"Static reward points: {dp_config.static_reward_points} (used only in mode 1)")
    print(f"DP: enabled={dp_config.dp_enabled} | clip={dp_config.dp_clip_norm} | sigma={dp_config.dp_noise_multiplier} | delta={dp_config.dp_delta}")
    print("-" * 90)
    for i in range(1, args.runs + 1):
        seed = args.seed_start + i - 1
        result = run_single(
            mode=args.mode,
            seed=seed,
            run_index=i,
            rounds=args.rounds,
            selection_rate=args.selection_rate,
            out_dir=mode_out_dir,
            roster_path=args.roster,
            config_overrides=config_overrides,
        )
        results.append(result)
        print(f"Run {i:2d} | seed={seed:4d} | final_accuracy={result['final_accuracy']:.4f} | selected_total={result['total_selected']:4d} | eps={result['dp_epsilon']:.2f} | {result['path']}")

    accuracies = [r["final_accuracy"] for r in results]
    mean_acc = sum(accuracies) / len(accuracies)
    variance = sum((a - mean_acc) ** 2 for a in accuracies) / len(accuracies)
    std_acc = variance ** 0.5

    index_path = os.path.join(mode_out_dir, f"batch_index_{MODE_TAGS[args.mode]}.json")
    with open(index_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "mode": args.mode,
                "mode_tag": MODE_TAGS[args.mode],
                "runs": args.runs,
                "rounds": args.rounds,
                "selection_rate": args.selection_rate,
                "roster_path": args.roster,
                "dp": {
                    "enabled": dp_config.dp_enabled,
                    "clip_norm": dp_config.dp_clip_norm,
                    "noise_multiplier": dp_config.dp_noise_multiplier,
                    "delta": dp_config.dp_delta,
                },
                "decision_seeds": [r["seed"] for r in results],
                "results": results,
                "final_accuracy_mean": mean_acc,
                "final_accuracy_std": std_acc,
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )

    print("-" * 90)
    print(f"Final accuracy across {args.runs} runs: mean={mean_acc:.4f}, std={std_acc:.4f}")
    print(f"Batch index saved to: {index_path}")


if __name__ == "__main__":
    main()
