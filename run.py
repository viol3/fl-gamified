import random

from src.fl_gamified.client import Client, build_demo_clients
from src.fl_gamified.server import Server
from src.fl_gamified.config import SimulationConfig


def main() -> None:
    print("=" * 90)
    print("Scenario: Digits Classification - Federated Learning with Gamified Incentives")
    print("=" * 90)
    print()

    # Server'ı initialize et
    config = SimulationConfig(seed=42, rounds=6)
    server = Server(config=config)
    server.initialize_model(input_dim=config.input_dim, num_classes=config.num_classes)
    print()

    # İlk 5 clienti register et
    initial_clients = build_demo_clients()
    server.register_clients(initial_clients)
    print("\n--- Initial Clients ---")
    for client in initial_clients:
        print(f"  {client.describe()}")

    # 6 round simülasyonu
    print("\n" + "=" * 90)
    print("Simulation: 6 Federated Learning Rounds")
    print("=" * 90)

    for round_num in range(1, 7):
        print(f"\n{'─' * 90}")
        print(f"ROUND {round_num}")
        print(f"{'─' * 90}")

        # ===== Scenario: Round 3'de yeni clientlar gelsin =====
        if round_num == 3:
            print("\n📌 [Event] Round 3: New clients are joining the network!")
            new_clients = [
                Client(
                    client_id=6,
                    local_samples=88,
                    digit_focus="0/1",
                    cpu_power=2.5,
                    data_quality=0.80,
                    storage_capacity_gb=0.15,
                    battery_level=85,
                    connectivity="strong",
                    engagement=0.77,
                    local_epochs=2,
                    label_histogram={0: 45, 1: 43},
                ),
                Client(
                    client_id=7,
                    local_samples=75,
                    digit_focus="9",
                    cpu_power=2.0,
                    data_quality=0.72,
                    storage_capacity_gb=0.12,
                    battery_level=60,
                    connectivity="medium",
                    engagement=0.65,
                    local_epochs=1,
                    label_histogram={9: 75},
                ),
            ]
            server.add_clients(new_clients)
            print()

        # ===== Scenario: Round 4'de bazı clientlar ayrılsın (low battery, disconnected) =====
        if round_num == 4:
            print("\n📌 [Event] Round 4: Client 4 has connectivity issues, Client 2 is leaving")
            server.remove_clients([4, 2])
            print()

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

    print("\n" + "=" * 90)
    print(f"Simulation Complete ✓")
    print("=" * 90)


if __name__ == "__main__":
    main()

