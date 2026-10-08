#!/usr/bin/env python3
"""TrafficTwin AI — Spillback-Aware Controller Runner (Module M6).

Runs one or all SUMO scenarios headlessly with TraCI and the spillback controller,
logs decisions, parses output files, calculates metrics, and saves CSV results.

Usage:
    python experiments/run_spillback.py --scenario blocked_downstream
    python experiments/run_spillback.py --scenario normal
    python experiments/run_spillback.py --all
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
from experiments.reactive_controller import init_junction_states
from experiments.spillback_controller import (
    load_spillback_config,
    step_spillback_junction,
)

# Paths relative to project root
SCENARIOS_DIR = Path("sumo/scenarios")
OUTPUT_DIR = Path("sumo/output")
RESULTS_DIR = Path("data/output/metrics")

VALID_SCENARIOS = ["normal", "rush", "blocked_downstream", "ambulance"]
JUNCTION_IDS = ["J1", "J2", "J3", "J4"]


def save_spillback_decision_log(records: list[dict], output_path: Path) -> None:
    """Save spillback controller decision records to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "timestamp",
        "junction_id",
        "current_phase",
        "queue_main",
        "queue_cross",
        "downstream_edge",
        "downstream_occupancy",
        "spillback_risk",
        "action",
        "reason",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)


def compute_spillback_metrics(records: list[dict]) -> dict:
    """Calculate spillback-specific metrics from decision logs."""
    spillback_blocks = 0
    max_occupancy = 0.0
    critical_timestamps = set()
    protected_transitions = 0

    for rec in records:
        occ = float(rec.get("downstream_occupancy", 0.0))
        if occ > max_occupancy:
            max_occupancy = occ

        if rec.get("spillback_risk") == "CRITICAL":
            critical_timestamps.add(rec.get("timestamp"))

        action = rec.get("action", "")
        if action == "SPILLBACK_BLOCK":
            spillback_blocks += 1
            protected_transitions += 1

    return {
        "spillback_blocks": spillback_blocks,
        "max_downstream_occupancy": round(max_occupancy, 3),
        "critical_downstream_seconds": len(critical_timestamps),
        "protected_transitions": protected_transitions,
    }


def run_scenario(scenario: str) -> dict:
    """Run SUMO with spillback controller for one scenario and return metrics."""
    cfg_path = SCENARIOS_DIR / f"corridor_{scenario}.sumocfg"
    if not cfg_path.exists():
        print(f"ERROR: Config not found: {cfg_path}")
        sys.exit(1)

    print(f"\n--- Running spillback controller: {scenario} ---")

    # Load configuration
    config = load_spillback_config()
    print(
        f"  Loaded config: min_green={config['min_green_s']}s, max_green={config['max_green_s']}s, "
        f"warning_th={config['warning_threshold']}, critical_th={config['critical_threshold']}"
    )

    # Output paths
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tripinfo_path = OUTPUT_DIR / f"spillback_{scenario}_tripinfo.xml"
    queue_path = OUTPUT_DIR / f"spillback_{scenario}_queue.xml"
    summary_path = OUTPUT_DIR / f"spillback_{scenario}_summary.xml"

    # Start SUMO via TraCI
    sumo_cmd = [
        "sumo",
        "-c",
        str(cfg_path),
        "--tripinfo-output",
        str(tripinfo_path),
        "--queue-output",
        str(queue_path),
        "--summary-output",
        str(summary_path),
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

            # Step spillback controller for each junction
            for jid in JUNCTION_IDS:
                record = step_spillback_junction(traci, jid, sim_time, states[jid], config)
                decision_records.append(record)

            step += 1
            if step >= 360:
                break
    finally:
        traci.close()

    print(f"SUMO spillback run completed for '{scenario}' ({len(decision_records)} decision steps)")

    # Verify output files
    for p in [tripinfo_path, queue_path, summary_path]:
        if not p.exists():
            print(f"ERROR: Expected output missing: {p}")
            sys.exit(1)

    # Parse outputs
    trips = parse_tripinfo(tripinfo_path)
    queue_records = parse_queue(queue_path)
    summary_steps = parse_summary(summary_path)

    print(
        f"  Parsed: {len(trips)} completed trips, {len(queue_records)} queue snapshots, "
        f"{len(summary_steps)} summary steps"
    )

    # Calculate metrics
    metrics = calc_metrics(trips, queue_records, scenario, controller="spillback")
    sp_metrics = compute_spillback_metrics(decision_records)
    metrics.update(sp_metrics)

    # Save CSVs
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    save_summary_csv(metrics, RESULTS_DIR / f"spillback_{scenario}_summary.csv")
    save_trips_csv(trips, RESULTS_DIR / f"spillback_{scenario}_trips.csv")
    save_queues_csv(queue_records, RESULTS_DIR / f"spillback_{scenario}_queues.csv")

    decision_log_path = RESULTS_DIR / f"spillback_{scenario}_decisions.csv"
    save_spillback_decision_log(decision_records, decision_log_path)

    print(f"  Results saved to {RESULTS_DIR}/spillback_{scenario}_*.csv")
    print(
        f"  throughput={metrics['throughput']}  avg_wait={metrics['average_waiting_time']}s  "
        f"p95_wait={metrics['p95_waiting_time']}s  avg_travel={metrics['average_travel_time']}s  "
        f"mean_queue={metrics['mean_queue_length']}  max_queue={metrics['maximum_queue_length']}"
    )
    print(
        f"  spillback_blocks={metrics['spillback_blocks']}  max_occ={metrics['max_downstream_occupancy']}  "
        f"critical_s={metrics['critical_downstream_seconds']}s  protected_transitions={metrics['protected_transitions']}"
    )

    if "emergency_delay" in metrics:
        print(f"  emergency_delay(emerg_1)={metrics['emergency_delay']}s")

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="TrafficTwin spillback-aware controller runner")
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
    print("\n=== Spillback-Aware Controller Summary ===")
    header = (
        f"{'Scenario':<20} {'Thru':>5} {'AvgWait':>8} {'P95Wait':>8} {'AvgTrav':>8} "
        f"{'MeanQ':>7} {'MaxQ':>7} {'SP_Blocks':>10} {'MaxOcc':>7}"
    )
    print(header)
    print("-" * len(header))
    for m in all_metrics:
        print(
            f"{m['scenario']:<20} {m['throughput']:>5} "
            f"{m['average_waiting_time']:>8.1f} {m['p95_waiting_time']:>8.1f} "
            f"{m['average_travel_time']:>8.1f} {m['mean_queue_length']:>7.2f} "
            f"{m['maximum_queue_length']:>7.2f} {m['spillback_blocks']:>10} "
            f"{m['max_downstream_occupancy']:>7.2f}"
        )


if __name__ == "__main__":
    main()
