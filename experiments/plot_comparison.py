#!/usr/bin/env python3
"""
TrafficTwin AI — Fixed vs Queue-Reactive Comparison Chart (Module M3)

Reads the fixed baseline and reactive summary CSVs and produces a comparison
bar chart of average waiting time across scenarios.

Usage:
    python experiments/plot_comparison.py
"""

import csv
import sys
from pathlib import Path

RESULTS_DIR = Path("data/output/metrics")
CHART_DIR = Path("data/demo_assets")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("ERROR: matplotlib is required. Install it with: pip install matplotlib")
    sys.exit(1)


def load_summary(controller: str, scenario: str) -> dict | None:
    """Read a summary CSV and return its data as a dict."""
    csv_path = RESULTS_DIR / f"{controller}_{scenario}_summary.csv"
    if not csv_path.exists():
        return None
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows[0] if rows else None


def main() -> None:
    scenarios = ["normal", "rush"]

    labels = []
    fixed_waits = []
    reactive_waits = []

    for sc in scenarios:
        fixed_row = load_summary("fixed", sc)
        reactive_row = load_summary("reactive", sc)

        if fixed_row is None:
            print(f"  Skipping '{sc}' — fixed summary CSV missing")
            continue
        if reactive_row is None:
            print(f"  Skipping '{sc}' — reactive summary CSV missing")
            continue

        labels.append(sc.capitalize())
        fixed_waits.append(float(fixed_row["average_waiting_time"]))
        reactive_waits.append(float(reactive_row["average_waiting_time"]))

    if not labels:
        print("ERROR: No matching summary CSV files found.")
        sys.exit(1)

    # Side-by-side bar chart
    x = list(range(len(labels)))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(7, 5))

    bars1 = ax.bar(
        [i - bar_width / 2 for i in x],
        fixed_waits,
        bar_width,
        label="Fixed-Time",
        color="#4878CF",
    )
    bars2 = ax.bar(
        [i + bar_width / 2 for i in x],
        reactive_waits,
        bar_width,
        label="Queue-Reactive",
        color="#6ACC65",
    )

    # Data value labels above bars
    for bar in bars1:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.4,
            f"{height:.1f}s",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    for bar in bars2:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.4,
            f"{height:.1f}s",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    ax.set_xlabel("Scenario", fontsize=11)
    ax.set_ylabel("Average Waiting Time (seconds)", fontsize=11)
    ax.set_title(
        "Average Waiting Time: Fixed-Time vs Queue-Reactive\n"
        "(TrafficTwin AI — Module M3 Baseline Comparison, seed=42)",
        fontsize=12,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.legend(fontsize=10)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    CHART_DIR.mkdir(parents=True, exist_ok=True)
    chart_path = CHART_DIR / "fixed_vs_reactive_waiting_time.png"
    plt.tight_layout()
    plt.savefig(chart_path, dpi=120)
    plt.close()

    print(f"Comparison chart saved: {chart_path}")


if __name__ == "__main__":
    main()
