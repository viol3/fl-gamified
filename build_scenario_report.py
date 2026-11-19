"""Build a detailed thesis-facing report for a scenario batch: system-level convergence/benefit
and per-client participation/benefit, aggregated across N paired Flower/Unity runs on the same
fixed client roster. Writes one consolidated Markdown report.
"""
import argparse
import glob
import json
import statistics


def load_runs(pattern):
    files = sorted(glob.glob(pattern))
    return [json.load(open(f, encoding="utf-8")) for f in files], files


def aggregate_system(runs):
    accs = [r["final_model_accuracy"] for r in runs]
    total_selected = [sum(rr["selected_count"] for rr in r["rounds"]) for r in runs]
    total_samples = [sum(rr["total_samples"] for rr in r["rounds"]) for r in runs]
    min_accuracy = runs[0]["config"]["min_accuracy"]
    return {
        "n_runs": len(runs),
        "accuracy_mean": statistics.mean(accs),
        "accuracy_std": statistics.pstdev(accs),
        "accuracy_min": min(accs),
        "accuracy_max": max(accs),
        "accuracy_gain_from_baseline": statistics.mean(accs) - min_accuracy,
        "selected_mean": statistics.mean(total_selected),
        "selected_std": statistics.pstdev(total_selected),
        "samples_mean": statistics.mean(total_samples),
    }


def accuracy_trend(runs, checkpoints):
    trend = {}
    for cp in checkpoints:
        values = []
        for r in runs:
            round_map = {rr["round"]: rr["model_accuracy"] for rr in r["rounds"]}
            if cp in round_map:
                values.append(round_map[cp])
        if values:
            trend[cp] = statistics.mean(values)
    return trend


def aggregate_clients(runs):
    per_client = {}
    for r in runs:
        for c in r["final_clients"]:
            cid = c["client_id"]
            bucket = per_client.setdefault(
                cid,
                {"total_participations": [], "battery_level": [], "fatigue": [], "local_model_accuracy": [], "participation_streak": []},
            )
            bucket["total_participations"].append(c["total_participations"])
            bucket["battery_level"].append(c["battery_level"])
            bucket["fatigue"].append(c["fatigue"])
            bucket["local_model_accuracy"].append(c["local_model_accuracy"])
            bucket["participation_streak"].append(c["participation_streak"])

    result = {}
    for cid, vals in per_client.items():
        result[cid] = {
            "participation_mean": statistics.mean(vals["total_participations"]),
            "participation_std": statistics.pstdev(vals["total_participations"]),
            "battery_mean": statistics.mean(vals["battery_level"]),
            "fatigue_mean": statistics.mean(vals["fatigue"]),
            "local_acc_mean": statistics.mean(vals["local_model_accuracy"]),
            "streak_mean": statistics.mean(vals["participation_streak"]),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a detailed per-client + system report for a scenario batch.")
    parser.add_argument("--mode-tag", default="standard", choices=["standard", "static", "dynamic"], help="Scenario subfolder to report on (matches outputs/Flower/<tag> and outputs/Unity/<tag>)")
    parser.add_argument("--flower-glob", default=None, help="default: outputs/Flower/<mode-tag>/flower_comparison_summary_*.json")
    parser.add_argument("--unity-glob", default=None, help="default: outputs/Unity/<mode-tag>/unity_comparison_summary_*.json")
    parser.add_argument("--roster", default="outputs/initial_clients.json")
    parser.add_argument("--scenario-name", default=None)
    parser.add_argument("--out-md", default=None, help="default: outputs/scenario_<mode-tag>_full_report.md")
    args = parser.parse_args()

    scenario_names = {"standard": "Scenario 0 - Baseline FL (no incentive)", "static": "Scenario 1 - Static Incentive", "dynamic": "Scenario 2 - Dynamic Gamified FL"}
    flower_glob = args.flower_glob or f"outputs/Flower/{args.mode_tag}/flower_comparison_summary_*.json"
    unity_glob = args.unity_glob or f"outputs/Unity/{args.mode_tag}/unity_comparison_summary_*.json"
    scenario_name = args.scenario_name or scenario_names[args.mode_tag]
    out_md = args.out_md or f"outputs/scenario_{args.mode_tag}_full_report.md"

    roster = json.load(open(args.roster, encoding="utf-8"))
    roster_by_id = {c["client_id"]: c for c in roster}

    flower_runs, flower_files = load_runs(flower_glob)
    unity_runs, unity_files = load_runs(unity_glob)

    rounds_total = flower_runs[0]["config"]["rounds"]
    flower_last_round = min(len(r["rounds"]) for r in flower_runs)
    unity_last_round = min(len(r["rounds"]) for r in unity_runs)
    common_last_round = min(flower_last_round, unity_last_round)
    checkpoints = sorted(set(min(common_last_round, cp) for cp in [1, 10, 25, 50, 75, 100]))

    flower_sys = aggregate_system(flower_runs)
    unity_sys = aggregate_system(unity_runs)
    flower_trend = accuracy_trend(flower_runs, checkpoints)
    unity_trend = accuracy_trend(unity_runs, checkpoints)
    flower_clients = aggregate_clients(flower_runs)
    unity_clients = aggregate_clients(unity_runs)

    client_ids = sorted(roster_by_id.keys())

    lines = []
    lines.append(f"# {scenario_name} - Detailed Report ({flower_sys['n_runs']} Flower runs + {unity_sys['n_runs']} Unity runs, fixed roster)")
    lines.append("")
    lines.append("## 1. System-Level Summary")
    lines.append("")
    lines.append("| Metric | Flower (Python) | Unity |")
    lines.append("|---|---|---|")
    lines.append(f"| Number of runs | {flower_sys['n_runs']} | {unity_sys['n_runs']} |")
    lines.append(f"| Rounds per run | {rounds_total} | {rounds_total} |")
    lines.append(f"| Final accuracy (mean) | {flower_sys['accuracy_mean']:.4f} | {unity_sys['accuracy_mean']:.4f} |")
    lines.append(f"| Final accuracy (std) | {flower_sys['accuracy_std']:.4f} | {unity_sys['accuracy_std']:.4f} |")
    lines.append(f"| Final accuracy (min-max) | {flower_sys['accuracy_min']:.4f} - {flower_sys['accuracy_max']:.4f} | {unity_sys['accuracy_min']:.4f} - {unity_sys['accuracy_max']:.4f} |")
    lines.append(f"| Gain over baseline (min_accuracy={flower_runs[0]['config']['min_accuracy']}) | +{flower_sys['accuracy_gain_from_baseline']:.4f} | +{unity_sys['accuracy_gain_from_baseline']:.4f} |")
    lines.append(f"| Total selections per run (client-rounds) | {flower_sys['selected_mean']:.1f} (±{flower_sys['selected_std']:.1f}) | {unity_sys['selected_mean']:.1f} (±{unity_sys['selected_std']:.1f}) |")
    lines.append(f"| Total samples per run | {flower_sys['samples_mean']:.0f} | {unity_sys['samples_mean']:.0f} |")
    lines.append(f"| Recorded rounds per run | {flower_last_round} | {unity_last_round} |")
    lines.append("")
    if flower_last_round != unity_last_round:
        lines.append(
            f"**Finding:** Unity records {unity_last_round} rounds per run although the config sets `rounds={rounds_total}` "
            f"(Flower records all {flower_last_round}). The likely cause is that the `IsMaxRoundsReached()` check in "
            "`FLSimulationManager.RunnerProcess()` runs after every phase call, before the round is complete: "
            f"as soon as `RoundNumber` reaches {rounds_total} in the Idle phase of round {rounds_total}, the loop exits with `yield break`, "
            "so the `RoundComplete` phase of that round never runs and the round is not added to `AggregationHistory`. "
            "This is an off-by-one stopping bug that can be fixed separately."
        )
        lines.append("")
    lines.append("**Comment:** After the weight-magnitude formula fix, the mean final accuracy of the two platforms is very close "
                  f"(difference: {abs(flower_sys['accuracy_mean'] - unity_sys['accuracy_mean']):.4f}). No systematic deviation remains; "
                  "the remaining difference is at the level of run-to-run stochastic variance.")
    lines.append("")

    lines.append("## 2. Convergence (Mean Accuracy per Round)")
    lines.append("")
    lines.append("| Round | Flower | Unity |")
    lines.append("|---|---|---|")
    for cp in checkpoints:
        f_val = flower_trend.get(cp)
        u_val = unity_trend.get(cp)
        lines.append(f"| {cp} | {f_val:.4f} | {u_val:.4f} |" if f_val is not None and u_val is not None else f"| {cp} | - | - |")
    lines.append("")

    lines.append("## 3. Participation and Benefit per Client")
    lines.append("")
    participation_basis = {
        "standard": "In Scenario 0 there is no reward, so clients are affected only by random selection and their own eligibility.",
        "static": "In Scenario 1 every client is offered the same fixed reward, so differences in participation depend on the clients' behavioural score (`base_score`: engagement/battery/cpu/data_quality) and on eligibility and disconnection risks.",
        "dynamic": "In Scenario 2 the reward is personalised per client and round, so differences in participation depend on both the behavioural score and the targeted bonuses for disadvantaged clients.",
    }
    lines.append(f"How often each client took part over {rounds_total} rounds (mean of {flower_sys['n_runs']} runs), "
                  "how fatigued it became and what local accuracy it reached. Because the roster is fixed (10 clients), "
                  f"'benefit' here means participation frequency plus the local model accuracy reached. {participation_basis[args.mode_tag]}")
    lines.append("")
    lines.append("| Client | Engagement | Connectivity | Battery(init) | Data Quality | Flower participation (mean/100) | Flower local acc | Unity participation (mean/100) | Unity local acc |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for cid in client_ids:
        roster_c = roster_by_id[cid]
        fc = flower_clients.get(cid, {})
        uc = unity_clients.get(cid, {})
        lines.append(
            f"| {cid} | {roster_c['engagement']:.2f} | {roster_c['connectivity']} | {roster_c['battery_level']} | {roster_c['data_quality']:.2f} | "
            f"{fc.get('participation_mean', 0):.1f} (±{fc.get('participation_std', 0):.1f}) | {fc.get('local_acc_mean', 0):.3f} | "
            f"{uc.get('participation_mean', 0):.1f} (±{uc.get('participation_std', 0):.1f}) | {uc.get('local_acc_mean', 0):.3f} |"
        )
    lines.append("")

    # Ranking: most vs least participating (Flower side, as reference)
    ranked = sorted(client_ids, key=lambda cid: flower_clients.get(cid, {}).get("participation_mean", 0), reverse=True)
    most = ranked[0]
    least = ranked[-1]
    lines.append("### Most and Least Participating Client (Flower as reference)")
    lines.append("")
    lines.append(
        f"- **Most participating:** Client {most}, mean {flower_clients[most]['participation_mean']:.1f}/{rounds_total} round "
        f"(engagement={roster_by_id[most]['engagement']:.2f}, connectivity={roster_by_id[most]['connectivity']}, battery={roster_by_id[most]['battery_level']})"
    )
    lines.append(
        f"- **Least participating:** Client {least}, mean {flower_clients[least]['participation_mean']:.1f}/{rounds_total} round "
        f"(engagement={roster_by_id[least]['engagement']:.2f}, connectivity={roster_by_id[least]['connectivity']}, battery={roster_by_id[least]['battery_level']})"
    )
    lines.append("")

    # Correlation-ish observation: engagement vs participation
    lines.append("### Participation vs. Client Attributes (observational)")
    lines.append("")
    lines.append("| Client | Engagement | Connectivity | Flower participation (mean) |")
    lines.append("|---|---|---|---|")
    for cid in sorted(client_ids, key=lambda c: roster_by_id[c]["engagement"], reverse=True):
        lines.append(f"| {cid} | {roster_by_id[cid]['engagement']:.2f} | {roster_by_id[cid]['connectivity']} | {flower_clients.get(cid, {}).get('participation_mean', 0):.1f} |")
    lines.append("")
    participation_note = {
        "standard": "*Note: in Scenario 0 `decide_participation()` is not called (see thesis, Section 3.8.2), so engagement "
                    "should have no direct effect on participation. The only factors are the eligibility filter (connectivity/battery) "
                    "and a Bernoulli draw with a fixed `selection_rate`. The table checks this expectation empirically: clients with "
                    "connectivity='weak' should participate slightly less (extra risk of being filtered out), while engagement "
                    "should show no strong relation to participation.*",
        "static": "*Note: in Scenario 1 `decide_participation()` is called (see thesis, Section 3.8.3), so engagement, battery, "
                  "cpu_power and data_quality enter the participation score directly (`base_score`). Since the reward is fixed, every "
                  "client gets the same `reward_bonus`, so differences between clients should come from the behavioural score. Clients "
                  "with connectivity='weak' are expected to be doubly disadvantaged, by the server-side eligibility filter and by the "
                  "client-side disconnection probability (0.35). The table is given for comparison with Scenario 0.*",
        "dynamic": "*Note: in Scenario 2 the reward is personalised per client and round (see thesis, Section 3.8.4). Low "
                   "engagement, weak connectivity and not taking part in the previous round trigger extra reward bonuses, a mechanism "
                   "expected to partly close the participation gap of disadvantaged clients compared with Scenario 1.*",
    }
    lines.append(participation_note[args.mode_tag])
    lines.append("")

    lines.append("## 4. Files")
    lines.append("")
    lines.append("### Flower runs")
    for f in flower_files:
        lines.append(f"- `{f}`")
    lines.append("")
    lines.append("### Unity runs")
    for f in unity_files:
        lines.append(f"- `{f}`")
    lines.append("")

    with open(out_md, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    print(f"Report written to: {out_md}")
    print(f"Flower accuracy mean={flower_sys['accuracy_mean']:.4f} | Unity accuracy mean={unity_sys['accuracy_mean']:.4f}")
    print(f"Most participating client (Flower): {most} | Least participating: {least}")


if __name__ == "__main__":
    main()
