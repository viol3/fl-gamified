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
    "standart": (
        "Senaryo 0'da `decide_participation()` hiç çağrılmadığı için (bkz. `senaryo_modlari.md` Bölüm 3), yukarıdaki "
        "özelliklerden yalnızca **connectivity** ve **battery_level** katılım üzerinde gerçek bir etkiye sahip "
        "(sunucu tarafı uygunluk filtresi üzerinden — weak connectivity ve düşük batarya elenme riskini artırır). "
        "**Engagement, cpu_power, data_quality ve storage_capacity_gb bu senaryoda katılım kararını hiç etkilemiyor** "
        "— roster'da bu özelliklerde büyük varyasyon (özellikle data_quality: 0.51-0.99 ve local_samples: 51-191) olsa "
        "bile, kimin seçileceği bundan bağımsız, salt `selection_rate=0.6` olasılıklı bir örnekleme. Bu roster, "
        "Senaryo 1/2 ile kıyaslandığında asıl farkı ortaya koyacak: aynı roster'da bu sefer engagement/data_quality'nin "
        "katılımı gerçekten etkileyip etkilemediğini göreceğiz."
    ),
    "static": (
        "Senaryo 1'de `decide_participation()` çağrıldığı için (bkz. `senaryo_modlari.md` Bölüm 4), yukarıdaki "
        "özelliklerin tamamı katılım skoruna doğrudan girer: `base_score = 0.45*engagement + 0.25*(battery/100) + "
        "0.15*min(cpu_power/4,1) + 0.15*data_quality`. Ödül sabit olduğu için (`static_reward_points`) tüm client'lara "
        "aynı `reward_bonus` eklenir — dolayısıyla client'lar arası katılım farkı artık **yalnızca roster'daki içsel "
        "farklılıklardan** kaynaklanır. Buna ek olarak, hem sunucu tarafı uygunluk filtresi (Bölüm 2) hem de istemci içi "
        "ikinci kademe kontrol (batarya<20, bağlantı kopma olasılığı: weak=0.35, medium=0.15, strong=0.05) weak/medium "
        "connectivity client'ları yapısal olarak dezavantajlı kılar. Senaryo 0'ın aksine burada engagement ve data_quality "
        "gibi özelliklerin katılım üzerinde ölçülebilir bir etkisi beklenir."
    ),
    "dynamic": (
        "Senaryo 2'de `decide_participation()` çağrılır ve ödül artık round/bağlılık/bağlantı/geçmişe duyarlı biçimde "
        "kişiselleştirilir (bkz. `senaryo_modlari.md` Bölüm 5). Roster'daki özelliklerin katılım üzerindeki etkisi Senaryo "
        "1'deki taban skor mekanizmasıyla aynıdır, ancak dezavantajlı client'lar (düşük engagement, zayıf bağlantı, önceki "
        "round'a katılmama) ek ödül bonusları alır — bu da Senaryo 1'e kıyasla dezavantajlı client'ların katılımını kısmen "
        "telafi etmesi beklenen bir mekanizmadır."
    ),
}


def render_roster_section(roster: list[dict], profile: dict, mode_tag: str = "standart") -> list[str]:
    lines = []
    lines.append("## 0. Client Roster Profili")
    lines.append("")
    lines.append(f"Sabit roster: {profile['n_clients']} client, toplam {profile['total_samples']} sample (ort. {profile['total_samples'] / profile['n_clients']:.1f}/client).")
    lines.append("")
    lines.append("### Özellik Dağılımı")
    lines.append("")
    lines.append("| Özellik | Min | Max | Ortalama | Std | Varyasyon Katsayısı (CV) |")
    lines.append("|---|---|---|---|---|---|")
    for attr, label in ROSTER_ATTRS:
        s = profile["stats"][attr]
        lines.append(f"| {label} | {s['min']} | {s['max']} | {s['mean']:.3f} | {s['std']:.3f} | {s['cv']:.3f} |")
    lines.append("")
    ranked_cv = sorted(ROSTER_ATTRS, key=lambda a: profile["stats"][a[0]]["cv"], reverse=True)
    most_varied = ranked_cv[0][1]
    least_varied = ranked_cv[-1][1]
    lines.append(
        f"**Ön plana çıkan özellik:** CV (std/mean) bazında en fazla farklılaşan özellik **{most_varied}** "
        f"(CV={profile['stats'][ranked_cv[0][0]]['cv']:.3f}) — client'lar arasında en çok bu boyutta ayrışıyorlar. "
        f"En homojen özellik ise **{least_varied}** (CV={profile['stats'][ranked_cv[-1][0]]['cv']:.3f}) — "
        "engagement değerleri client'lar arasında görece dar bir bantta (0.59-0.78) toplanmış, yani roster'da "
        "'aşırı motivasyonsuz' ya da 'aşırı motivasyonlu' bir uç client yok."
    )
    lines.append("")
    lines.append("### Connectivity Dağılımı")
    lines.append("")
    for level in ["strong", "medium", "weak"]:
        count = profile["connectivity_counts"].get(level, 0)
        lines.append(f"- {level}: {count} client")
    lines.append("")
    lines.append("### Veri (Digit) Kapsamı")
    lines.append("")
    lines.append(f"- Roster'ın kapsadığı rakamlar: {profile['digits_covered']}")
    if profile["digits_missing"]:
        lines.append(
            f"- **Hiç örneği olmayan rakamlar: {profile['digits_missing']}** — bu roster'da hiçbir client'ın "
            f"local_samples'ında {profile['digits_missing']} rakamlarına ait tek bir örnek yok (Dirichlet/non-IID dağılımın "
            "rastgele bir sonucu). Bu, hangi senaryo çalışırsa çalışsın (0/1/2 fark etmez) global modelin bu rakamları "
            "hiç görmeden eğitileceği anlamına gelir — mevcut accuracy simülasyonu rakam-bazlı değil toplu bir formül "
            "kullandığı için sayısal sonucu etkilemiyor, ama gerçek bir sınıflandırma deneyinde bu ciddi bir kapsam "
            "boşluğu olarak raporlanmalı."
        )
    else:
        lines.append("- Roster tüm rakamları (0-9) kapsıyor.")
    lines.append("")
    lines.append(f"### Senaryo {'0' if mode_tag == 'standart' else '1' if mode_tag == 'static' else '2'} İçin Çıkarım")
    lines.append("")
    lines.append(SCENARIO_INFERENCE[mode_tag])
    lines.append("")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare paired Flower/Unity batch runs and write an aggregate report.")
    parser.add_argument("--mode-tag", default="standart", choices=["standart", "static", "dynamic"], help="Scenario subfolder to compare (matches outputs/Flower/<tag> and outputs/Unity/<tag>)")
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
        print(f"WARNING: {len(flower_files)} Flower files vs {len(unity_files)} Unity files — pairing only the first {min(len(flower_files), len(unity_files))}.")

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

    scenario_titles = {"standart": "Scenario 0 — Baz FL", "static": "Scenario 1 — Statik Teşvik", "dynamic": "Scenario 2 — Dinamik Oyunlaştırılmış FL"}
    # Markdown report
    lines = []
    lines.append(f"# {scenario_titles[args.mode_tag]} — Flower vs Unity (10 paired runs, fixed roster)")
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
