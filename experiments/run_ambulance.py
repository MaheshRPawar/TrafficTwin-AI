#!/usr/bin/env python3
"""TrafficTwin AI — M7 Fairness + Staged Ambulance Priority + Recovery Runner.

Runs SUMO corridor scenarios headlessly with TraCI and the integrated M7 controller,
tracking fairness debt, staged emergency preemption, and post-emergency recovery.
Generates metrics CSVs and audit logs.

Usage:
    python experiments/run_ambulance.py --scenario ambulance
    python experiments/run_ambulance.py --all
"""

import argparse
import csv
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import traci

from experiments.emergency_controller import (
    AmbulancePreemptionManager,
    FairnessTracker,
    PostEmergencyRecoveryManager,
    load_m7_config,
    step_m7_junction,
)
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

SCENARIOS_DIR = Path("sumo/scenarios")
OUTPUT_DIR = Path("sumo/output")
RESULTS_DIR = Path("data/output/metrics")
SAFETY_DIR = Path("data/output/safety")
FAIRNESS_DIR = Path("data/output/fairness")

VALID_SCENARIOS = ["ambulance", "normal", "rush", "blocked_downstream"]
JUNCTION_IDS = ["J1", "J2", "J3", "J4"]


def save_emergency_decision_log(records: list[dict], output_path: Path) -> None:
    """Save emergency and controller decision records to a CSV file."""
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
        "cross_debt",
        "cross_starvation_risk",
        "emergency_status",
        "recovery_active",
        "action",
        "reason",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)


def save_fairness_audit_log(records: list[dict], output_path: Path) -> None:
    """Save fairness audit records to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "timestamp",
        "junction_id",
        "cross_debt",
        "cross_starvation_risk",
        "queue_cross",
        "action",
        "reason",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for r in records:
            writer.writerow({
                "timestamp": r.get("timestamp"),
                "junction_id": r.get("junction_id"),
                "cross_debt": r.get("cross_debt"),
                "cross_starvation_risk": r.get("cross_starvation_risk"),
                "queue_cross": r.get("queue_cross"),
                "action": r.get("action"),
                "reason": r.get("reason"),
            })


def compute_m7_metrics(
    trips: list[dict],
    decision_records: list[dict],
    amb_manager: AmbulancePreemptionManager,
    rec_manager: PostEmergencyRecoveryManager,
) -> dict:
    """Calculate specialized M7 fairness, ambulance, and recovery metrics."""
    # Emergency delay and ambulance travel time
    emergency_delay = None
    ambulance_travel_time = None
    cross_road_delays: list[float] = []

    for trip in trips:
        if trip["id"] == "emerg_1":
            emergency_delay = trip["waiting_time"]
            ambulance_travel_time = trip["travel_time"]
        elif "cr" in trip["id"] or "cross" in trip.get("route", ""):
            cross_road_delays.append(trip["waiting_time"])

    avg_cross_delay = (
        round(sum(cross_road_delays) / len(cross_road_delays), 2)
        if cross_road_delays
        else 0.0
    )

    # Fairness and recovery stats
    max_debt = 0.0
    starvation_events = 0
    staged_priority_count = 0
    recovery_active_steps = 0

    for r in decision_records:
        debt = float(r.get("cross_debt", 0.0))
        if debt > max_debt:
            max_debt = debt
        if r.get("cross_starvation_risk"):
            starvation_events += 1
        if r.get("emergency_status") == "PRIORITY_STAGED":
            staged_priority_count += 1
        if r.get("recovery_active"):
            recovery_active_steps += 1

    recovery_duration = 0.0
    if amb_manager.exit_time is not None and amb_manager.entry_time is not None:
        recovery_duration = round(recovery_active_steps / len(JUNCTION_IDS), 1)

    return {
        "emergency_delay": emergency_delay if emergency_delay is not None else 0.0,
        "ambulance_travel_time": ambulance_travel_time if ambulance_travel_time is not None else 0.0,
        "cross_road_delay": avg_cross_delay,
        "recovery_duration": recovery_duration,
        "peak_fairness_debt": round(max_debt, 2),
        "starvation_risk_events": starvation_events,
        "staged_priority_steps": staged_priority_count,
        "recovery_actions": rec_manager.total_recovery_actions,
    }


def run_ambulance_scenario(scenario: str = "ambulance") -> dict:
    """Execute SUMO simulation with M7 integrated intelligence controller."""
    cfg_path = SCENARIOS_DIR / f"corridor_{scenario}.sumocfg"
    if not cfg_path.exists():
        print(f"ERROR: Scenario configuration not found: {cfg_path}")
        sys.exit(1)

    print("\n==================================================")
    print(f"  RUNNING M7 INTELLIGENCE CONTROLLER: {scenario.upper()}")
    print("==================================================")

    config = load_m7_config()
    print(
        f"  Parameters: min_green={config['min_green_s']}s, max_green={config['max_green_s']}s, "
        f"lead_time={config['lead_time_s']}s, recovery_max={config['recovery_max_green_s']}s, "
        f"starvation_th={config['starvation_threshold']}"
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tripinfo_path = OUTPUT_DIR / f"m7_{scenario}_tripinfo.xml"
    queue_path = OUTPUT_DIR / f"m7_{scenario}_queue.xml"
    summary_path = OUTPUT_DIR / f"m7_{scenario}_summary.xml"

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

    # Initialize sub-managers and junction states
    fairness_tracker = FairnessTracker(JUNCTION_IDS, config)
    ambulance_manager = AmbulancePreemptionManager(config)
    recovery_manager = PostEmergencyRecoveryManager(config)
    states = init_junction_states(JUNCTION_IDS, config["min_green_s"])

    for jid in JUNCTION_IDS:
        traci.trafficlight.setPhaseDuration(jid, config["max_green_s"])

    decision_records = []
    step = 0

    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            sim_time = traci.simulation.getTime()
            traci.simulationStep()

            # Global ambulance detection on corridor
            amb_info = ambulance_manager.detect_ambulance(traci, sim_time)

            # Step each junction
            for jid in JUNCTION_IDS:
                record = step_m7_junction(
                    traci_client=traci,
                    junction_id=jid,
                    sim_time=sim_time,
                    state=states[jid],
                    config=config,
                    fairness_tracker=fairness_tracker,
                    ambulance_manager=ambulance_manager,
                    recovery_manager=recovery_manager,
                    amb_info=amb_info,
                )
                decision_records.append(record)

            step += 1
            if step >= 360:
                break
    finally:
        traci.close()

    print(f"  Completed {step} simulation steps ({len(decision_records)} junction decisions).")

    # Verify and parse output files
    trips = parse_tripinfo(tripinfo_path)
    queue_records = parse_queue(queue_path)
    parse_summary(summary_path)

    # Calculate metrics
    metrics = calc_metrics(trips, queue_records, scenario, controller="m7_intelligence")
    m7_stats = compute_m7_metrics(trips, decision_records, ambulance_manager, recovery_manager)
    metrics.update(m7_stats)

    # Save CSV files
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    SAFETY_DIR.mkdir(parents=True, exist_ok=True)
    FAIRNESS_DIR.mkdir(parents=True, exist_ok=True)

    save_summary_csv(metrics, RESULTS_DIR / f"m7_{scenario}_summary.csv")
    save_trips_csv(trips, RESULTS_DIR / f"m7_{scenario}_trips.csv")
    save_queues_csv(queue_records, RESULTS_DIR / f"m7_{scenario}_queues.csv")

    decisions_path = SAFETY_DIR / f"emergency_{scenario}_decisions.csv"
    save_emergency_decision_log(decision_records, decisions_path)

    fairness_path = FAIRNESS_DIR / f"fairness_audit_{scenario}.csv"
    save_fairness_audit_log(decision_records, fairness_path)

    print(f"  Artifacts saved to {RESULTS_DIR} and {SAFETY_DIR}")
    print(
        f"  Throughput: {metrics['throughput']} trips | Avg Wait: {metrics['average_waiting_time']}s | "
        f"Avg Travel: {metrics['average_travel_time']}s"
    )
    if scenario == "ambulance":
        print(
            f"  [AMBULANCE] Travel Time: {metrics['ambulance_travel_time']}s | "
            f"Emergency Delay: {metrics['emergency_delay']}s | Cross-Road Delay: {metrics['cross_road_delay']}s"
        )
        print(
            f"  [RECOVERY] Duration: {metrics['recovery_duration']}s | "
            f"Recovery Actions: {metrics['recovery_actions']} | Peak Debt: {metrics['peak_fairness_debt']}"
        )

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="TrafficTwin M7 Intelligence Controller Runner")
    parser.add_argument(
        "--scenario",
        choices=VALID_SCENARIOS,
        default="ambulance",
        help="Scenario to run (default: ambulance)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all scenarios",
    )
    args = parser.parse_args()

    scenarios = VALID_SCENARIOS if args.all else [args.scenario]
    all_metrics = []

    for sc in scenarios:
        m = run_ambulance_scenario(sc)
        all_metrics.append(m)

    print("\n==================================================")
    print("         MODULE M7 SUMMARY REPORT")
    print("==================================================")
    header = f"{'Scenario':<20} {'Thru':>5} {'AvgWait':>8} {'AmbTravel':>10} {'AmbDelay':>9} {'CrossDelay':>11} {'PeakDebt':>9}"
    print(header)
    print("-" * len(header))
    for m in all_metrics:
        print(
            f"{m['scenario']:<20} {m['throughput']:>5} "
            f"{m['average_waiting_time']:>8.1f} {m.get('ambulance_travel_time', 0.0):>10.1f} "
            f"{m.get('emergency_delay', 0.0):>9.1f} {m.get('cross_road_delay', 0.0):>11.1f} "
            f"{m.get('peak_fairness_debt', 0.0):>9.2f}"
        )


if __name__ == "__main__":
    main()
