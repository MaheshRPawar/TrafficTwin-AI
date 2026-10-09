#!/usr/bin/env python3
"""
TrafficTwin AI — Fixed-Time Baseline Runner (Module M2)

Runs one SUMO scenario headlessly, parses all output files,
calculates baseline metrics, and saves CSV results.

Usage:
    python experiments/run_fixed.py --scenario normal
    python experiments/run_fixed.py --scenario rush
    python experiments/run_fixed.py --scenario blocked_downstream
    python experiments/run_fixed.py --scenario ambulance
    python experiments/run_fixed.py --all
"""

import argparse
import subprocess  # nosec B404
import sys
from pathlib import Path

# Add project root to path so experiments/metrics can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.metrics.calculate_metrics import (
    calc_metrics,
    save_queues_csv,
    save_summary_csv,
    save_trips_csv,
)
from experiments.metrics.queue_parser import parse_queue
from experiments.metrics.summary_parser import parse_summary
from experiments.metrics.tripinfo_parser import parse_tripinfo

# Paths relative to project root
SCENARIOS_DIR = Path("sumo/scenarios")
OUTPUT_DIR = Path("sumo/output")
RESULTS_DIR = Path("data/output/metrics")

VALID_SCENARIOS = ["normal", "rush", "blocked_downstream", "ambulance"]


def run_scenario(scenario: str, gui: bool = False) -> dict:
    """Run SUMO for one scenario and return the computed metrics dict."""
    cfg_path = SCENARIOS_DIR / f"corridor_{scenario}.sumocfg"
    if not cfg_path.exists():
        print(f"ERROR: Config not found: {cfg_path}")
        sys.exit(1)

    print(f"\n--- Running fixed-time baseline: {scenario}{' (GUI)' if gui else ''} ---")
    sumo_bin = "sumo-gui" if gui else "sumo"
    cmd = [sumo_bin, "-c", str(cfg_path)]
    if gui:
        cmd.extend(["--start", "--quit-on-end"])

    result = subprocess.run(  # nosec B603 B607
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"ERROR: SUMO failed for scenario '{scenario}'")
        print(result.stderr)
        sys.exit(1)

    print(f"SUMO completed for '{scenario}' (exit code 0)")

    # Check output files exist
    tripinfo_path = OUTPUT_DIR / f"tripinfo_{scenario}.xml"
    queue_path = OUTPUT_DIR / f"queue_{scenario}.xml"
    summary_path = OUTPUT_DIR / f"summary_{scenario}.xml"

    for p in [tripinfo_path, queue_path, summary_path]:
        if not p.exists():
            print(f"ERROR: Expected output missing: {p}")
            sys.exit(1)

    # Parse outputs
    trips = parse_tripinfo(tripinfo_path)
    queue_records = parse_queue(queue_path)
    summary_steps = parse_summary(summary_path)

    print(f"  Parsed: {len(trips)} completed trips, {len(queue_records)} queue snapshots, "
          f"{len(summary_steps)} summary steps")

    # Calculate metrics
    metrics = calc_metrics(trips, queue_records, scenario)

    # Save CSVs
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    save_summary_csv(metrics, RESULTS_DIR / f"fixed_{scenario}_summary.csv")
    save_trips_csv(trips, RESULTS_DIR / f"fixed_{scenario}_trips.csv")
    save_queues_csv(queue_records, RESULTS_DIR / f"fixed_{scenario}_queues.csv")

    print(f"  Results saved to {RESULTS_DIR}/fixed_{scenario}_*.csv")
    print(f"  throughput={metrics['throughput']}  avg_wait={metrics['average_waiting_time']}s  "
          f"p95_wait={metrics['p95_waiting_time']}s  avg_travel={metrics['average_travel_time']}s  "
          f"mean_queue={metrics['mean_queue_length']}  max_queue={metrics['maximum_queue_length']}")

    if "emergency_delay" in metrics:
        print(f"  emergency_delay(emerg_1)={metrics['emergency_delay']}s")

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="TrafficTwin fixed-time baseline runner")
    parser.add_argument(
        "--scenario",
        choices=VALID_SCENARIOS,
        help="Scenario to run",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all scenarios",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch simulation in interactive SUMO GUI mode",
    )
    args = parser.parse_args()

    if not args.all and not args.scenario:
        parser.print_help()
        sys.exit(1)

    scenarios = VALID_SCENARIOS if args.all else [args.scenario]
    all_metrics = []

    for sc in scenarios:
        m = run_scenario(sc, gui=args.gui)
        all_metrics.append(m)

    # Print summary table
    print("\n=== Fixed-Time Baseline Summary ===")
    header = f"{'Scenario':<22} {'Thru':>6} {'AvgWait':>9} {'P95Wait':>9} {'AvgTrav':>9} {'MeanQ':>8} {'MaxQ':>8}"
    print(header)
    print("-" * len(header))
    for m in all_metrics:
        print(
            f"{m['scenario']:<22} {m['throughput']:>6} "
            f"{m['average_waiting_time']:>9.1f} {m['p95_waiting_time']:>9.1f} "
            f"{m['average_travel_time']:>9.1f} {m['mean_queue_length']:>8.2f} "
            f"{m['maximum_queue_length']:>8.2f}"
        )


if __name__ == "__main__":
    main()
