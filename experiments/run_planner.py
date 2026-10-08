#!/usr/bin/env python3
"""TrafficTwin AI — Digital Twin Plan A/B/C Planner Runner (Module M9).

Runs SUMO corridor headlessly with TraCI and the Digital Twin Plan A/B/C Evaluator,
testing safe control alternatives and logging transparent scoring breakdowns.

Usage:
    python experiments/run_planner.py --scenario rush
    python experiments/run_planner.py --scenario blocked_downstream
    python experiments/run_planner.py --all
"""

import argparse
import csv
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import traci

from backend.app.guards.safety_firewall import validate_action
from backend.app.planner.evaluator import DigitalTwinPlanner, load_planner_config
from backend.app.planner.models import CorridorSnapshot, JunctionSnapshot
from experiments.emergency_controller import (
    AmbulancePreemptionManager,
    FairnessTracker,
    load_m7_config,
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
from experiments.reactive_controller import (
    NEXT_CLEARANCE_PHASE,
    get_incoming_queues,
    init_junction_states,
)
from experiments.spillback_controller import (
    apply_spillback_guard,
    get_downstream_state,
)

SCENARIOS_DIR = Path("sumo/scenarios")
OUTPUT_DIR = Path("sumo/output")
RESULTS_DIR = Path("data/output/metrics")
SAFETY_DIR = Path("data/output/safety")

VALID_SCENARIOS = ["rush", "blocked_downstream", "normal", "ambulance"]
JUNCTION_IDS = ["J1", "J2", "J3", "J4"]


def save_planner_decision_log(records: list[dict], output_path: Path) -> None:
    """Save evaluator plan selection decisions to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "timestamp",
        "scenario",
        "selected_plan",
        "plan_a_score",
        "plan_b_score",
        "plan_c_score",
        "delay_score",
        "queue_score",
        "spillback_score",
        "fairness_score",
        "emergency_score",
        "total_score",
        "reason",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)


def run_planner_scenario(scenario: str) -> dict:
    """Execute SUMO corridor run evaluated by Digital Twin Planner."""
    cfg_path = SCENARIOS_DIR / f"corridor_{scenario}.sumocfg"
    if not cfg_path.exists():
        print(f"ERROR: Config not found: {cfg_path}")
        sys.exit(1)

    print("\n==================================================")
    print(f"  RUNNING DIGITAL TWIN PLANNER: {scenario.upper()}")
    print("==================================================")

    config = load_m7_config()
    planner_cfg = load_planner_config()
    planner = DigitalTwinPlanner(planner_cfg)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tripinfo_path = OUTPUT_DIR / f"planner_{scenario}_tripinfo.xml"
    queue_path = OUTPUT_DIR / f"planner_{scenario}_queue.xml"
    summary_path = OUTPUT_DIR / f"planner_{scenario}_summary.xml"

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

    fairness = FairnessTracker(JUNCTION_IDS, config)
    amb_manager = AmbulancePreemptionManager(config)
    states = init_junction_states(JUNCTION_IDS, config["min_green_s"])

    for jid in JUNCTION_IDS:
        traci.trafficlight.setPhaseDuration(jid, config["max_green_s"])

    decision_records = []
    plan_counts = {"PLAN_A": 0, "PLAN_B": 0, "PLAN_C": 0, "SAFE_ADAPTIVE": 0}
    step = 0

    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            sim_time = traci.simulation.getTime()
            traci.simulationStep()

            amb_info = amb_manager.detect_ambulance(traci, sim_time)

            # 1. Build CorridorSnapshot
            junction_snaps = {}
            for jid in JUNCTION_IDS:
                cur_phase = traci.trafficlight.getPhase(jid)
                if cur_phase != states[jid]["last_phase"]:
                    states[jid]["last_phase"] = cur_phase
                    states[jid]["phase_start"] = sim_time
                    if cur_phase in (0, 3):
                        states[jid]["allocated_green"] = config["min_green_s"]
                        traci.trafficlight.setPhaseDuration(jid, config["max_green_s"])

                q_main, q_cross = get_incoming_queues(traci, jid)
                downstream = get_downstream_state(traci, jid, config)
                f_state = fairness.update(traci, jid, cur_phase, sim_time)

                p_status, _, _ = amb_manager.evaluate_priority_request(
                    jid, amb_info, downstream, cur_phase, sim_time - states[jid]["phase_start"]
                )

                elapsed_green = sim_time - states[jid]["phase_start"] if cur_phase in (0, 3) else 0.0

                junction_snaps[jid] = JunctionSnapshot(
                    junction_id=jid,
                    current_phase=cur_phase,
                    elapsed_green_s=elapsed_green,
                    queue_main=q_main,
                    queue_cross=q_cross,
                    downstream_edge=downstream["edge_id"],
                    downstream_occupancy=downstream["occupancy"],
                    spillback_risk=downstream["risk"],
                    cross_fairness_debt=f_state["cross_debt"],
                    starvation_risk=f_state["cross_starvation_risk"],
                    emergency_status=p_status,
                )

            corridor_snapshot = CorridorSnapshot(
                timestamp=sim_time,
                scenario=scenario,
                controller_mode="PREDICTIVE",
                junctions=junction_snaps,
            )

            # 2. Digital Twin Plan Evaluation
            eval_result = planner.evaluate(corridor_snapshot)
            sel_plan = eval_result.selected_plan
            plan_counts[eval_result.selected_plan_id] = (
                plan_counts.get(eval_result.selected_plan_id, 0) + 1
            )

            # 3. Actuate selected plan through M6 -> M5 -> TraCI
            for jid in JUNCTION_IDS:
                cur_phase = traci.trafficlight.getPhase(jid)
                if cur_phase not in (0, 3):
                    continue

                raw_action = sel_plan.proposed_actions.get(jid, "KEEP_GREEN")
                green_time = sim_time - states[jid]["phase_start"]
                downstream = get_downstream_state(traci, jid, config)

                # M6 Downstream Guard
                m6_action, m6_reason, signal_action = apply_spillback_guard(
                    proposed_action=raw_action,
                    proposed_reason=f"planner_{eval_result.selected_plan_id}",
                    downstream_state=downstream,
                    current_phase=cur_phase,
                    green_duration=green_time,
                    min_green=config["min_green_s"],
                    config=config,
                )

                # M5 Safety Firewall
                fw_action = {
                    "junction_id": jid,
                    "current_phase": cur_phase,
                    "requested_phase": (
                        NEXT_CLEARANCE_PHASE.get(cur_phase)
                        if signal_action == "START_TRANSITION"
                        else cur_phase
                    ),
                    "action": signal_action,
                    "timestamp": sim_time,
                    "elapsed_green_s": green_time,
                    "extension_s": (
                        config["extension_step_s"] if signal_action == "EXTEND_GREEN" else 0.0
                    ),
                    "reason": m6_reason,
                }
                fw_result = validate_action(fw_action, config)

                if fw_result["allowed"]:
                    if signal_action == "START_TRANSITION":
                        yellow_phase = NEXT_CLEARANCE_PHASE[cur_phase]
                        traci.trafficlight.setPhase(jid, yellow_phase)
                    elif signal_action == "EXTEND_GREEN":
                        if states[jid]["allocated_green"] < config["max_green_s"]:
                            step_len = min(
                                config["extension_step_s"],
                                config["max_green_s"] - states[jid]["allocated_green"],
                            )
                            states[jid]["allocated_green"] += step_len

            # Record plan scores
            scores = {p.plan_id: p.total_score for p in eval_result.candidate_plans}
            decision_records.append({
                "timestamp": sim_time,
                "scenario": scenario,
                "selected_plan": eval_result.selected_plan_id,
                "plan_a_score": scores.get("PLAN_A", 0.0),
                "plan_b_score": scores.get("PLAN_B", 0.0),
                "plan_c_score": scores.get("PLAN_C", 0.0),
                "delay_score": sel_plan.delay_score,
                "queue_score": sel_plan.queue_score,
                "spillback_score": sel_plan.spillback_score,
                "fairness_score": sel_plan.fairness_score,
                "emergency_score": sel_plan.emergency_score,
                "total_score": sel_plan.total_score,
                "reason": eval_result.selection_reason,
            })

            step += 1
            if step >= 360:
                break
    finally:
        traci.close()

    print(f"  Simulation complete ({step} steps). Plan selections: {plan_counts}")

    # Parse and calculate metrics
    trips = parse_tripinfo(tripinfo_path)
    queue_records = parse_queue(queue_path)
    parse_summary(summary_path)

    metrics = calc_metrics(trips, queue_records, scenario, controller="m9_planner")
    metrics["plan_a_selections"] = plan_counts.get("PLAN_A", 0)
    metrics["plan_b_selections"] = plan_counts.get("PLAN_B", 0)
    metrics["plan_c_selections"] = plan_counts.get("PLAN_C", 0)
    metrics["fallback_selections"] = plan_counts.get("SAFE_ADAPTIVE", 0)

    # Save CSV outputs
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    SAFETY_DIR.mkdir(parents=True, exist_ok=True)

    save_summary_csv(metrics, RESULTS_DIR / f"planner_{scenario}_summary.csv")
    save_trips_csv(trips, RESULTS_DIR / f"planner_{scenario}_trips.csv")
    save_queues_csv(queue_records, RESULTS_DIR / f"planner_{scenario}_queues.csv")
    save_planner_decision_log(decision_records, SAFETY_DIR / f"planner_{scenario}_decisions.csv")

    print(
        f"  Throughput: {metrics['throughput']} trips | Avg Wait: {metrics['average_waiting_time']}s | "
        f"Avg Travel: {metrics['average_travel_time']}s"
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="TrafficTwin Digital Twin Plan A/B/C Runner")
    parser.add_argument(
        "--scenario",
        choices=VALID_SCENARIOS,
        default="rush",
        help="Scenario to run (default: rush)",
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
        m = run_planner_scenario(sc)
        all_metrics.append(m)

    print("\n==================================================")
    print("         MODULE M9 PLANNER SUMMARY REPORT")
    print("==================================================")
    header = f"{'Scenario':<20} {'Thru':>5} {'AvgWait':>8} {'PlanA':>7} {'PlanB':>7} {'PlanC':>7} {'Fallback':>9}"
    print(header)
    print("-" * len(header))
    for m in all_metrics:
        print(
            f"{m['scenario']:<20} {m['throughput']:>5} "
            f"{m['average_waiting_time']:>8.1f} {m['plan_a_selections']:>7} "
            f"{m['plan_b_selections']:>7} {m['plan_c_selections']:>7} "
            f"{m['fallback_selections']:>9}"
        )


if __name__ == "__main__":
    main()
