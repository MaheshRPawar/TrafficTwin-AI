#!/usr/bin/env python3
"""
TrafficTwin AI — Safe Queue-Reactive Controller Runner (Module M3)

Runs one SUMO scenario headlessly with TraCI and the safe queue-reactive controller,
logs decisions, parses output files, calculates metrics, and saves CSV results.

Usage:
    python experiments/run_reactive.py --scenario normal
    python experiments/run_reactive.py --scenario rush
    python experiments/run_reactive.py --all
"""

import argparse
import csv
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import traci

from experiments.metrics.calculate_metrics import (
    calc_metrics,
    save_queues_csv,
    save_summary_csv,
    save_trips_csv,
)
from experiments.metrics.queue_parser import parse_queue
from experiments.metrics.summary_parser import parse_summary
from experiments.metrics.tripinfo_parser import parse_tripinfo
from experiments.reactive_controller import (
    init_junction_states,
    load_controller_config,
    step_junction,
)

# Paths relative to project root
SCENARIOS_DIR = Path("sumo/scenarios")
OUTPUT_DIR = Path("sumo/output")
RESULTS_DIR = Path("data/output/metrics")

VALID_SCENARIOS = ["normal", "rush", "blocked_downstream", "ambulance"]
JUNCTION_IDS = ["J1", "J2", "J3", "J4"]


def save_decision_log(records: list[dict], output_path: Path) -> None:
    """Save controller decision records to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "timestamp",
        "junction_id",
        "current_phase",
        "queue_main",
        "queue_cross",
        "action",
        "reason",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)


def run_scenario(scenario: str) -> dict:
    """Run SUMO with reactive controller for one scenario and return metrics."""
    cfg_path = SCENARIOS_DIR / f"corridor_{scenario}.sumocfg"
    if not cfg_path.exists():
        print(f"ERROR: Config not found: {cfg_path}")
        sys.exit(1)

    print(f"\n--- Running queue-reactive controller: {scenario} ---")

    # Load controller parameters
    config = load_controller_config()
    print(f"  Loaded config: min_green={config['min_green_s']}s, max_green={config['max_green_s']}s, "
          f"ext_step={config['extension_step_s']}s, queue_threshold={config['queue_threshold']}")

    # Separate output files for reactive run
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tripinfo_path = OUTPUT_DIR / f"reactive_{scenario}_tripinfo.xml"
    queue_path = OUTPUT_DIR / f"reactive_{scenario}_queue.xml"
    summary_path = OUTPUT_DIR / f"reactive_{scenario}_summary.xml"

    # Start SUMO via TraCI
    sumo_cmd = [
        "sumo",
        "-c", str(cfg_path),
        "--tripinfo-output", str(tripinfo_path),
        "--queue-output", str(queue_path),
        "--summary-output", str(summary_path),
    ]

    try:
        traci.start(sumo_cmd)
    except Exception as exc:
        print(f"ERROR: TraCI connection failed: {exc}")
        sys.exit(1)

    # Initialize junction tracking states
    states = init_junction_states(JUNCTION_IDS, config["min_green_s"])
    for jid in JUNCTION_IDS:
        traci.trafficlight.setPhaseDuration(jid, config["max_green_s"])

    decision_records = []
    step = 0

    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            sim_time = traci.simulation.getTime()
            traci.simulationStep()

            # Step reactive controller for each junction
            for jid in JUNCTION_IDS:
                record = step_junction(traci, jid, sim_time, states[jid], config)
                decision_records.append(record)

            step += 1
            if step >= 360:
                break
    finally:
        # Safely close TraCI
        traci.close()

    print(f"SUMO reactive run completed for '{scenario}' ({len(decision_records)} decision steps)")

    # Check output files exist
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
    metrics = calc_metrics(trips, queue_records, scenario, controller="reactive")

    # Save CSVs
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    save_summary_csv(metrics, RESULTS_DIR / f"reactive_{scenario}_summary.csv")
    save_trips_csv(trips, RESULTS_DIR / f"reactive_{scenario}_trips.csv")
    save_queues_csv(queue_records, RESULTS_DIR / f"reactive_{scenario}_queues.csv")

    # Save decision log
    decision_log_path = RESULTS_DIR / f"reactive_{scenario}_decisions.csv"
    save_decision_log(decision_records, decision_log_path)

    print(f"  Results saved to {RESULTS_DIR}/reactive_{scenario}_*.csv")
    print(f"  throughput={metrics['throughput']}  avg_wait={metrics['average_waiting_time']}s  "
          f"p95_wait={metrics['p95_waiting_time']}s  avg_travel={metrics['average_travel_time']}s  "
          f"mean_queue={metrics['mean_queue_length']}  max_queue={metrics['maximum_queue_length']}")

    if "emergency_delay" in metrics:
        print(f"  emergency_delay(emerg_1)={metrics['emergency_delay']}s")

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="TrafficTwin safe queue-reactive controller runner")
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
    args = parser.parse_args()

    if not args.all and not args.scenario:
        parser.print_help()
        sys.exit(1)

    scenarios = VALID_SCENARIOS if args.all else [args.scenario]
    all_metrics = []

    for sc in scenarios:
        m = run_scenario(sc)
        all_metrics.append(m)

    # Print summary table
    print("\n=== Queue-Reactive Controller Summary ===")
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
