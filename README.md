# Gamified Federated Learning Thesis Starter

This repository is a starter testbed for your thesis topic:

Simulating Participant Behavior in Gamified Federated Learning Systems

## What is included

- Flower-based federated learning simulation
- Participant behavior model (battery, connectivity, engagement, churn)
- Three scenarios:
  - baseline: no incentive mechanism
  - static: fixed incentive per participation
  - gamified: dynamic incentive with levels and streaks
- Unity-ready event stream output as JSONL (round metrics, leaderboard, client states)

## Project structure

- src/fl_gamified/config.py: experiment and scenario configuration
- src/fl_gamified/data.py: heterogeneous client data partitioning
- src/fl_gamified/model.py: sklearn model parameter utilities
- src/fl_gamified/behavior.py: participant behavior model
- src/fl_gamified/gamification.py: incentive and leaderboard engine
- src/fl_gamified/client.py: Flower NumPy client implementation
- src/fl_gamified/strategy.py: custom Flower strategy for behavior-aware client selection
- src/fl_gamified/bridge.py: Unity event publishing to JSONL
- src/fl_gamified/simulation.py: simulation runner
- run.py: command-line entrypoint

## Setup

1) Create and activate a virtual environment

- Windows PowerShell:
  - python -m venv .venv
  - .\.venv\Scripts\Activate.ps1

2) Install dependencies

- pip install -r requirements.txt

## Run examples

- Baseline
  - python run.py --scenario baseline --rounds 10 --clients 20

- Static incentives
  - python run.py --scenario static --rounds 10 --clients 20

- Gamified incentives
  - python run.py --scenario gamified --rounds 10 --clients 20

## Unity integration path

Simulation creates JSONL events at:

- outputs/unity_events.jsonl

Each line is a JSON event containing round stats, selected clients, incentive outcomes, and leaderboard snapshot.
Unity can tail this file or consume it through a small bridge service in later steps.

## Next thesis-oriented extensions

- Add differential privacy accounting and noisy reward attribution
- Add richer churn model with time-varying user routines
- Replace digits dataset with MNIST/CIFAR-10 scenarios
- Build socket bridge for real-time Unity ingestion
