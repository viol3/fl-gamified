"""Compare N paired Flower vs Unity runs (same fixed roster, same scenario mode) and write
one consolidated report with per-pair diffs plus aggregate statistics (mean/std) across all
pairs. Files are paired in sorted-filename order from each directory.
"""
import argparse
import csv
import glob
import json
import os
from collections import Counter
from statistics import mean, pstdev

from src.fl_gamified.reporting import compare_comparison_summaries

ROSTER_ATTRS = [
    ("engagement", "Engagement"),
    ("battery_level", "Battery Level"),
    ("cpu_power", "CPU Power"),
    ("data_quality", "Data Quality"),
    ("storage_capacity_gb", "Storage (GB)"),
    ("local_samples", "Local Samples"),
    ("local_epochs", "Local Epochs"),
]


def roster_profile(roster: list[dict]) -> dict:
    stats = {}
    for attr, _ in ROSTER_ATTRS:
        values = [c[attr] for c in roster]
        m = mean(values)
        s = pstdev(values)
        stats[attr] = {
            "min": min(values),
            "max": max(values),
            "mean": m,
            "std": s,
            "cv": (s / m) if m else 0.0,
        }

    connectivity_counts = Counter(c["connectivity"] for c in roster)

    digits_covered = set()
    for c in roster:
        for digit in c.get("label_histogram", {}).keys():
            digits_covered.add(int(digit))
    digits_missing = sorted(set(range(10)) - digits_covered)

    total_samples = sum(c["local_samples"] for c in roster)

    return {
        "stats": stats,
        "connectivity_counts": connectivity_counts,
        "digits_covered": sorted(digits_covered),
        "digits_missing": digits_missing,
        "total_samples": total_samples,
        "n_clients": len(roster),
    }


SCENARIO_INFERENCE = {
    "standard": (
        "In Scenario 0 `decide_participation()` is never called (see thesis, Section 3.8.2), so of the attributes above "
        "only **connectivity** and **battery_level** have a real effect on participation, through the server-side "
        "eligibility filter (weak connectivity and low battery raise the risk of being filtered out). "
        "**Engagement, cpu_power, data_quality and storage_capacity_gb do not affect the participation decision in this scenario.** "
        "Even though the roster varies widely in these attributes (for example data_quality: 0.51-0.99 and local_samples: 51-191), "
        "who is selected is independent of them and follows a plain random draw with `selection_rate=0.6`. "
        "Comparing this roster with Scenarios 1 and 2 shows whether engagement and data_quality start to affect participation."
    ),
    "static": (
        "In Scenario 1 `decide_participation()` is called (see thesis, Section 3.8.3), so all attributes above "
        "enter the participation score directly: `base_score = 0.45*engagement + 0.25*(battery/100) + "
        "0.15*min(cpu_power/4,1) + 0.15*data_quality`. Because the reward is fixed (`static_reward_points`), every client "
        "gets the same `reward_bonus`, so differences in participation between clients come **only from the differences "
        "within the roster**. In addition, both the server-side eligibility filter (thesis, Section 3.8.1) and the client-side "
        "second check (battery<20, disconnection probability: weak=0.35, medium=0.15, strong=0.05) put clients with weak or medium "
        "connectivity at a structural disadvantage. Unlike Scenario 0, attributes such as engagement and data_quality are "
        "expected to have a measurable effect on participation."
    ),
    "dynamic": (
        "In Scenario 2 `decide_participation()` is called and the reward is personalised by round, engagement, connectivity "
        "and history (see thesis, Section 3.8.4). The attributes affect participation through the same base score as in "
        "Scenario 1, but disadvantaged clients (low engagement, weak connectivity, no participation in the previous round) "
        "receive extra reward bonuses, which is expected to partly compensate for their lower participation in Scenario 1."
    ),
}


def render_roster_section(roster: list[dict], profile: dict, mode_tag: str = "standard") -> list[str]:
    lines = []
    lines.append("## 0. Client Roster Profile")
    lines.append("")
    lines.append(f"Fixed roster: {profile['n_clients']} clients, {profile['total_samples']} samples in total (mean {profile['total_samples'] / profile['n_clients']:.1f} per client).")
    lines.append("")
    lines.append("### Attribute Distribution")
    lines.append("")
    lines.append("| Attribute | Min | Max | Mean | Std | Coefficient of Variation (CV) |")
    lines.append("|---|---|---|---|---|---|")
    for attr, label in ROSTER_ATTRS:
        s = profile["stats"][attr]
        lines.append(f"| {label} | {s['min']} | {s['max']} | {s['mean']:.3f} | {s['std']:.3f} | {s['cv']:.3f} |")
    lines.append("")
    ranked_cv = sorted(ROSTER_ATTRS, key=lambda a: profile["stats"][a[0]]["cv"], reverse=True)
    most_varied = ranked_cv[0][1]
    least_varied = ranked_cv[-1][1]
    lines.append(
        f"**Most varied attribute:** by CV (std/mean), clients differ most in **{most_varied}** "
        f"(CV={profile['stats'][ranked_cv[0][0]]['cv']:.3f}). "
        f"The most homogeneous attribute is **{least_varied}** (CV={profile['stats'][ranked_cv[-1][0]]['cv']:.3f}): "
        "engagement values lie in a fairly narrow band (0.59-0.78), so the roster has no extremely unmotivated "
        "or extremely motivated client."
    )
    lines.append("")
    lines.append("### Connectivity Distribution")
    lines.append("")
    for level in ["strong", "medium", "weak"]:
        count = profile["connectivity_counts"].get(level, 0)
        lines.append(f"- {level}: {count} clients")
    lines.append("")
    lines.append("### Data (Digit) Coverage")
    lines.append("")
    lines.append(f"- Digits covered by the roster: {profile['digits_covered']}")
    if profile["digits_missing"]:
        lines.append(
            f"- **Digits with no samples: {profile['digits_missing']}**. No client in this roster has a single sample of "
            f"digits {profile['digits_missing']} in its local data (a random outcome of the Dirichlet/non-IID split). "
            "Whatever the scenario (0, 1 or 2), the global model is trained without ever seeing these digits. "
            "The current accuracy simulation uses an aggregate formula rather than per-digit accuracy, so the numbers are "
            "not affected, but in a real classification experiment this would be a serious coverage gap."
        )
    else:
        lines.append("- The roster covers all digits (0-9).")
    lines.append("")
    lines.append(f"### Implications for Scenario {'0' if mode_tag == 'standard' else '1' if mode_tag == 'static' else '2'}")
    lines.append("")
    lines.append(SCENARIO_INFERENCE[mode_tag])
    lines.append("")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare paired Flower/Unity batch runs and write an aggregate report.")
    parser.add_argument("--mode-tag", default="standard", choices=["standard", "static", "dynamic"], help="Scenario subfolder to compare (matches outputs/Flower/<tag> and outputs/Unity/<tag>)")
    parser.add_argument("--flower-dir", default=None, help="Directory containing flower_comparison_summary_*.json files (default: outputs/Flower/<mode-tag>)")
    parser.add_argument("--unity-dir", default=None, help="Directory containing unity_comparison_summary_*.json files (default: outputs/Unity/<mode-tag>)")
    parser.add_argument("--roster", default="outputs/initial_clients.json", help="Fixed client roster JSON used by both platforms")
    parser.add_argument("--out-md", default=None, help="default: outputs/summary_comparison_scenario_<mode-tag>_10runs.md")
    parser.add_argument("--out-csv", default=None, help="default: outputs/summary_comparison_scenario_<mode-tag>_10runs.csv")
    parser.add_argument("--out-json", default=None, help="default: outputs/summary_comparison_scenario_<mode-tag>_10runs.json")
    args = parser.parse_args()

    flower_dir = args.flower_dir or os.path.join("outputs", "Flower", args.mode_tag)
    unity_dir = args.unity_dir or os.path.join("outputs", "Unity", args.mode_tag)
    out_md = args.out_md or f"outputs/summary_comparison_scenario_{args.mode_tag}_10runs.md"
    out_csv = args.out_csv or f"outputs/summary_comparison_scenario_{args.mode_tag}_10runs.csv"
    out_json = args.out_json or f"outputs/summary_comparison_scenario_{args.mode_tag}_10runs.json"

    flower_files = sorted(glob.glob(os.path.join(flower_dir, "flower_comparison_summary_*.json")))
    unity_files = sorted(glob.glob(os.path.join(unity_dir, "unity_comparison_summary_*.json")))

    if len(flower_files) != len(unity_files):
        print(f"WARNING: {len(flower_files)} Flower files vs {len(unity_files)} Unity files - pairing only the first {min(len(flower_files), len(unity_files))}.")

    pairs = list(zip(flower_files, unity_files))
    rows = []
    for i, (fpath, upath) in enumerate(pairs, start=1):
        report = compare_comparison_summaries(fpath, upath)
        sd = report["summary_diff"]
        rows.append(
            {
                "pair": i,
                "flower_path": fpath,
                "unity_path": upath,
                "flower_final_accuracy": sd["flower_final_accuracy"],
                "unity_final_accuracy": sd["unity_final_accuracy"],
                "accuracy_diff": sd["accuracy_diff"],
                "flower_selected_total": sd["flower_selected_total"],
                "unity_selected_total": sd["unity_selected_total"],
                "flower_total_samples": sd["flower_total_samples"],
                "unity_total_samples": sd["unity_total_samples"],
            }
        )

    flower_accs = [r["flower_final_accuracy"] for r in rows]
    unity_accs = [r["unity_final_accuracy"] for r in rows]
    diffs = [r["accuracy_diff"] for r in rows]

    aggregate = {
        "pairs": len(rows),
        "flower_accuracy_mean": mean(flower_accs),
        "flower_accuracy_std": pstdev(flower_accs),
        "unity_accuracy_mean": mean(unity_accs),
        "unity_accuracy_std": pstdev(unity_accs),
        "accuracy_diff_mean": mean(diffs),
        "accuracy_diff_std": pstdev(diffs),
        "accuracy_diff_max": max(diffs),
        "accuracy_diff_min": min(diffs),
    }

    os.makedirs(os.path.dirname(out_md), exist_ok=True)

    roster = json.load(open(args.roster, encoding="utf-8"))
    profile = roster_profile(roster)

    scenario_titles = {"standard": "Scenario 0 - Baseline FL", "static": "Scenario 1 - Static Incentive", "dynamic": "Scenario 2 - Dynamic Gamified FL"}
    # Markdown report
    lines = []
    lines.append(f"# {scenario_titles[args.mode_tag]} - Flower vs Unity (10 paired runs, fixed roster)")
    lines.append("")
    lines.extend(render_roster_section(roster, profile, args.mode_tag))
    lines.append("## Aggregate")
    lines.append(f"- Pairs compared: {aggregate['pairs']}")
    lines.append(f"- Flower final accuracy: mean={aggregate['flower_accuracy_mean']:.4f}, std={aggregate['flower_accuracy_std']:.4f}")
    lines.append(f"- Unity final accuracy: mean={aggregate['unity_accuracy_mean']:.4f}, std={aggregate['unity_accuracy_std']:.4f}")
    lines.append(f"- Accuracy diff |Flower-Unity|: mean={aggregate['accuracy_diff_mean']:.4f}, std={aggregate['accuracy_diff_std']:.4f}, min={aggregate['accuracy_diff_min']:.4f}, max={aggregate['accuracy_diff_max']:.4f}")
    lines.append("")
    lines.append("## Per-Pair Detail")
    lines.append("")
    lines.append("| Pair | Flower Acc | Unity Acc | Diff | Flower Selected | Unity Selected | Flower Samples | Unity Samples |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| {r['pair']} | {r['flower_final_accuracy']:.4f} | {r['unity_final_accuracy']:.4f} | {r['accuracy_diff']:.4f} | "
            f"{r['flower_selected_total']} | {r['unity_selected_total']} | {r['flower_total_samples']} | {r['unity_total_samples']} |"
        )
    lines.append("")
    lines.append("## Files")
    for r in rows:
        lines.append(f"- Pair {r['pair']}: `{r['flower_path']}` <-> `{r['unity_path']}`")

    with open(out_md, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    # CSV report
    with open(out_csv, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # JSON (full detail + aggregate)
    with open(out_json, "w", encoding="utf-8") as handle:
        json.dump({"aggregate": aggregate, "pairs": rows}, handle, ensure_ascii=False, indent=2)

    print(f"Pairs compared: {len(rows)}")
    print(f"Flower accuracy: mean={aggregate['flower_accuracy_mean']:.4f}, std={aggregate['flower_accuracy_std']:.4f}")
    print(f"Unity accuracy:  mean={aggregate['unity_accuracy_mean']:.4f}, std={aggregate['unity_accuracy_std']:.4f}")
    print(f"Diff: mean={aggregate['accuracy_diff_mean']:.4f}, std={aggregate['accuracy_diff_std']:.4f}")
    print(f"Markdown: {out_md}")
    print(f"CSV: {out_csv}")
    print(f"JSON: {out_json}")


if __name__ == "__main__":
    main()
