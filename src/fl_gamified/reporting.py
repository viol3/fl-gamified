from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def load_summary(path: str | Path) -> dict[str, Any]:
    summary_path = Path(path)
    with summary_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _round_map(summary: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(round_info["round"]): round_info for round_info in summary.get("rounds", [])}


def _client_map(summary: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {int(client["client_id"]): client for client in summary.get("final_clients", [])}


def compare_comparison_summaries(
    flower_summary_path: str | Path,
    unity_summary_path: str | Path,
    markdown_output_path: str | Path | None = None,
    csv_output_path: str | Path | None = None,
) -> dict[str, Any]:
    flower_summary = load_summary(flower_summary_path)
    unity_summary = load_summary(unity_summary_path)

    flower_rounds = _round_map(flower_summary)
    unity_rounds = _round_map(unity_summary)
    common_rounds = sorted(set(flower_rounds).intersection(unity_rounds))

    round_differences: list[dict[str, Any]] = []
    for round_number in common_rounds:
        flower_round = flower_rounds[round_number]
        unity_round = unity_rounds[round_number]
        round_differences.append(
            {
                "round": round_number,
                "flower_selected_count": flower_round.get("selected_count", 0),
                "unity_selected_count": unity_round.get("selected_count", 0),
                "flower_trained_count": flower_round.get("trained_count", 0),
                "unity_trained_count": unity_round.get("trained_count", 0),
                "flower_total_samples": flower_round.get("total_samples", 0),
                "unity_total_samples": unity_round.get("total_samples", 0),
                "flower_model_accuracy": flower_round.get("model_accuracy", 0.0),
                "unity_model_accuracy": unity_round.get("model_accuracy", 0.0),
            }
        )

    flower_clients = _client_map(flower_summary)
    unity_clients = _client_map(unity_summary)
    client_differences: list[dict[str, Any]] = []
    for client_id in sorted(set(flower_clients).intersection(unity_clients)):
        flower_client = flower_clients[client_id]
        unity_client = unity_clients[client_id]
        diff_keys = [
            key
            for key in sorted(set(flower_client).union(unity_client))
            if flower_client.get(key) != unity_client.get(key)
        ]
        if diff_keys:
            client_differences.append(
                {
                    "client_id": client_id,
                    "different_fields": diff_keys,
                    "flower": flower_client,
                    "unity": unity_client,
                }
            )

    summary_diff = {
        "flower_final_accuracy": flower_summary.get("final_model_accuracy", 0.0),
        "unity_final_accuracy": unity_summary.get("final_model_accuracy", 0.0),
        "accuracy_diff": abs(
            float(flower_summary.get("final_model_accuracy", 0.0))
            - float(unity_summary.get("final_model_accuracy", 0.0))
        ),
        "flower_selected_total": sum(round_info.get("selected_count", 0) for round_info in flower_summary.get("rounds", [])),
        "unity_selected_total": sum(round_info.get("selected_count", 0) for round_info in unity_summary.get("rounds", [])),
        "flower_trained_total": sum(round_info.get("trained_count", 0) for round_info in flower_summary.get("rounds", [])),
        "unity_trained_total": sum(round_info.get("trained_count", 0) for round_info in unity_summary.get("rounds", [])),
        "flower_total_samples": sum(round_info.get("total_samples", 0) for round_info in flower_summary.get("rounds", [])),
        "unity_total_samples": sum(round_info.get("total_samples", 0) for round_info in unity_summary.get("rounds", [])),
        "flower_config_rounds": flower_summary.get("config", {}).get("rounds"),
        "unity_config_rounds": unity_summary.get("config", {}).get("rounds"),
    }

    report = {
        "flower_summary_path": str(flower_summary_path),
        "unity_summary_path": str(unity_summary_path),
        "summary_diff": summary_diff,
        "round_differences": round_differences,
        "client_differences": client_differences,
    }

    if markdown_output_path is not None:
        _write_markdown_report(report, markdown_output_path)
    if csv_output_path is not None:
        _write_csv_report(report, csv_output_path)

    return report


def _write_markdown_report(report: dict[str, Any], markdown_output_path: str | Path) -> None:
    output_path = Path(markdown_output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary_diff = report["summary_diff"]
    round_differences = report["round_differences"]
    client_differences = report["client_differences"]

    lines: list[str] = []
    lines.append("# Flower vs Unity Comparison")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Flower summary: {report['flower_summary_path']}")
    lines.append(f"- Unity summary: {report['unity_summary_path']}")
    lines.append(f"- Final accuracy diff: {summary_diff['accuracy_diff']:.6f}")
    lines.append(f"- Flower selected total: {summary_diff['flower_selected_total']}")
    lines.append(f"- Unity selected total: {summary_diff['unity_selected_total']}")
    lines.append(f"- Flower total samples: {summary_diff['flower_total_samples']}")
    lines.append(f"- Unity total samples: {summary_diff['unity_total_samples']}")
    lines.append(f"- Flower config rounds: {summary_diff['flower_config_rounds']}")
    lines.append(f"- Unity config rounds: {summary_diff['unity_config_rounds']}")
    lines.append("")
    lines.append("## Biggest Round Gaps")
    for round_info in round_differences[:10]:
        lines.append(
            f"- Round {round_info['round']}: flower selected={round_info['flower_selected_count']}, "
            f"unity selected={round_info['unity_selected_count']}, "
            f"flower samples={round_info['flower_total_samples']}, "
            f"unity samples={round_info['unity_total_samples']}, "
            f"flower acc={round_info['flower_model_accuracy']:.6f}, "
            f"unity acc={round_info['unity_model_accuracy']:.6f}"
        )
    lines.append("")
    lines.append("## Client Differences")
    for client_info in client_differences:
        lines.append(
            f"- Client {client_info['client_id']}: different fields = {', '.join(client_info['different_fields'])}"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv_report(report: dict[str, Any], csv_output_path: str | Path) -> None:
    output_path = Path(csv_output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "scope",
            "id",
            "flower_value",
            "unity_value",
            "difference_fields",
        ])

        summary_diff = report["summary_diff"]
        for key in [
            "flower_final_accuracy",
            "unity_final_accuracy",
            "accuracy_diff",
            "flower_selected_total",
            "unity_selected_total",
            "flower_trained_total",
            "unity_trained_total",
            "flower_total_samples",
            "unity_total_samples",
            "flower_config_rounds",
            "unity_config_rounds",
        ]:
            writer.writerow(["summary", key, summary_diff.get(key), "", ""])

        for round_info in report["round_differences"]:
            writer.writerow([
                "round",
                round_info["round"],
                json.dumps({
                    "selected_count": round_info["flower_selected_count"],
                    "trained_count": round_info["flower_trained_count"],
                    "total_samples": round_info["flower_total_samples"],
                    "model_accuracy": round_info["flower_model_accuracy"],
                }),
                json.dumps({
                    "selected_count": round_info["unity_selected_count"],
                    "trained_count": round_info["unity_trained_count"],
                    "total_samples": round_info["unity_total_samples"],
                    "model_accuracy": round_info["unity_model_accuracy"],
                }),
                "selected_count,trained_count,total_samples,model_accuracy",
            ])

        for client_info in report["client_differences"]:
            writer.writerow([
                "client",
                client_info["client_id"],
                json.dumps(client_info["flower"], ensure_ascii=False),
                json.dumps(client_info["unity"], ensure_ascii=False),
                ",".join(client_info["different_fields"]),
            ])