import json
import os

from src.fl_gamified.client import build_random_clients
from src.fl_gamified.server import Server
from src.fl_gamified.config import SimulationConfig
from src.fl_gamified.logger import EventLogger


def main() -> None:
    print("=" * 90)
    print("Scenario: Digits Classification - Federated Learning with Gamified Incentives")
    print("=" * 90)
    print()

    os.makedirs("outputs", exist_ok=True)

    # Server'ı initialize et
    config = SimulationConfig(seed=42, rounds=100)
    logger = EventLogger(path="outputs/simulation_events.jsonl", mode="w")
    server = Server(config=config, logger=logger)
    server.initialize_model(input_dim=config.input_dim, num_classes=config.num_classes)
    print()

    # İlk 10 rastgele client'i register et
    initial_clients = build_random_clients(count=10)
    server.register_clients(initial_clients)
    print("\n--- Initial Clients ---")
    for client in initial_clients:
        print(f"  {client.describe()}")

    initial_clients_path = "outputs/initial_clients.json"
    with open(initial_clients_path, "w", encoding="utf-8") as handle:
        json.dump([client.to_dict() for client in initial_clients], handle, ensure_ascii=False, indent=2)
    print(f"\nInitial client config saved to: {initial_clients_path}")

    # 100 round simülasyonu
    print("\n" + "=" * 90)
    print("Simulation: 100 Federated Learning Rounds")
    print("=" * 90)

    for round_num in range(1, config.rounds + 1):
        print(f"\n{'─' * 90}")
        print(f"ROUND {round_num}")
        print(f"{'─' * 90}")

        # State bilgisi göster
        print(f"\nServer: {server.describe()}")
        print(f"Status: {server.get_active_clients_summary()}")

        # Round'ı simüle et
        print("\n--- Client Participation Decisions ---")
        round_result = server.simulate_round(selection_rate=0.6)

        # Seçilen clientları göster
        print(f"\n✓ Round {round_num} Aggregation:")
        print(f"  - Active Clients: {round_result['active_clients']}")
        print(f"  - Selected for training: {round_result['selected_count']}")
        print(f"  - Selected Client IDs: {round_result['selected_client_ids']}")
        print(f"  - Total samples aggregated: {round_result['total_samples']}")

        # Seçilen clientların detaylarını göster
        print("\n  Details:")
        for client in server.selected_clients:
            reward = server._compute_reward_offer(client)
            participates, details = client.decide_participation(reward_points=reward, rng=server.rng)
            print(
                f"    Client {client.client_id} | "
                f"reward={reward:2d} | "
                f"decision={details['reason']:12s} | "
                f"score={details['score']:.2f} | "
                f"streak={client.participation_streak:2d} | "
                f"battery={client.battery_level:3d}% | "
                f"fatigue={client.fatigue:.2f}"
            )

    # Final states
    print("\n" + "=" * 90)
    print("Final Client States")
    print("=" * 90)
    for client in server.all_clients:
        print(f"  {client.describe()}")

    # Aggregation history
    print("\n" + "=" * 90)
    print("Aggregation History")
    print("=" * 90)
    for entry in server.aggregation_history:
        print(f"  Round {entry['round']}: "
              f"active={entry['active_clients']}, "
              f"selected={entry['selected_count']}, "
              f"samples={entry['total_samples']}, "
              f"ids={entry['selected_client_ids']}")

    # Log final simulation summary and per-client summary for replay
    if logger:
        per_client_summary = [
            {
                "client_id": c.client_id,
                "total_participations": c.total_participations,
                "final_battery": c.battery_level,
                "final_engagement": c.engagement,
            }
            for c in server.all_clients
        ]
        logger.log_event("simulation_end", {
            "rounds": config.rounds,
            "aggregation_history": server.aggregation_history,
            "per_client_summary": per_client_summary,
            "initial_clients_path": initial_clients_path,
            "comparison_summary_path": summary_path,
        })
        logger.close()

    #print all clients local accuracy and server's global accuracy
    print("\n" + "=" * 90)
    print("Final Accuracy Summary")
    print("=" * 90)
    for client in server.all_clients:
        print(f"  Client {client.client_id}: Local Accuracy = {client.local_model_accuracy:.4f}")

    summary_path = server.export_comparison_summary("outputs/flower_comparison_summary.json")
    print(f"\nComparison summary saved to: {summary_path}")

    print("\n" + "=" * 90)
    print(f"Simulation Complete ✓")
    print("=" * 90)


if __name__ == "__main__":
    main()

