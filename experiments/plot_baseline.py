#!/usr/bin/env python3
"""
TrafficTwin AI — Fixed-Time Baseline Chart (Module M2)

Reads the fixed-time summary CSVs and produces a bar chart comparing
average waiting time across scenarios.

Usage:
    python experiments/plot_baseline.py
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


def load_summary(scenario: str) -> dict | None:
    """Read a single fixed baseline summary CSV and return its data as a dict."""
    csv_path = RESULTS_DIR / f"fixed_{scenario}_summary.csv"
    if not csv_path.exists():
        return None
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows[0] if rows else None


def main() -> None:
    scenarios = ["normal", "rush", "blocked_downstream", "ambulance"]

    labels = []
    avg_waits = []
    p95_waits = []

    for sc in scenarios:
        row = load_summary(sc)
        if row is None:
            print(f"  Skipping '{sc}' — summary CSV not found (run run_fixed.py first)")
            continue
        labels.append(sc.replace("_", "\n"))
        avg_waits.append(float(row["average_waiting_time"]))
        p95_waits.append(float(row["p95_waiting_time"]))

    if not labels:
        print("ERROR: No summary CSV files found. Run run_fixed.py --all first.")
        sys.exit(1)

    # Bar chart: average waiting time and p95 waiting time side by side
    x = list(range(len(labels)))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))

    bars1 = ax.bar([i - bar_width / 2 for i in x], avg_waits, bar_width,
                   label="Average Waiting Time (s)", color="#4878CF")
    bars2 = ax.bar([i + bar_width / 2 for i in x], p95_waits, bar_width,
                   label="P95 Waiting Time (s)", color="#E07B39")

    # Label each bar with its value
    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, height + 0.5,
                f"{height:.1f}", ha="center", va="bottom", fontsize=9)

    for bar in bars2:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, height + 0.5,
                f"{height:.1f}", ha="center", va="bottom", fontsize=9)

    ax.set_xlabel("Scenario")
    ax.set_ylabel("Waiting Time (seconds)")
    ax.set_title("Fixed-Time Baseline — Waiting Time by Scenario\n(TrafficTwin AI, controller=fixed, seed=42)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    CHART_DIR.mkdir(parents=True, exist_ok=True)
    chart_path = CHART_DIR / "fixed_baseline_waiting_time.png"
    plt.tight_layout()
    plt.savefig(chart_path, dpi=120)
    plt.close()

    print(f"Chart saved: {chart_path}")


if __name__ == "__main__":
    main()
