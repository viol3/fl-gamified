# Gamified Federated Learning Simulator

Code for my M.Sc. thesis at Ankara University (Computer Engineering, 2026):
*Simulating Participant Behavior in Gamified Federated Learning Systems*
(supervisor: Assoc. Prof. Dr. Bülent Tuğrul).

The simulator models a federated learning system in which clients decide in every round whether to take part, based on their battery, connectivity, engagement, fatigue and the reward offered by the server. It is used to compare three incentive settings:

| Mode | Scenario | Participation rule |
|---|---|---|
| `0` | Standard FL | no incentive, random participation among eligible clients |
| `1` | Static incentive | every participant gets the same fixed reward |
| `2` | Dynamic gamified incentive | the reward depends on the client's state and history (engagement, weak connectivity, previous participation), with a reward cap |

Training uses FedAvg with DP-FedAvg (update clipping and Gaussian noise). The same logic was also implemented in C# as a separate Unity simulation, and the results of both implementations were compared run by run.

## Results in short

All results below come from 10 runs of 100 rounds per scenario on the same fixed roster of 10 clients.

- A static reward **lowered** total participation by about 17% compared with no incentive, because the extra eligibility checks outweighed the small reward bonus.
- After tuning, the dynamic scheme recovered participation to about 94% (Flower) and 96% (Unity) of the standard scenario.
- Weakly connected clients recovered only about half of their lost participation, compared with almost all of it for well-connected clients.
- The Python and Unity implementations agreed within about 1 to 2.5 percentage points of accuracy.

The full analysis is in the thesis.

## Project structure

```
src/fl_gamified/
  client.py        client model, random roster generation, participation decision
  server.py        client selection, reward offer, FedAvg aggregation, summary export
  privacy.py       DP-FedAvg (clipping, Gaussian noise, privacy accounting)
  system.py        step-by-step simulation runner with detailed logs
  config.py        all simulation parameters (SimulationConfig)
  logger.py        JSONL event logger
  reporting.py     comparison of a Flower summary with a Unity summary
run.py                     single demo run (also generates a new client roster)
run_batch.py               N repeated runs of one scenario on a fixed roster
compare_batch.py           Flower vs Unity comparison over all runs of a scenario
build_scenario_report.py   detailed per-scenario report
compare_reward_budget.py   control experiment: static reward with the same total budget as dynamic
compare_summaries.py       compare one Flower summary with one Unity summary
outputs/
  initial_clients.json     the fixed client roster used in the thesis
  Flower/<scenario>/       per-run summaries from the Python simulation
  Flower_static_matched35/ static scenario with the reward matched to the dynamic budget
  Unity/<scenario>/        per-run summaries exported from the Unity simulation
  summary_comparison_scenario_<scenario>_10runs.*   Flower vs Unity comparison tables
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Reproducing the experiments

Run each scenario 10 times on the fixed roster (seeds 101 to 110):

```bash
python run_batch.py --mode 0 --runs 10
python run_batch.py --mode 1 --runs 10
python run_batch.py --mode 2 --runs 10
```

Results are written to `outputs/Flower/<standard|static|dynamic>/`.

Compare them with the Unity runs and build the reports:

```bash
python compare_batch.py --mode-tag dynamic
python build_scenario_report.py --mode-tag dynamic
```

Useful options of `run_batch.py`: `--rounds`, `--selection-rate`, `--seed-start`, `--no-dp`, `--dp-noise`, `--dp-clip`, `--static-reward`. All other parameters are in `src/fl_gamified/config.py`.

**Note:** `run.py` creates a new random client roster and overwrites `outputs/initial_clients.json`. To reproduce the thesis results, use `run_batch.py`, which always loads the existing roster.

## Unity simulation

The Unity project is not part of this repository. It reads `outputs/initial_clients.json`, runs the same three scenarios with a visual interface and exports `unity_comparison_summary_*.json` files with the same structure as the Python summaries. The exported files used in the thesis are in `outputs/Unity/`.

## Notes

- The accuracy value is an analytical function of the aggregated weights, not a real classification accuracy. The thesis focuses on participation and incentive design rather than model accuracy.
- `conceptual_framework_diagram.png` shows the overall design of the simulator.
