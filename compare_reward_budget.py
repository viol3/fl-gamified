"""Budget-matched control: is Scenario 2's participation gain over Scenario 1 due to
personalisation, or just to a larger average reward?

Compares four Flower-side batches on the same fixed roster and seeds:
standard, static (default reward), static with reward matched to dynamic's mean offer, dynamic.
Reports total participation, per-connectivity-group participation, recovery rate of each group's
static-vs-standard loss, and participation inequality across clients.
"""
import argparse
import glob
import json
import os
from statistics import mean, pstdev

from scipy import stats


def load_batch(directory):
    files = sorted(glob.glob(os.path.join(directory, "flower_comparison_summary_*.json")))
    if not files:
        raise SystemExit(f"No run files found in {directory}")
    return [json.load(open(f, encoding="utf-8")) for f in files]


def total_selected(run):
    return sum(r["selected_count"] for r in run["rounds"])


def group_participation(runs, roster):
    """Mean participations per client (averaged over runs), then averaged within each connectivity group."""
    groups = {}
    for c in roster:
        groups.setdefault(c["connectivity"], []).append(c["client_id"])
    per_client = {c["client_id"]: mean(next(fc["total_participations"] for fc in r["final_clients"] if fc["client_id"] == c["client_id"]) for r in runs) for c in roster}
    return {g: mean(per_client[cid] for cid in ids) for g, ids in groups.items()}, per_client


def gini(values):
    values = sorted(values)
    n = len(values)
    cum = sum((i + 1) * v for i, v in enumerate(values))
    return (2 * cum) / (n * sum(values)) - (n + 1) / n


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard", default="outputs/Flower/standard")
    parser.add_argument("--static", default="outputs/Flower/static")
    parser.add_argument("--static-matched", default="outputs/Flower_static_matched35/static")
    parser.add_argument("--dynamic", default="outputs/Flower/dynamic")
    parser.add_argument("--roster", default="outputs/initial_clients.json")
    parser.add_argument("--out-md", default="outputs/analysis_reward_budget_control.md")
    args = parser.parse_args()

    roster = json.load(open(args.roster, encoding="utf-8"))
    batches = {
        "standard": load_batch(args.standard),
        "static": load_batch(args.static),
        "static_matched": load_batch(args.static_matched),
        "dynamic": load_batch(args.dynamic),
    }
    static_reward = batches["static"][0]["config"]["static_reward_points"]
    matched_reward = batches["static_matched"][0]["config"]["static_reward_points"]
    labels = {
        "standard": "Scenario 0 - Standard",
        "static": f"Scenario 1 - Static ({static_reward} points)",
        "static_matched": f"Scenario 1b - Static, matched budget ({matched_reward} points)",
        "dynamic": "Scenario 2 - Dynamic (final)",
    }

    totals = {k: [total_selected(r) for r in runs] for k, runs in batches.items()}
    accs = {k: [r["final_model_accuracy"] for r in runs] for k, runs in batches.items()}
    groups, per_client = {}, {}
    for k, runs in batches.items():
        groups[k], per_client[k] = group_participation(runs, roster)

    base = mean(totals["standard"])
    lines = [
        "# Reward Budget Control: Does the Dynamic Gain Come from Personalisation or from a Larger Reward?",
        "",
        f"Same roster (`{args.roster}`), same seeds (101-110), 10 runs x 100 rounds, Flower (Python) side. "
        f"In Scenario 1b the static reward is set equal to the dynamic scenario's mean offer to eligible clients (about 35.4 points).",
        "",
        "## 1. Total Participation",
        "",
        "| Condition | Total selections per run (mean ± std) | Relative to standard | Final accuracy (mean ± std) |",
        "|---|---|---|---|",
    ]
    for k in batches:
        lines.append(
            f"| {labels[k]} | {mean(totals[k]):.1f} ± {pstdev(totals[k]):.1f} | {100 * mean(totals[k]) / base:.1f}% | "
            f"{mean(accs[k]):.4f} ± {pstdev(accs[k]):.4f} |"
        )
    lines.append("")

    t_dm = stats.ttest_ind(totals["dynamic"], totals["static_matched"], equal_var=False)
    t_ms = stats.ttest_ind(totals["static_matched"], totals["static"], equal_var=False)
    lines += [
        "Welch t-test (total selections):",
        f"- Dynamic vs static-matched-budget: difference = {mean(totals['dynamic']) - mean(totals['static_matched']):+.1f}, p = {t_dm.pvalue:.4f}",
        f"- Static-matched-budget vs static-{static_reward}: difference = {mean(totals['static_matched']) - mean(totals['static']):+.1f}, p = {t_ms.pvalue:.4g}",
        "",
        "## 2. Participation by Connectivity Group (mean per client, out of 100 rounds)",
        "",
        "| Group | Clients | " + " | ".join(labels[k] for k in batches) + " |",
        "|---|---|" + "---|" * len(batches),
    ]
    order = ["weak", "medium", "strong"]
    for g in order:
        ids = [c["client_id"] for c in roster if c["connectivity"] == g]
        lines.append(f"| {g} | {', '.join(map(str, ids))} | " + " | ".join(f"{groups[k][g]:.1f}" for k in batches) + " |")
    lines += [
        "",
        f"## 3. Recovery Rate (share of the static-{static_reward} loss relative to standard that is recovered)",
        "",
        "`recovery = (condition - static) / (standard - static)`",
        "",
        "| Group | Static, matched budget | Dynamic |",
        "|---|---|---|",
    ]
    for g in order:
        loss = groups["standard"][g] - groups["static"][g]
        rec = lambda k: (groups[k][g] - groups["static"][g]) / loss * 100 if loss else float("nan")
        lines.append(f"| {g} | {rec('static_matched'):.1f}% | {rec('dynamic'):.1f}% |")
    lines += [
        "",
        "## 4. Participation Inequality (across clients)",
        "",
        "| Condition | Gini | Least / most participating client (mean) |",
        "|---|---|---|",
    ]
    for k in batches:
        vals = list(per_client[k].values())
        lines.append(f"| {labels[k]} | {gini(vals):.4f} | {min(vals):.1f} / {max(vals):.1f} |")
    lines += [
        "",
        "## 5. Participation per Client (mean, out of 100 rounds)",
        "",
        "| Client | Connectivity | " + " | ".join(labels[k] for k in batches) + " |",
        "|---|---|" + "---|" * len(batches),
    ]
    for c in roster:
        cid = c["client_id"]
        lines.append(f"| {cid} | {c['connectivity']} | " + " | ".join(f"{per_client[k][cid]:.1f}" for k in batches) + " |")
    lines.append("")

    with open(args.out_md, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nReport written to: {args.out_md}")


if __name__ == "__main__":
    main()
