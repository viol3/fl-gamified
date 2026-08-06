from __future__ import annotations

import argparse

from src.fl_gamified.reporting import compare_comparison_summaries


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Flower and Unity comparison summaries.")
    parser.add_argument("--flower", default="outputs/flower_comparison_summary.json", help="Path to Flower summary JSON")
    parser.add_argument("--unity", default="outputs/unity_comparison_summary.json", help="Path to Unity summary JSON")
    parser.add_argument("--markdown", default="outputs/summary_comparison.md", help="Markdown report output path")
    parser.add_argument("--csv", default="outputs/summary_comparison.csv", help="CSV report output path")
    args = parser.parse_args()

    report = compare_comparison_summaries(args.flower, args.unity, args.markdown, args.csv)

    print("Comparison report generated")
    print(f"  Markdown: {args.markdown}")
    print(f"  CSV: {args.csv}")
    print(f"  Final accuracy diff: {report['summary_diff']['accuracy_diff']:.6f}")


if __name__ == "__main__":
    main()