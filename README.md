# Gamified Federated Learning Thesis Starter

This repository is a small thesis testbed for comparing a Flower/Python federated learning simulation with a Unity simulation.

The current workflow is:

1. Generate a fresh random client roster in Python.
2. Run 100 federated rounds in Python and export `flower_comparison_summary.json`.
3. Copy the generated `initial_clients.json` into Unity and run the same scenario.
4. Export `unity_comparison_summary.json` from Unity.
5. Compare the two summaries with the reusable compare function or CLI script.

## Project Files

- `run.py`: runs the Flower/Python simulation and writes summary outputs.
- `compare_summaries.py`: compares the Flower and Unity summaries and writes report files.
- `src/fl_gamified/client.py`: client model and random client generation.
- `src/fl_gamified/server.py`: federated round logic and Flower summary export.
- `src/fl_gamified/system.py`: higher-level simulation orchestration.
- `src/fl_gamified/reporting.py`: reusable summary comparison helper.

## Flower / Python Run

### 1. Create the environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run the simulation

```powershell
python run.py
```

What this produces:

- `outputs/initial_clients.json`
- `outputs/flower_comparison_summary.json`
- `outputs/simulation_events.jsonl`

The initial client roster is randomized by default on every run. The current setup uses `build_random_clients(count=10)` without a fixed seed, so each run can produce a different client mix.

### 3. What the Flower summary contains

- `config`: the simulation configuration used for the run.
- `rounds`: per-round selection, training, samples, and accuracy values.
- `final_clients`: final client state snapshot.
- `final_model_accuracy`: the final global accuracy.

## Unity Run

### 1. Move the Python client roster into Unity

Take `outputs/initial_clients.json` from the Python run and place it where Unity can read it, then import it through the parser in the Unity project.

The current Unity import flow is implemented in `FLSimulationManager` and `FLParser`.

### 2. Run the Unity simulation

Use the Unity UI to start the simulation and export the report. The report button writes the summary to:

- `Outputs/unity_comparison_summary.json`

Unity is currently configured for 100 rounds, matching the Python run.

### 3. What the Unity summary contains

The Unity summary matches the same top-level structure as the Flower summary:

- `config`
- `rounds`
- `final_clients`
- `final_model_accuracy`

## Compare Flower and Unity

### CLI usage

After both summaries exist, generate the comparison reports with:

```powershell
python compare_summaries.py --flower outputs/flower_comparison_summary.json --unity outputs/unity_comparison_summary.json
```

This writes:

- `outputs/summary_comparison.md`
- `outputs/summary_comparison.csv`

### Reusable function

If you want to use the comparison logic from another Python script, import:

```python
from src.fl_gamified.reporting import compare_comparison_summaries

report = compare_comparison_summaries(
    "outputs/flower_comparison_summary.json",
    "outputs/unity_comparison_summary.json",
    "outputs/summary_comparison.md",
    "outputs/summary_comparison.csv",
)
```

The function returns a dictionary with:

- summary-level differences
- round-level differences
- client-level differences

## Current Comparison Artifacts

The latest generated comparison artifacts are:

- `outputs/summary_comparison.md`
- `outputs/summary_comparison.csv`

Those files are meant to be regenerated every time you run a new Flower summary and a new Unity summary.

## Notes

- Unity export naming is standardized to `unity_comparison_summary.json`.
- The comparison script assumes both summaries share the same schema.
- If you change the number of clients or the selection logic, regenerate both summaries before comparing.