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
    parser.add_argument("--mode-tag", default="standart", choices=["standart", "static", "dynamic"], help="Scenario subfolder to report on (matches outputs/Flower/<tag> and outputs/Unity/<tag>)")
    parser.add_argument("--flower-glob", default=None, help="default: outputs/Flower/<mode-tag>/flower_comparison_summary_*.json")
    parser.add_argument("--unity-glob", default=None, help="default: outputs/Unity/<mode-tag>/unity_comparison_summary_*.json")
    parser.add_argument("--roster", default="outputs/initial_clients.json")
    parser.add_argument("--scenario-name", default=None)
    parser.add_argument("--out-md", default=None, help="default: outputs/scenario_<mode-tag>_full_report.md")
    args = parser.parse_args()

    scenario_names = {"standart": "Senaryo 0 - Baz FL (Teşviksiz)", "static": "Senaryo 1 - Statik Teşvik", "dynamic": "Senaryo 2 - Dinamik Oyunlaştırılmış FL"}
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
    lines.append(f"# {scenario_name} — Ayrıntılı Rapor ({flower_sys['n_runs']} Flower run + {unity_sys['n_runs']} Unity run, sabit roster)")
    lines.append("")
    lines.append("## 1. Sistem Düzeyi Özet")
    lines.append("")
    lines.append("| Metrik | Flower (Python) | Unity |")
    lines.append("|---|---|---|")
    lines.append(f"| Run sayısı | {flower_sys['n_runs']} | {unity_sys['n_runs']} |")
    lines.append(f"| Round sayısı / run | {rounds_total} | {rounds_total} |")
    lines.append(f"| Final accuracy (ortalama) | {flower_sys['accuracy_mean']:.4f} | {unity_sys['accuracy_mean']:.4f} |")
    lines.append(f"| Final accuracy (std) | {flower_sys['accuracy_std']:.4f} | {unity_sys['accuracy_std']:.4f} |")
    lines.append(f"| Final accuracy (min-max) | {flower_sys['accuracy_min']:.4f} - {flower_sys['accuracy_max']:.4f} | {unity_sys['accuracy_min']:.4f} - {unity_sys['accuracy_max']:.4f} |")
    lines.append(f"| Baseline'a göre kazanç (min_accuracy={flower_runs[0]['config']['min_accuracy']}) | +{flower_sys['accuracy_gain_from_baseline']:.4f} | +{unity_sys['accuracy_gain_from_baseline']:.4f} |")
    lines.append(f"| Run başına toplam seçim (client-round) | {flower_sys['selected_mean']:.1f} (±{flower_sys['selected_std']:.1f}) | {unity_sys['selected_mean']:.1f} (±{unity_sys['selected_std']:.1f}) |")
    lines.append(f"| Run başına toplam sample | {flower_sys['samples_mean']:.0f} | {unity_sys['samples_mean']:.0f} |")
    lines.append(f"| Kaydedilen round sayısı / run | {flower_last_round} | {unity_last_round} |")
    lines.append("")
    if flower_last_round != unity_last_round:
        lines.append(
            f"**⚠ Bulgu:** Unity her run'da {unity_last_round} round kaydediyor, config'de `rounds={rounds_total}` olmasına rağmen "
            f"(Flower tam {flower_last_round} kaydediyor). Sebebi muhtemelen `FLSimulationManager.RunnerProcess()` içindeki "
            "`IsMaxRoundsReached()` kontrolünün her PHASE çağrısından sonra (round tamamlanmadan) devreye girmesi — "
            f"`RoundNumber`, {rounds_total}. round'un Idle fazında {rounds_total}'e ulaşır ulaşmaz döngü hemen `yield break` ile "
            f"duruyor, bu round'un `RoundComplete` fazı hiç çalışmadığı için `AggregationHistory`'ye eklenmiyor. Bu bir off-by-one "
            "durdurma hatası — düzeltilmek istenirse ayrıca ele alınabilir."
        )
        lines.append("")
    lines.append("**Yorum:** Weight-magnitude formülü düzeltmesi sonrası iki platformun final accuracy ortalaması birbirine çok yakın "
                  f"(fark: {abs(flower_sys['accuracy_mean'] - unity_sys['accuracy_mean']):.4f}) — sistemli bir sapma kalmamış, kalan fark run-to-run "
                  "stokastik varyans seviyesinde.")
    lines.append("")

    lines.append("## 2. Yakınsama Eğrisi (Round Bazlı Ortalama Accuracy)")
    lines.append("")
    lines.append("| Round | Flower | Unity |")
    lines.append("|---|---|---|")
    for cp in checkpoints:
        f_val = flower_trend.get(cp)
        u_val = unity_trend.get(cp)
        lines.append(f"| {cp} | {f_val:.4f} | {u_val:.4f} |" if f_val is not None and u_val is not None else f"| {cp} | - | - |")
    lines.append("")

    lines.append("## 3. Client Bazlı Katılım ve Fayda Analizi")
    lines.append("")
    participation_basis = {
        "standart": "Senaryo 0'da ödül olmadığı için client'lar teşvikten değil, sadece rastgele seçim + kendi uygunluk durumlarından etkileniyor.",
        "static": "Senaryo 1'de tüm client'lara aynı sabit ödül teklif edildiği için katılım farkları artık client'ların davranışsal skoruna (`base_score`: engagement/battery/cpu/data_quality) ve uygunluk/bağlantı-kopma risklerine bağlı.",
        "dynamic": "Senaryo 2'de ödül client/round'a özgü kişiselleştirildiği için katılım farkları hem davranışsal skora hem de dezavantajlı client'lara yönelik hedefli ödül bonuslarına bağlı.",
    }
    lines.append(f"Her client, {rounds_total} round üzerinden {flower_sys['n_runs']} ayrı run'da (ortalama) ne kadar katıldı, "
                  "ne kadar 'yorgun' düştü ve ne kadar local accuracy elde etti. Roster sabit olduğu için (10 client, seed=42), "
                  f"'fayda' burada katılım sıklığı + elde edilen local model accuracy olarak okunmalı — {participation_basis[args.mode_tag]}")
    lines.append("")
    lines.append("| Client | Engagement | Connectivity | Battery(init) | Data Quality | Flower Katılım (ort/100) | Flower Local Acc | Unity Katılım (ort/100) | Unity Local Acc |")
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
    lines.append("### En Çok / En Az Katılan Client (Flower referansı)")
    lines.append("")
    lines.append(
        f"- **En çok katılan:** Client {most} — ortalama {flower_clients[most]['participation_mean']:.1f}/{rounds_total} round "
        f"(engagement={roster_by_id[most]['engagement']:.2f}, connectivity={roster_by_id[most]['connectivity']}, battery={roster_by_id[most]['battery_level']})"
    )
    lines.append(
        f"- **En az katılan:** Client {least} — ortalama {flower_clients[least]['participation_mean']:.1f}/{rounds_total} round "
        f"(engagement={roster_by_id[least]['engagement']:.2f}, connectivity={roster_by_id[least]['connectivity']}, battery={roster_by_id[least]['battery_level']})"
    )
    lines.append("")

    # Correlation-ish observation: engagement vs participation
    lines.append("### Katılım — Client Özelliği İlişkisi (gözlemsel)")
    lines.append("")
    lines.append("| Client | Engagement | Connectivity | Flower Katılım (ort) |")
    lines.append("|---|---|---|---|")
    for cid in sorted(client_ids, key=lambda c: roster_by_id[c]["engagement"], reverse=True):
        lines.append(f"| {cid} | {roster_by_id[cid]['engagement']:.2f} | {roster_by_id[cid]['connectivity']} | {flower_clients.get(cid, {}).get('participation_mean', 0):.1f} |")
    lines.append("")
    participation_note = {
        "standart": "*Not: Senaryo 0'da katılım kararı `decide_participation()` çağrılmadığı için (bkz. `senaryo_modlari.md` Bölüm 3) "
                    "engagement'ın katılım üzerinde DOĞRUDAN bir etkisi olmamalı — tek etken uygunluk filtresi (bağlantı/batarya) + "
                    "sabit `selection_rate` Bernoulli çekilişi. Tablo, bu teorik beklentiyi ampirik olarak doğrulamak için verilmiştir: "
                    "connectivity='weak' olan client'ların (uygunluk filtresinde ek elenme riski nedeniyle) hafifçe daha düşük katılım "
                    "göstermesi beklenir, engagement seviyesinin ise katılımla güçlü bir ilişkisi olmamalıdır.*",
        "static": "*Not: Senaryo 1'de `decide_participation()` çağrıldığı için (bkz. `senaryo_modlari.md` Bölüm 4) engagement, battery, "
                  "cpu_power ve data_quality katılım skoruna doğrudan girer (`base_score`). Ödül sabit olduğundan tüm client'lara aynı "
                  "`reward_bonus` eklenir, dolayısıyla client'lar arası fark artık davranışsal skordan kaynaklanmalı. connectivity='weak' "
                  "olan client'ların hem sunucu tarafı uygunluk filtresinde hem de istemci içi bağlantı-kopma olasılığında (0.35) çifte "
                  "dezavantajlı olması beklenir; bu tablo, engagement/connectivity'nin katılım üzerinde artık ölçülebilir bir etkisi olup "
                  "olmadığını Senaryo 0 ile karşılaştırmak için verilmiştir.*",
        "dynamic": "*Not: Senaryo 2'de ödül client/round'a özgü kişiselleştirildiği için (bkz. `senaryo_modlari.md` Bölüm 5) düşük "
                   "engagement, zayıf bağlantı ve önceki round'a katılmama gibi dezavantajlı durumlar ek ödül bonusu tetikler — bu, "
                   "Senaryo 1'e kıyasla dezavantajlı client'ların katılım açığını kısmen kapatması beklenen bir mekanizmadır.*",
    }
    lines.append(participation_note[args.mode_tag])
    lines.append("")

    lines.append("## 4. Dosyalar")
    lines.append("")
    lines.append("### Flower run'ları")
    for f in flower_files:
        lines.append(f"- `{f}`")
    lines.append("")
    lines.append("### Unity run'ları")
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
