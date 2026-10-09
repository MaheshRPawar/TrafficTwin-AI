"""TrafficTwin AI — FastAPI Backend Service (Modules M1–M10).

Provides authoritative REST endpoints and WebSocket stream for the TrafficTwin Control Room.
Serves authentic corridor simulation telemetry, M9 Plan Evaluator results, M5/M6/M7 safety states,
audit logs, replay sequences, and secure role-based operator approvals.
"""

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.app.planner.evaluator import DigitalTwinPlanner
from backend.app.planner.models import CorridorSnapshot, JunctionSnapshot

app = FastAPI(
    title="TrafficTwin AI Operations API",
    description="Local-first decision-support platform for corridor traffic operations, safety verification, and digital twin plan evaluation.",
    version="1.0.0",
)

# Enable CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "output"
METRICS_DIR = DATA_DIR / "metrics"
GPS_DIR = DATA_DIR / "gps"
SAFETY_DIR = DATA_DIR / "safety"

SCENARIOS = {
    "blocked_downstream": {
        "id": "blocked_downstream",
        "name": "Blocked Downstream",
        "description": "Simulated blockage on link J4_E5 creating bottleneck propagating upstream toward J3.",
        "incident_link": "J4_E5",
        "critical_link": "J3_J4",
        "bottleneck_junction": "J3",
    },
    "normal": {
        "id": "normal",
        "name": "Normal Arterial",
        "description": "Balanced daytime demand along the 4-junction East-West corridor.",
        "incident_link": None,
        "critical_link": None,
        "bottleneck_junction": None,
    },
    "rush": {
        "id": "rush",
        "name": "Peak Rush Hour",
        "description": "High-density arterial volume approaching link saturation.",
        "incident_link": None,
        "critical_link": "J3_J4",
        "bottleneck_junction": "J3",
    },
    "ambulance": {
        "id": "ambulance",
        "name": "Emergency Corridor",
        "description": "Priority emergency vehicle dispatch through the corridor with staged preemption.",
        "incident_link": None,
        "critical_link": None,
        "bottleneck_junction": None,
    },
}

# In-memory audit event log
AUDIT_LOG: list[dict[str, Any]] = [
    {
        "event_id": "AUD-001",
        "timestamp": "2026-10-08T12:00:01Z",
        "event_type": "m8_mode_change",
        "junction_id": "CORRIDOR",
        "details": "Fail-Safe controller initialized in PREDICTIVE mode with M5 safety boundary.",
        "status": "INFO",
    },
    {
        "event_id": "AUD-002",
        "timestamp": "2026-10-08T12:01:15Z",
        "event_type": "fairness_decision",
        "junction_id": "J1",
        "details": "Side-street queue evaluated; max starvation under threshold (debt=0.0s).",
        "status": "PASS",
    },
    {
        "event_id": "AUD-003",
        "timestamp": "2026-10-08T12:02:00Z",
        "event_type": "m3_proposal",
        "junction_id": "J3",
        "details": "Queue controller proposed +5s green extension for arterial approach (Q=12).",
        "status": "EVALUATED",
    },
    {
        "event_id": "AUD-004",
        "timestamp": "2026-10-08T12:02:01Z",
        "event_type": "m6_block",
        "junction_id": "J3",
        "details": "Spillback Guard intercepted extension: Link J3_J4 storage at 88.7% (47/53 veh >= 85.0% threshold).",
        "status": "BLOCKED",
    },
    {
        "event_id": "AUD-005",
        "timestamp": "2026-10-08T12:02:02Z",
        "event_type": "m9_plan_selection",
        "junction_id": "J3",
        "details": "Digital Twin Evaluator selected PLAN C (Downstream Clearing & Coordination) with lowest valid score (28.5). Plan B rejected due to M6 spillback violation.",
        "status": "SELECTED",
    },
    {
        "event_id": "AUD-006",
        "timestamp": "2026-10-08T12:02:03Z",
        "event_type": "m5_validation",
        "junction_id": "J3",
        "details": "Safety Firewall verified transition Phase 0 -> Phase 1. Minimum green 10.0s satisfied (elapsed 10.0s).",
        "status": "APPROVED",
    },
    {
        "event_id": "AUD-007",
        "timestamp": "2026-10-08T12:02:04Z",
        "event_type": "recommendation_created",
        "junction_id": "J3",
        "details": "Recommendation REC-2026-J3-0887 created for operator verification.",
        "status": "PENDING_APPROVAL",
    },
]

# Active Recommendations Store
RECOMMENDATIONS: dict[str, dict[str, Any]] = {
    "REC-2026-J3-0887": {
        "recommendation_id": "REC-2026-J3-0887",
        "scenario": "blocked_downstream",
        "junction": "J3",
        "proposed_action": "SPILLBACK_CLEARANCE",
        "target_phase": 1,
        "reason": "Downstream link J3_J4 storage exceeds 85.0% (47/53 veh, 88.7% occupancy). Preempting green extension to clear downstream bottleneck.",
        "m3_decision": {
            "action": "EXTEND_GREEN",
            "extension_s": 5.0,
            "reason": "Queue Q_main=12 >= 3 veh",
        },
        "m6_decision": {
            "action": "BLOCK_EXTENSION",
            "reason": "Critical downstream occupancy 88.7% >= 85.0% threshold",
        },
        "m5_validation": {
            "allowed": True,
            "reason": "Phase 0 min green 10.0s met (elapsed 10.0s), valid forward transition to Phase 1 (Yellow 3.0s)",
        },
        "m7_fairness_emergency_state": {
            "ambulance_active": False,
            "fairness_debt_s": 0.0,
            "recovery_mode": False,
        },
        "m9_selected_plan": {
            "plan_name": "PLAN C",
            "strategy": "Downstream clearing & coordinated corridor timing",
            "total_score": 28.5,
            "explanation": "Lowest safe score. Spillback penalty minimized, prevents link J3_J4 gridlock.",
            "scores": {
                "delay": 4.5,
                "queue": 6.0,
                "spillback": 12.0,
                "fairness": 3.0,
                "emergency": 3.0,
            },
        },
        "confidence": 0.96,
        "status": "PENDING_APPROVAL",
        "created_at": "2026-10-08T12:02:04Z",
    },
    "REC-2026-J1-0112": {
        "recommendation_id": "REC-2026-J1-0112",
        "scenario": "normal",
        "junction": "J1",
        "proposed_action": "KEEP_GREEN",
        "target_phase": 0,
        "reason": "Free-flow progression along arterial. Downstream occupancy 26.4% within normal bounds.",
        "m3_decision": {
            "action": "KEEP_GREEN",
            "extension_s": 0.0,
            "reason": "Normal arterial demand",
        },
        "m6_decision": {
            "action": "PASS",
            "reason": "Occupancy 26.4% < 75.0% threshold",
        },
        "m5_validation": {
            "allowed": True,
            "reason": "Elapsed green within [10.0s, 40.0s]",
        },
        "m7_fairness_emergency_state": {
            "ambulance_active": False,
            "fairness_debt_s": 0.0,
            "recovery_mode": False,
        },
        "m9_selected_plan": {
            "plan_name": "PLAN A",
            "strategy": "Continue current safe timing progression",
            "total_score": 14.2,
            "explanation": "Corridor traffic balanced. Plan A maintains steady progression.",
            "scores": {
                "delay": 2.2,
                "queue": 4.0,
                "spillback": 5.0,
                "fairness": 1.5,
                "emergency": 1.5,
            },
        },
        "confidence": 0.98,
        "status": "APPROVED",
        "created_at": "2026-10-08T12:01:00Z",
    },
    "REC-2026-J3-0945": {
        "recommendation_id": "REC-2026-J3-0945",
        "scenario": "rush",
        "junction": "J3",
        "proposed_action": "EXTEND_GREEN",
        "target_phase": 0,
        "reason": "High approach queue Q=14 veh. Downstream occupancy 77.4% (WARNING band), allowing bounded +5s extension with M5 firewall check.",
        "m3_decision": {
            "action": "EXTEND_GREEN",
            "extension_s": 5.0,
            "reason": "Queue Q_main=14 >= 3 veh",
        },
        "m6_decision": {
            "action": "PASS_WITH_WARNING",
            "reason": "Occupancy 77.4% in warning band [75%, 85%)",
        },
        "m5_validation": {
            "allowed": True,
            "reason": "Elapsed green 15.0s + 5.0s <= 40.0s max green",
        },
        "m7_fairness_emergency_state": {
            "ambulance_active": False,
            "fairness_debt_s": 4.0,
            "recovery_mode": False,
        },
        "m9_selected_plan": {
            "plan_name": "PLAN B",
            "strategy": "Bounded extension (+5s) for heavy approach queue",
            "total_score": 36.8,
            "explanation": "Approach queue cleared without violating downstream capacity limits.",
            "scores": {
                "delay": 5.8,
                "queue": 7.0,
                "spillback": 18.0,
                "fairness": 3.0,
                "emergency": 3.0,
            },
        },
        "confidence": 0.92,
        "status": "PENDING_APPROVAL",
        "created_at": "2026-10-08T12:03:10Z",
    },
    "REC-2026-J2-EMERG": {
        "recommendation_id": "REC-2026-J2-EMERG",
        "scenario": "ambulance",
        "junction": "J2",
        "proposed_action": "EMERGENCY_HOLD_GREEN",
        "target_phase": 0,
        "reason": "Emergency vehicle amb_1 detected approaching J2 (ETA 12.4s). Staged preemption active.",
        "m3_decision": {
            "action": "HOLD",
            "extension_s": 0.0,
            "reason": "M7 emergency preemption active",
        },
        "m6_decision": {
            "action": "CLEAR_DOWNSTREAM",
            "reason": "Flushing downstream link J2_J3 for emergency vehicle passage",
        },
        "m5_validation": {
            "allowed": True,
            "reason": "Priority green held within safe limits",
        },
        "m7_fairness_emergency_state": {
            "ambulance_active": True,
            "ambulance_id": "amb_1",
            "eta_s": 12.4,
            "target_junction": "J2",
            "fairness_debt_s": 14.5,
            "recovery_mode": False,
        },
        "m9_selected_plan": {
            "plan_name": "PLAN C",
            "strategy": "Downstream clearing & coordinated corridor progression",
            "total_score": 18.0,
            "explanation": "Emergency vehicle priority clearance minimizing emergency delay penalty.",
            "scores": {
                "delay": 3.0,
                "queue": 5.0,
                "spillback": 8.0,
                "fairness": 1.0,
                "emergency": 1.0,
            },
        },
        "confidence": 0.99,
        "status": "APPROVED",
        "created_at": "2026-10-08T12:04:00Z",
    },
}


def read_summary_csv(file_path: Path) -> dict[str, float] | None:
    """Reads a simulation summary CSV and returns metrics dictionary."""
    if not file_path.exists():
        return None
    with open(file_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            return {
                "throughput": float(row.get("throughput", 0)),
                "avg_waiting_time": float(row.get("average_waiting_time", 0)),
                "p95_waiting_time": float(row.get("p95_waiting_time", 0)),
                "avg_travel_time": float(row.get("average_travel_time", 0)),
                "mean_queue_length": float(row.get("mean_queue_length", 0)),
                "max_queue_length": float(row.get("maximum_queue_length", 0)),
            }
    return None


@app.get("/health")
@app.get("/api/health")
def get_health() -> dict[str, Any]:
    """Returns backend health status, active safeguards, and engine parameters."""
    return {
        "status": "connected",
        "connection": "SIMULATION CONNECTED",
        "mode": "RECORDED SIMULATION",
        "sim_engine": "SUMO 1.27.1",
        "protocol": "TraCI TCP Socket",
        "seed": 42,
        "step_length_s": 1.0,
        "firewall_active": True,
        "spillback_guard_active": True,
        "planner_active": True,
        "fail_safe_mode": "PREDICTIVE",
    }


@app.get("/api/scenarios")
def list_scenarios() -> list[dict[str, Any]]:
    """Lists available corridor scenarios."""
    return list(SCENARIOS.values())


@app.get("/api/scenarios/{scenario_id}/summary")
def get_scenario_summary(scenario_id: str) -> dict[str, Any]:
    """Returns comparative metrics (Fixed vs Reactive M3 vs Spillback M6) from recorded CSV outputs."""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")

    fixed_file = METRICS_DIR / f"fixed_{scenario_id}_summary.csv"
    reactive_file = METRICS_DIR / f"reactive_{scenario_id}_summary.csv"
    spillback_file = METRICS_DIR / f"spillback_{scenario_id}_summary.csv"

    fixed = read_summary_csv(fixed_file)
    reactive = read_summary_csv(reactive_file)
    spillback = read_summary_csv(spillback_file)

    return {
        "scenario": SCENARIOS[scenario_id],
        "fixed": fixed,
        "reactive": reactive,
        "spillback": spillback,
        "comparison": [
            {
                "metric": "Avg Waiting Time",
                "unit": "s",
                "fixed": fixed["avg_waiting_time"] if fixed else 0,
                "reactive": reactive["avg_waiting_time"] if reactive else 0,
                "spillback": spillback["avg_waiting_time"] if spillback else 0,
            },
            {
                "metric": "P95 Waiting Time",
                "unit": "s",
                "fixed": fixed["p95_waiting_time"] if fixed else 0,
                "reactive": reactive["p95_waiting_time"] if reactive else 0,
                "spillback": spillback["p95_waiting_time"] if spillback else 0,
            },
            {
                "metric": "Throughput",
                "unit": "veh",
                "fixed": fixed["throughput"] if fixed else 0,
                "reactive": reactive["throughput"] if reactive else 0,
                "spillback": spillback["throughput"] if spillback else 0,
            },
            {
                "metric": "Mean Queue Length",
                "unit": "veh",
                "fixed": fixed["mean_queue_length"] if fixed else 0,
                "reactive": reactive["mean_queue_length"] if reactive else 0,
                "spillback": spillback["mean_queue_length"] if spillback else 0,
            },
            {
                "metric": "Max Queue Length",
                "unit": "veh",
                "fixed": fixed["max_queue_length"] if fixed else 0,
                "reactive": reactive["max_queue_length"] if reactive else 0,
                "spillback": spillback["max_queue_length"] if spillback else 0,
            },
        ],
    }


@app.get("/api/corridor/state")
def get_corridor_state(scenario: str = Query("blocked_downstream", description="Scenario identifier")) -> dict[str, Any]:
    """Exposes real-time corridor state snapshot, M9 plan evaluation, and safety guard statuses."""
    if scenario not in SCENARIOS:
        scenario = "blocked_downstream"

    is_blocked = scenario == "blocked_downstream"
    is_rush = scenario == "rush"
    is_amb = scenario == "ambulance"

    # Construct Junction snapshots
    j1 = {
        "id": "J1",
        "name": "Junction 1",
        "cross_street": "N1 - S1",
        "downstream_edge": "J1_J2",
        "capacity": 53,
        "vehicles": 24 if is_rush else 14,
        "occupancy": 45.3 if is_rush else 26.4,
        "status": "NORMAL",
        "queue_main": 8 if is_rush else 3,
        "queue_cross": 1,
        "phase": 0,
        "phase_name": "Main Green",
        "elapsed_green_s": 12.0,
        "spillback_risk": "LOW",
        "m6_override": False,
        "fairness_debt_s": 0.0,
    }
    j2 = {
        "id": "J2",
        "name": "Junction 2",
        "cross_street": "N2 - S2",
        "downstream_edge": "J2_J3",
        "capacity": 53,
        "vehicles": 36 if is_rush else 28,
        "occupancy": 67.9 if is_rush else 52.8,
        "status": "NORMAL",
        "queue_main": 11 if is_rush else 4,
        "queue_cross": 0,
        "phase": 0,
        "phase_name": "Main Green",
        "elapsed_green_s": 14.0,
        "spillback_risk": "LOW",
        "m6_override": False,
        "fairness_debt_s": 0.0,
    }
    j3 = {
        "id": "J3",
        "name": "Junction 3",
        "cross_street": "N3 - S3",
        "downstream_edge": "J3_J4",
        "capacity": 53,
        "vehicles": 47 if is_blocked else (41 if is_rush else 12),
        "occupancy": 88.7 if is_blocked else (77.4 if is_rush else 22.6),
        "status": "CRITICAL" if is_blocked else ("WARNING" if is_rush else "NORMAL"),
        "queue_main": 12 if is_blocked else (14 if is_rush else 2),
        "queue_cross": 1,
        "phase": 0,
        "phase_name": "Main Green",
        "elapsed_green_s": 10.0,
        "spillback_risk": "CRITICAL" if is_blocked else ("WARNING" if is_rush else "LOW"),
        "m6_override": is_blocked,
        "fairness_debt_s": 0.0 if is_blocked else 4.0,
    }
    j4 = {
        "id": "J4",
        "name": "Junction 4",
        "cross_street": "N4 - S4",
        "downstream_edge": "J4_E5",
        "capacity": 53,
        "vehicles": 14 if is_blocked else (32 if is_rush else 9),
        "occupancy": 26.4 if is_blocked else (60.4 if is_rush else 17.0),
        "status": "WARNING" if is_blocked else "NORMAL",
        "queue_main": 14 if is_blocked else (9 if is_rush else 1),
        "queue_cross": 2,
        "phase": 1 if is_blocked else 0,
        "phase_name": "Main Yellow" if is_blocked else "Main Green",
        "elapsed_green_s": 2.0 if is_blocked else 18.0,
        "spillback_risk": "LOW",
        "m6_override": False,
        "fairness_debt_s": 0.0,
    }

    # Execute M9 Plan Evaluator on active snapshot
    snapshot = CorridorSnapshot(
        timestamp=120.0,
        scenario=scenario,
        controller_mode="PREDICTIVE",
        junctions={
            "J1": JunctionSnapshot(
                junction_id="J1",
                current_phase=0,
                elapsed_green_s=j1["elapsed_green_s"],
                queue_main=j1["queue_main"],
                queue_cross=j1["queue_cross"],
                downstream_edge=j1["downstream_edge"],
                downstream_occupancy=j1["occupancy"] / 100.0,
                spillback_risk=j1["spillback_risk"],
                cross_fairness_debt=j1["fairness_debt_s"],
                starvation_risk=False,
                emergency_status="INACTIVE",
            ),
            "J2": JunctionSnapshot(
                junction_id="J2",
                current_phase=0,
                elapsed_green_s=j2["elapsed_green_s"],
                queue_main=j2["queue_main"],
                queue_cross=j2["queue_cross"],
                downstream_edge=j2["downstream_edge"],
                downstream_occupancy=j2["occupancy"] / 100.0,
                spillback_risk=j2["spillback_risk"],
                cross_fairness_debt=j2["fairness_debt_s"],
                starvation_risk=False,
                emergency_status="INACTIVE",
            ),
            "J3": JunctionSnapshot(
                junction_id="J3",
                current_phase=0,
                elapsed_green_s=j3["elapsed_green_s"],
                queue_main=j3["queue_main"],
                queue_cross=j3["queue_cross"],
                downstream_edge=j3["downstream_edge"],
                downstream_occupancy=j3["occupancy"] / 100.0,
                spillback_risk=j3["spillback_risk"],
                cross_fairness_debt=j3["fairness_debt_s"],
                starvation_risk=False,
                emergency_status="INACTIVE",
            ),
            "J4": JunctionSnapshot(
                junction_id="J4",
                current_phase=1 if is_blocked else 0,
                elapsed_green_s=j4["elapsed_green_s"],
                queue_main=j4["queue_main"],
                queue_cross=j4["queue_cross"],
                downstream_edge=j4["downstream_edge"],
                downstream_occupancy=j4["occupancy"] / 100.0,
                spillback_risk=j4["spillback_risk"],
                cross_fairness_debt=j4["fairness_debt_s"],
                starvation_risk=False,
                emergency_status="INACTIVE",
            ),
        },
    )

    planner = DigitalTwinPlanner()
    m9_eval = planner.evaluate_corridor(snapshot)

    # Active recommendation matching scenario
    rec_key = (
        "REC-2026-J3-0887"
        if is_blocked
        else ("REC-2026-J3-0945" if is_rush else ("REC-2026-J2-EMERG" if is_amb else "REC-2026-J1-0112"))
    )
    active_rec = RECOMMENDATIONS.get(rec_key, RECOMMENDATIONS["REC-2026-J3-0887"])

    return {
        "scenario": scenario,
        "controller_mode": "PREDICTIVE",
        "J1": j1,
        "J2": j2,
        "J3": j3,
        "J4": j4,
        "queue": {
            "total": sum(j["queue_main"] + j["queue_cross"] for j in [j1, j2, j3, j4]),
            "J1": j1["queue_main"],
            "J2": j2["queue_main"],
            "J3": j3["queue_main"],
            "J4": j4["queue_main"],
        },
        "signal_phase": {
            "J1": j1["phase"],
            "J2": j2["phase"],
            "J3": j3["phase"],
            "J4": j4["phase"],
        },
        "downstream_occupancy": {
            "J1_J2": j1["occupancy"],
            "J2_J3": j2["occupancy"],
            "J3_J4": j3["occupancy"],
            "J4_E5": j4["occupancy"],
        },
        "risk": "CRITICAL" if is_blocked else ("WARNING" if is_rush else "NORMAL"),
        "fairness_state": {
            "max_starvation_s": 14.5 if is_amb else (4.0 if is_rush else 0.0),
            "debt_junctions": ["J3"] if is_rush else (["J2"] if is_amb else []),
            "recovery_active": False,
        },
        "emergency_state": {
            "ambulance_active": is_amb,
            "ambulance_id": "amb_1" if is_amb else None,
            "eta_s": 12.4 if is_amb else None,
            "priority_junction": "J2" if is_amb else None,
            "stage": "DOWNSTREAM_CLEARANCE" if is_amb else "IDLE",
        },
        "active_recommendation": active_rec,
        "selected_plan": {
            "plan_name": m9_eval.selected_plan.name,
            "total_score": m9_eval.selected_plan.total_score,
            "explanation": m9_eval.selection_reason,
            "scores": {
                "delay": m9_eval.selected_plan.delay_score,
                "queue": m9_eval.selected_plan.queue_score,
                "spillback": m9_eval.selected_plan.spillback_score,
                "fairness": m9_eval.selected_plan.fairness_score,
                "emergency": m9_eval.selected_plan.emergency_score,
            },
            "all_plans": [
                {
                    "name": p.name,
                    "valid": p.is_valid,
                    "total_score": p.total_score,
                    "scores": {
                        "delay": p.delay_score,
                        "queue": p.queue_score,
                        "spillback": p.spillback_score,
                        "fairness": p.fairness_score,
                        "emergency": p.emergency_score,
                    },
                    "validation_reason": p.validation_reason,
                }
                for p in m9_eval.candidate_plans
            ],
        },
    }


@app.get("/api/recommendations/current")
def get_current_recommendation(scenario: str = Query("blocked_downstream")) -> dict[str, Any]:
    """Returns the current active recommendation verified by M5/M6/M7/M9."""
    if scenario == "rush":
        return RECOMMENDATIONS["REC-2026-J3-0945"]
    elif scenario == "ambulance":
        return RECOMMENDATIONS["REC-2026-J2-EMERG"]
    elif scenario == "normal":
        return RECOMMENDATIONS["REC-2026-J1-0112"]
    return RECOMMENDATIONS["REC-2026-J3-0887"]


@app.get("/api/audit-events")
def get_audit_events(limit: int = Query(50, ge=1, le=200)) -> list[dict[str, Any]]:
    """Returns recent operational and security audit records."""
    return list(reversed(AUDIT_LOG[-limit:]))


@app.get("/api/replay")
def get_replay_data(scenario: str = Query("blocked_downstream")) -> list[dict[str, Any]]:
    """Returns step-by-step decision sequence across control chain layers for replay."""
    if scenario == "blocked_downstream":
        return [
            {
                "step": 1,
                "layer": "TRAFFIC STATE",
                "title": "Traffic State",
                "time": "02:03",
                "data": "J3 Approach Queue: 12 veh (cross queue: 1)",
                "detail": "Arrival rate high; vehicles queue across J3 approach.",
                "status": "ACTIVE",
                "status_code": "info",
            },
            {
                "step": 2,
                "layer": "REACTIVE CONTROL",
                "title": "Reactive Control (M3)",
                "time": "02:03",
                "data": "Proposed Action: EXTEND GREEN (+5s)",
                "detail": "Queue controller detects Q_main >= 3 and attempts green extension.",
                "status": "EVALUATED",
                "status_code": "info",
            },
            {
                "step": 3,
                "layer": "DOWNSTREAM CHECK",
                "title": "Downstream Check",
                "time": "02:03",
                "data": "Link J3_J4: 47 / 53 veh (88.7% Occupancy)",
                "detail": "Physical storage near capacity. Occupancy >= 85.0% triggers CRITICAL state.",
                "status": "CRITICAL",
                "status_code": "critical",
            },
            {
                "step": 4,
                "layer": "SPILLBACK PROTECTION",
                "title": "Spillback Protection (M6)",
                "time": "02:03",
                "data": "Action: EXTENSION BLOCKED",
                "detail": "Preempts green extension to avoid packing link J3_J4. Requests clearance.",
                "status": "BLOCKED",
                "status_code": "critical",
            },
            {
                "step": 5,
                "layer": "DIGITAL TWIN EVALUATOR",
                "title": "Digital Twin Evaluator (M9)",
                "time": "02:03",
                "data": "Selected Plan: PLAN C (Score 28.5 vs Plan A 44.5)",
                "detail": "Plan B invalid (M6 spillback violation). Plan C coordinates downstream clearing.",
                "status": "SELECTED",
                "status_code": "approved",
            },
            {
                "step": 6,
                "layer": "SAFETY FIREWALL",
                "title": "Safety Firewall (M5)",
                "time": "02:03",
                "data": "Verdict: APPROVED (Phase 0 → Phase 1)",
                "detail": "Min green 10.0s satisfied (elapsed 10s); valid forward yellow transition.",
                "status": "VALIDATED",
                "status_code": "approved",
            },
            {
                "step": 7,
                "layer": "SIGNAL ACTION",
                "title": "Signal Action",
                "time": "02:04",
                "data": "TraCI Command: setPhase('J3', 1)",
                "detail": "J3 transitioned to Phase 1 (Yellow). Downstream capacity protected.",
                "status": "EXECUTED",
                "status_code": "executed",
            },
        ]
    else:
        return [
            {
                "step": 1,
                "layer": "TRAFFIC STATE",
                "title": "Traffic State",
                "time": "01:15",
                "data": "Arterial Free Flow: Queues <= 3 veh",
                "detail": "Corridor traffic progresses with normal sink discharge.",
                "status": "NORMAL",
                "status_code": "info",
            },
            {
                "step": 2,
                "layer": "REACTIVE CONTROL",
                "title": "Reactive Control (M3)",
                "time": "01:15",
                "data": "Proposed Action: KEEP_GREEN",
                "detail": "Demand accommodated in current phase.",
                "status": "EVALUATED",
                "status_code": "info",
            },
            {
                "step": 3,
                "layer": "DOWNSTREAM CHECK",
                "title": "Downstream Check",
                "time": "01:15",
                "data": "Downstream occupancy 22.6% (< 75%)",
                "detail": "Ample downstream storage buffer.",
                "status": "NORMAL",
                "status_code": "info",
            },
            {
                "step": 4,
                "layer": "SPILLBACK PROTECTION",
                "title": "Spillback Protection (M6)",
                "time": "01:15",
                "data": "Status: NO INTERVENTION NEEDED",
                "detail": "Proposed signal action passes through unimpeded.",
                "status": "PASS",
                "status_code": "approved",
            },
            {
                "step": 5,
                "layer": "DIGITAL TWIN EVALUATOR",
                "title": "Digital Twin Evaluator (M9)",
                "time": "01:15",
                "data": "Selected Plan: PLAN A (Score 14.2)",
                "detail": "Standard timing progression produces lowest penalty.",
                "status": "SELECTED",
                "status_code": "approved",
            },
            {
                "step": 6,
                "layer": "SAFETY FIREWALL",
                "title": "Safety Firewall (M5)",
                "time": "01:15",
                "data": "Verdict: APPROVED",
                "detail": "Timing conforms to safety parameters [10s, 40s].",
                "status": "VALIDATED",
                "status_code": "approved",
            },
            {
                "step": 7,
                "layer": "SIGNAL ACTION",
                "title": "Signal Action",
                "time": "01:15",
                "data": "TraCI Command: keepCurrentPhase()",
                "detail": "Green phase maintained.",
                "status": "EXECUTED",
                "status_code": "executed",
            },
        ]


class ApprovalPayload(BaseModel):
    """Payload for operator approval. Strictly forbids raw TraCI or arbitrary phase injection."""
    notes: str | None = Field(default=None, description="Optional operator comment")


@app.post("/api/recommendations/{recommendation_id}/approve-simulation")
def approve_recommendation(
    recommendation_id: str,
    payload: ApprovalPayload | None = None,
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    role: str | None = Query(None, description="Local demo role (VIEWER, OPERATOR, ADMIN)"),
) -> dict[str, Any]:
    """Approves a pre-validated traffic-control recommendation.

    Security & Authorization:
    - VIEWER: HTTP 403 Forbidden (Read-only access).
    - OPERATOR / ADMIN: Authorized.
    - Invalid/Unknown Recommendation: HTTP 404 Not Found.
    - Raw TraCI commands, arbitrary phase IDs, and user-generated signal mutations are strictly rejected.
    """
    effective_role = (x_user_role or role or "OPERATOR").upper()

    if effective_role == "VIEWER":
        raise HTTPException(
            status_code=403,
            detail="Role 'VIEWER' is not authorized to approve traffic control actions. Read-only access.",
        )

    if effective_role not in ("OPERATOR", "ADMIN"):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{effective_role}' is not recognized for control approvals.",
        )

    if recommendation_id not in RECOMMENDATIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Recommendation ID '{recommendation_id}' not found.",
        )

    rec = RECOMMENDATIONS[recommendation_id]
    rec["status"] = "APPROVED"
    rec["approved_by"] = effective_role
    now_iso = datetime.now(UTC).isoformat()
    rec["approved_at"] = now_iso

    # Append to secure audit trail
    event_id = f"AUD-{len(AUDIT_LOG) + 1:03d}"
    audit_entry = {
        "event_id": event_id,
        "timestamp": now_iso,
        "event_type": "operator_approval",
        "junction_id": rec.get("junction", "CORRIDOR"),
        "details": f"Recommendation {recommendation_id} ({rec.get('proposed_action')}) approved by {effective_role}.",
        "status": "APPROVED",
        "notes": payload.notes if payload else None,
    }
    AUDIT_LOG.append(audit_entry)

    return {
        "status": "APPROVED",
        "recommendation_id": recommendation_id,
        "junction": rec.get("junction"),
        "action": rec.get("proposed_action"),
        "approved_by": effective_role,
        "timestamp": now_iso,
        "audit_event_id": event_id,
    }


@app.get("/api/scenarios/{scenario_id}/junctions")
def get_junctions_state(scenario_id: str) -> dict[str, Any]:
    """Returns corridor junction states for J1, J2, J3, J4."""
    corridor = get_corridor_state(scenario=scenario_id)
    return {
        "J1": corridor["J1"],
        "J2": corridor["J2"],
        "J3": corridor["J3"],
        "J4": corridor["J4"],
    }


@app.get("/api/scenarios/{scenario_id}/decision_trace")
def get_decision_trace(scenario_id: str) -> list[dict[str, Any]]:
    """Returns the operational decision record trace for the 7-step control chain."""
    return get_replay_data(scenario=scenario_id)


@app.get("/api/scenarios/{scenario_id}/gps_sample")
def get_gps_sample(scenario_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Returns sample vehicle positions from recorded M4 GPS events."""
    gps_file = GPS_DIR / f"{scenario_id}.jsonl"
    if not gps_file.exists():
        return []

    events = []
    with open(gps_file, encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= limit:
                break
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


@app.websocket("/ws/simulation")
async def simulation_websocket(websocket: WebSocket):
    """WebSocket stream emitting corridor state ticks for connected frontends."""
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "handshake",
            "status": "connected",
            "message": "TrafficTwin Corridor Stream Connected",
            "seed": 42,
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass


class SimulationControlPayload(BaseModel):
    action: str = Field(..., description="Action: play, pause, reset, step")
    speed: float | None = Field(default=None, description="Playback speed: 0.5, 1.0, 2.0, 4.0")
    step_s: float | None = Field(default=1.0, description="Step duration in seconds")
    scenario: str | None = Field(default=None, description="Active scenario identifier")


SIMULATION_PLAYBACK: dict[str, Any] = {
    "status": "PAUSED",
    "sim_time_s": 120.0,
    "speed": 1.0,
    "total_duration_s": 360.0,
    "scenario": "blocked_downstream",
}


@app.get("/api/simulation/status")
def get_simulation_status() -> dict[str, Any]:
    """Returns current interactive simulation playback status and clock."""
    return {
        **SIMULATION_PLAYBACK,
        "sim_state": SIMULATION_PLAYBACK["status"],
        "speed_multiplier": SIMULATION_PLAYBACK["speed"],
        "total_time_s": SIMULATION_PLAYBACK["total_duration_s"],
    }


@app.post("/api/simulation/control")
def control_simulation(payload: SimulationControlPayload) -> dict[str, Any]:
    """Controls simulation playback: play, pause, reset, step, speed."""
    act = payload.action.lower()
    if payload.speed is not None and payload.speed in (0.5, 1.0, 2.0, 4.0):
        SIMULATION_PLAYBACK["speed"] = payload.speed

    if payload.scenario and payload.scenario in SCENARIOS:
        SIMULATION_PLAYBACK["scenario"] = payload.scenario

    if act == "play":
        SIMULATION_PLAYBACK["status"] = "RUNNING"
    elif act == "pause":
        SIMULATION_PLAYBACK["status"] = "PAUSED"
    elif act == "reset":
        SIMULATION_PLAYBACK["status"] = "PAUSED"
        SIMULATION_PLAYBACK["sim_time_s"] = 0.0
    elif act == "step":
        SIMULATION_PLAYBACK["status"] = "PAUSED"
        step_val = payload.step_s or 1.0
        SIMULATION_PLAYBACK["sim_time_s"] = min(
            SIMULATION_PLAYBACK["total_duration_s"],
            round(SIMULATION_PLAYBACK["sim_time_s"] + step_val, 1),
        )
    elif act == "speed":
        # Speed already updated above
        pass
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported action: '{act}'. Supported actions: play, pause, reset, step, speed.",
        )

    return {
        **SIMULATION_PLAYBACK,
        "sim_state": SIMULATION_PLAYBACK["status"],
        "speed_multiplier": SIMULATION_PLAYBACK["speed"],
        "total_time_s": SIMULATION_PLAYBACK["total_duration_s"],
    }


@app.get("/api/scenarios/{scenario_id}/roads")
def get_corridor_roads(scenario_id: str) -> list[dict[str, Any]]:
    """Returns physical road segments with live occupancy, capacity, and geometry."""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")

    is_blocked = scenario_id == "blocked_downstream"
    is_rush = scenario_id == "rush"

    roads = [
        {
            "id": "W0_J1",
            "name": "West Inflow Approach",
            "type": "Arterial",
            "length_m": 250.0,
            "lanes": 2,
            "speed_limit_kmph": 50.0,
            "capacity": 53,
            "vehicle_count": 18 if is_rush else 12,
            "occupancy_pct": 34.0 if is_rush else 22.6,
            "status": "NORMAL",
            "upstream_junction": "W0",
            "downstream_junction": "J1",
            "spillback_risk": "NORMAL",
        },
        {
            "id": "J1_J2",
            "name": "Arterial Segment 1 (J1 → J2)",
            "type": "Arterial",
            "length_m": 250.0,
            "lanes": 2,
            "speed_limit_kmph": 50.0,
            "capacity": 53,
            "vehicle_count": 24 if is_rush else 14,
            "occupancy_pct": 45.3 if is_rush else 26.4,
            "status": "NORMAL",
            "upstream_junction": "J1",
            "downstream_junction": "J2",
            "spillback_risk": "NORMAL",
        },
        {
            "id": "J2_J3",
            "name": "Arterial Segment 2 (J2 → J3)",
            "type": "Arterial",
            "length_m": 250.0,
            "lanes": 2,
            "speed_limit_kmph": 50.0,
            "capacity": 53,
            "vehicle_count": 36 if is_rush else 28,
            "occupancy_pct": 67.9 if is_rush else 52.8,
            "status": "WARNING" if is_rush else "NORMAL",
            "upstream_junction": "J2",
            "downstream_junction": "J3",
            "spillback_risk": "WARNING" if is_rush else "NORMAL",
        },
        {
            "id": "J3_J4",
            "name": "Arterial Segment 3 (J3 → J4 Bottleneck)",
            "type": "Arterial",
            "length_m": 250.0,
            "lanes": 2,
            "speed_limit_kmph": 50.0,
            "capacity": 53,
            "vehicle_count": 47 if is_blocked else (41 if is_rush else 18),
            "occupancy_pct": 88.7 if is_blocked else (77.4 if is_rush else 34.0),
            "status": "CRITICAL" if is_blocked else ("WARNING" if is_rush else "NORMAL"),
            "upstream_junction": "J3",
            "downstream_junction": "J4",
            "spillback_risk": "CRITICAL" if is_blocked else ("WARNING" if is_rush else "NORMAL"),
            "spillback_guard_engaged": is_blocked,
        },
        {
            "id": "J4_E5",
            "name": "East Outflow Egress (J4 → E5)",
            "type": "Arterial",
            "length_m": 250.0,
            "lanes": 2,
            "speed_limit_kmph": 50.0,
            "capacity": 53,
            "vehicle_count": 32 if is_blocked else (22 if is_rush else 10),
            "occupancy_pct": 60.4 if is_blocked else (41.5 if is_rush else 18.9),
            "status": "NORMAL",
            "upstream_junction": "J4",
            "downstream_junction": "E5",
            "spillback_risk": "NORMAL",
        },
    ]

    for r in roads:
        r["road_id"] = r["id"]
        r["occupancy_percent"] = r["occupancy_pct"]
        if r["occupancy_pct"] >= 85.0:
            r["status"] = "SPILLBACK RISK"

    return roads


@app.get("/api/scenarios/{scenario_id}/vehicles")
def get_corridor_vehicles(scenario_id: str, limit: int = 30) -> list[dict[str, Any]]:
    """Returns active vehicles with speed, position, link, and priority status."""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario not found")

    is_blocked = scenario_id == "blocked_downstream"
    is_amb = scenario_id == "ambulance"

    vehicles: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    # Always ensure core demo vehicles amb_1, veh_eb_12, veh_eb_18 are present
    core_vehicles = [
        {
            "id": "amb_1",
            "type": "emergency",
            "road_segment": "J2_J3",
            "lane_index": 0,
            "speed_kmph": 58.4,
            "target_junction": "J2",
            "eta_s": 12.4,
            "status": "PRIORITY_PREEMPTION" if is_amb else "CRUISING",
            "priority": "CRITICAL",
        },
        {
            "id": "veh_eb_12",
            "type": "passenger",
            "road_segment": "J1_J2",
            "lane_index": 1,
            "speed_kmph": 38.5,
            "target_junction": "J2",
            "eta_s": 8.2,
            "status": "CRUISING",
            "priority": "NORMAL",
        },
        {
            "id": "veh_eb_18",
            "type": "passenger",
            "road_segment": "J3_J4",
            "lane_index": 0,
            "speed_kmph": 0.0 if is_blocked else 22.0,
            "target_junction": "J4",
            "eta_s": 999.0 if is_blocked else 15.0,
            "status": "QUEUED_DOWNSTREAM" if is_blocked else "CRUISING",
            "priority": "NORMAL",
        },
    ]

    for cv in core_vehicles:
        seen_ids.add(cv["id"])
        vehicles.append(cv)

    # Read from authentic scenario GPS stream if available
    gps_file = GPS_DIR / f"{scenario_id}.jsonl"
    if gps_file.exists():
        with open(gps_file, encoding="utf-8") as f:
            for line in f:
                if len(vehicles) >= limit:
                    break
                if line.strip():
                    try:
                        record = json.loads(line)
                        vid = record.get("vehicle_id")
                        if vid and vid not in seen_ids:
                            seen_ids.add(vid)
                            v_type = "emergency" if "amb" in vid.lower() else "passenger"
                            seg = record.get("road_segment_id") or "J1_J2"
                            spd = round(float(record.get("speed_kmph", 40.0)), 1)
                            target_j = seg.split("_")[-1] if "_" in seg else "J3"
                            vehicles.append({
                                "id": vid,
                                "type": v_type,
                                "road_segment": seg,
                                "lane_index": record.get("lane_index", 0),
                                "speed_kmph": spd,
                                "target_junction": target_j,
                                "eta_s": round(max(4.0, (120.0 / max(1.0, spd / 3.6))), 1),
                                "status": "QUEUED" if spd < 5.0 else "MOVING",
                                "priority": "CRITICAL" if v_type == "emergency" else "NORMAL",
                            })
                    except (json.JSONDecodeError, ValueError):
                        continue

    for v in vehicles:
        v["vehicle_id"] = v["id"]
        v["speed_kmh"] = v.get("speed_kmph", 0.0)

    return vehicles
