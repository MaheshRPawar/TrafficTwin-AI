"""TrafficTwin AI — Module M11 Integration Flows Test Suite.

Verifies the 7 end-to-end operational and fail-safe flows of the TrafficTwin AI decision-support platform:
- FLOW 1: Normal Arterial Progression (SUMO -> M3 -> M7 -> M6 -> M9 -> M5 -> TraCI)
- FLOW 2: Blocked Downstream Link (M3 extension proposal -> M6 spillback block -> M5 validation -> phase transition)
- FLOW 3: Staged Ambulance Priority & Post-Preemption Fairness Recovery (M7 -> M6 -> M5)
- FLOW 4: Planner Failure -> Safe Adaptive Fallback Graceful Degradation
- FLOW 5: Controller Failure -> Local Safe Fallback Mode
- FLOW 6: Shadow Recovery -> Autonomous Return to Predictive Mode
- FLOW 7: Role-Based Operator Approval Security & Injection Rejection
"""

from fastapi.testclient import TestClient

from backend.app.guards.safety_firewall import validate_action
from backend.app.main import app
from backend.app.planner.evaluator import DigitalTwinPlanner
from backend.app.planner.models import CorridorSnapshot, JunctionSnapshot
from backend.app.reliability.fail_safe_manager import (
    FailSafeManager,
    FailSafeMode,
)
from experiments.emergency_controller import (
    AmbulancePreemptionManager,
    FairnessTracker,
    PostEmergencyRecoveryManager,
)
from experiments.reactive_controller import decide_action
from experiments.spillback_controller import (
    apply_spillback_guard,
    calculate_spillback_risk,
)


# ==============================================================================
# FLOW 1: NORMAL TRAFFIC PROGRESSION
# ==============================================================================
def test_flow_1_normal_traffic():
    """FLOW 1: Normal traffic progression along corridor without blockage."""
    # 1. Traffic State
    q_main = 2
    q_cross = 1
    curr_phase = 0
    elapsed_green = 14.0
    downstream_occ = 0.28
    downstream_vehs = 15
    downstream_cap = 53

    # 2. M3 Reactive Proposal
    m3_act, reason = decide_action(
        current_phase=curr_phase,
        green_duration=elapsed_green,
        queue_main=q_main,
        queue_cross=q_cross,
        min_green=10.0,
        max_green=40.0,
    )
    assert m3_act == "KEEP_GREEN"

    # 3. M7 Fairness & Emergency check
    tracker = FairnessTracker(junction_ids=["J1", "J2", "J3", "J4"])
    debt = tracker.state["J1"]["cross"]["fairness_debt"]
    assert debt == 0.0

    amb_mgr = AmbulancePreemptionManager()
    status, amb_act, amb_rsn = amb_mgr.evaluate_priority_request(
        junction_id="J1",
        amb_info=None,
        downstream_state={"risk": "NORMAL", "occupancy": downstream_occ},
        current_phase=curr_phase,
        green_duration=elapsed_green,
    )
    assert status == "INACTIVE"

    # 4. M6 Spillback Guard
    m6_risk = calculate_spillback_risk(downstream_occ)
    assert m6_risk == "NORMAL"
    downstream_state = {
        "edge_id": "J1_J2",
        "occupancy": downstream_occ,
        "vehicle_count": downstream_vehs,
        "capacity": downstream_cap,
        "risk": m6_risk,
    }
    m6_act, m6_reason, sig_act = apply_spillback_guard(
        proposed_action=m3_act,
        proposed_reason=reason,
        downstream_state=downstream_state,
        current_phase=curr_phase,
        green_duration=elapsed_green,
        min_green=10.0,
    )
    assert m6_act == "KEEP_GREEN"

    # 5. M9 Plan Evaluator
    snapshot = CorridorSnapshot(
        timestamp=60.0,
        scenario="normal",
        controller_mode="PREDICTIVE",
        junctions={
            "J1": JunctionSnapshot(
                junction_id="J1",
                current_phase=curr_phase,
                elapsed_green_s=elapsed_green,
                queue_main=q_main,
                queue_cross=q_cross,
                downstream_edge="J1_J2",
                downstream_occupancy=downstream_occ,
                spillback_risk="NORMAL",
                cross_fairness_debt=0.0,
                starvation_risk=False,
                emergency_status="INACTIVE",
            ),
            "J2": JunctionSnapshot("J2", 0, 15.0, 3, 0, "J2_J3", 0.25, "NORMAL", 0.0, False, "INACTIVE"),
            "J3": JunctionSnapshot("J3", 0, 15.0, 2, 0, "J3_J4", 0.20, "NORMAL", 0.0, False, "INACTIVE"),
            "J4": JunctionSnapshot("J4", 0, 15.0, 2, 0, "J4_E5", 0.15, "NORMAL", 0.0, False, "INACTIVE"),
        },
    )
    planner = DigitalTwinPlanner()
    m9_eval = planner.evaluate(snapshot)
    assert m9_eval.selected_plan_id in ("PLAN_A", "PLAN_B")

    # 6. M5 Safety Firewall
    fw_req = {
        "junction_id": "J1",
        "current_phase": curr_phase,
        "requested_phase": curr_phase,
        "action": "KEEP_GREEN",
        "elapsed_green_s": elapsed_green,
        "extension_s": 0.0,
    }
    fw_res = validate_action(fw_req)
    assert fw_res["allowed"] is True
    assert fw_res["reason"] == "valid_action"


# ==============================================================================
# FLOW 2: BLOCKED DOWNSTREAM (M6 SPILLBACK GUARD OVERRIDE)
# ==============================================================================
def test_flow_2_blocked_downstream_spillback():
    """FLOW 2: Heavy arrival at J3 with blocked downstream link J3_J4."""
    # 1. Heavy queue arriving at J3
    q_main = 12
    q_cross = 1
    curr_phase = 0
    elapsed_green = 10.0
    downstream_vehs = 47
    downstream_cap = 53  # Occupancy = 47/53 = 88.68% >= 85.0% CRITICAL
    downstream_occ = downstream_vehs / downstream_cap

    # 2. M3 proposes extension due to large queue
    m3_act, reason = decide_action(
        current_phase=curr_phase,
        green_duration=elapsed_green,
        queue_main=q_main,
        queue_cross=q_cross,
        min_green=10.0,
        max_green=40.0,
    )
    assert m3_act == "EXTEND_GREEN"

    # 3. M6 Spillback Guard detects critical downstream occupancy and BLOCKS extension
    m6_risk = calculate_spillback_risk(downstream_occ)
    assert m6_risk == "CRITICAL"
    downstream_state = {
        "edge_id": "J3_J4",
        "occupancy": downstream_occ,
        "vehicle_count": downstream_vehs,
        "capacity": downstream_cap,
        "risk": m6_risk,
    }
    m6_act, m6_reason, sig_act = apply_spillback_guard(
        proposed_action=m3_act,
        proposed_reason=reason,
        downstream_state=downstream_state,
        current_phase=curr_phase,
        green_duration=elapsed_green,
        min_green=10.0,
    )
    assert m6_act == "SPILLBACK_BLOCK"
    assert sig_act == "START_TRANSITION"
    assert "critical" in m6_reason.lower()

    # 4. M9 Plan Evaluator rejects Plan B due to spillback risk and evaluates Plan C
    snapshot = CorridorSnapshot(
        timestamp=120.0,
        scenario="blocked_downstream",
        controller_mode="PREDICTIVE",
        junctions={
            "J1": JunctionSnapshot("J1", 0, 15.0, 3, 0, "J1_J2", 0.25, "NORMAL", 0.0, False, "INACTIVE"),
            "J2": JunctionSnapshot("J2", 0, 15.0, 4, 1, "J2_J3", 0.40, "NORMAL", 0.0, False, "INACTIVE"),
            "J3": JunctionSnapshot(
                junction_id="J3",
                current_phase=curr_phase,
                elapsed_green_s=elapsed_green,
                queue_main=q_main,
                queue_cross=q_cross,
                downstream_edge="J3_J4",
                downstream_occupancy=downstream_occ,
                spillback_risk="CRITICAL",
                cross_fairness_debt=0.0,
                starvation_risk=False,
                emergency_status="INACTIVE",
            ),
            "J4": JunctionSnapshot("J4", 1, 3.0, 8, 2, "J4_E5", 0.88, "CRITICAL", 0.0, False, "INACTIVE"),
        },
    )
    planner = DigitalTwinPlanner()
    plan_b = planner.generate_plan_b(snapshot)
    assert plan_b.is_valid is False
    assert "m6_spillback_violation" in plan_b.validation_reason

    # 5. M5 Safety Firewall validates safe transition to Phase 1 (Yellow)
    fw_req = {
        "junction_id": "J3",
        "current_phase": 0,
        "requested_phase": 1,
        "action": "START_TRANSITION",
        "elapsed_green_s": elapsed_green,
        "extension_s": 0.0,
    }
    fw_res = validate_action(fw_req)
    assert fw_res["allowed"] is True
    assert fw_res["requested_phase"] == 1


# ==============================================================================
# FLOW 3: AMBULANCE STAGED PRIORITY & FAIRNESS RECOVERY
# ==============================================================================
def test_flow_3_ambulance_staged_priority_and_recovery():
    """FLOW 3: Emergency vehicle arrival, staged preemption, and post-preemption recovery."""
    amb_mgr = AmbulancePreemptionManager()
    rec_mgr = PostEmergencyRecoveryManager()

    # Ambulance approaches J2 with safe downstream
    amb_info = {
        "vehicle_id": "amb_01",
        "edge": "J1_J2",
        "target_junction": "J2",
        "eta_s": 8.5,
    }
    downstream_safe = {"risk": "NORMAL", "occupancy": 0.25}

    # Step J2 under ambulance priority
    status, action, reason = amb_mgr.evaluate_priority_request(
        junction_id="J2",
        amb_info=amb_info,
        downstream_state=downstream_safe,
        current_phase=0,
        green_duration=12.0,
    )
    assert status == "PRIORITY_STAGED"
    assert action == "KEEP_GREEN"
    assert "DOWNSTREAM_CAPACITY_SUFFICIENT" in reason

    # M5 validates holding priority green
    fw_req = {
        "junction_id": "J2",
        "current_phase": 0,
        "requested_phase": 0,
        "action": "KEEP_GREEN",
        "elapsed_green_s": 12.0,
        "extension_s": 0.0,
    }
    assert validate_action(fw_req)["allowed"] is True

    # Ambulance clears corridor -> triggers recovery
    rec_mgr.trigger_recovery("J2", sim_time=60.0, cross_debt=20.0)
    assert rec_mgr.recovery_state["J2"]["active"] is True


# ==============================================================================
# FLOW 4: PLANNER FAILURE -> SAFE ADAPTIVE FALLBACK
# ==============================================================================
def test_flow_4_planner_failure_safe_adaptive():
    """FLOW 4: When M9 planner encounters unexpected corrupt data, gracefully fallback to SAFE_ADAPTIVE."""
    fsm = FailSafeManager()
    assert fsm.current_mode == FailSafeMode.PREDICTIVE

    # Planner throws exception or emits invalid state
    res = fsm.evaluate_state(
        sim_time=10.0,
        telemetry_healthy=True,
        planner_healthy=False,  # Planner failure
        controller_healthy=True,
        trust_score=0.85,
        gps_age_s=1.0,
    )
    assert fsm.current_mode == FailSafeMode.SAFE_ADAPTIVE
    assert res["transition_event"]["to_mode"] == "SAFE_ADAPTIVE"


# ==============================================================================
# FLOW 5: CONTROLLER FAILURE -> LOCAL SAFE FALLBACK
# ==============================================================================
def test_flow_5_controller_failure_local_safe():
    """FLOW 5: When controller fails, system falls back to LOCAL_SAFE."""
    fsm = FailSafeManager()
    res = fsm.evaluate_state(
        sim_time=20.0,
        telemetry_healthy=True,
        planner_healthy=True,
        controller_healthy=False,  # Controller failure
        trust_score=0.85,
        gps_age_s=1.0,
    )
    assert fsm.current_mode == FailSafeMode.LOCAL_SAFE
    assert res["transition_event"]["to_mode"] == "LOCAL_SAFE"

    # In LOCAL_SAFE, timing reverts to pre-computed conservative cycle
    target_phase = fsm.get_fallback_target_phase(31.0)
    assert target_phase == 1  # Yellow


# ==============================================================================
# FLOW 6: RECOVERY -> SHADOW RECOVERY -> PREDICTIVE
# ==============================================================================
def test_flow_6_shadow_recovery_to_predictive():
    """FLOW 6: Reconnected/recovered health promotes system through SHADOW_RECOVERY back to PREDICTIVE."""
    fsm = FailSafeManager(initial_mode=FailSafeMode.LOCAL_SAFE)
    assert fsm.current_mode == FailSafeMode.LOCAL_SAFE

    # System begins recovery -> enters SHADOW_RECOVERY
    res = fsm.evaluate_state(
        sim_time=100.0,
        telemetry_healthy=True,
        planner_healthy=True,
        controller_healthy=True,
        trust_score=0.90,
        gps_age_s=1.0,
    )
    assert res["current_mode"] == FailSafeMode.SHADOW_RECOVERY.value
    assert fsm.current_mode == FailSafeMode.SHADOW_RECOVERY
    assert fsm.shadow_start_time == 100.0

    # Stable window passed (at t=131s, elapsed 31s >= 30s window) -> Back to PREDICTIVE
    res_stable = fsm.evaluate_state(
        sim_time=131.0,
        telemetry_healthy=True,
        planner_healthy=True,
        controller_healthy=True,
        trust_score=0.92,
        gps_age_s=1.0,
    )
    assert fsm.current_mode == FailSafeMode.PREDICTIVE
    assert res_stable["transition_event"]["to_mode"] == "PREDICTIVE"


# ==============================================================================
# FLOW 7: OPERATOR APPROVAL SECURITY & INJECTION PREVENTION
# ==============================================================================
def test_flow_7_operator_approval_security_and_injection():
    """FLOW 7: Viewer 403, Operator 200, Admin 200, Invalid 404, arbitrary TraCI injection rejected."""
    client = TestClient(app)

    # 1. Viewer role is strictly read-only (403)
    res_viewer = client.post(
        "/api/recommendations/REC-2026-J3-0887/approve-simulation",
        headers={"X-User-Role": "VIEWER"},
    )
    assert res_viewer.status_code == 403

    # 2. Operator role successfully approves valid recommendation (200)
    res_op = client.post(
        "/api/recommendations/REC-2026-J3-0887/approve-simulation",
        headers={"X-User-Role": "OPERATOR"},
        json={"notes": "Approved during shift handoff"},
    )
    assert res_op.status_code == 200
    assert res_op.json()["status"] == "APPROVED"

    # 3. Admin role successfully approves recommendation (200)
    res_admin = client.post(
        "/api/recommendations/REC-2026-J3-0945/approve-simulation",
        headers={"X-User-Role": "ADMIN"},
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["status"] == "APPROVED"

    # 4. Unknown recommendation ID returns 404
    res_404 = client.post(
        "/api/recommendations/REC-UNKNOWN-INVALID/approve-simulation",
        headers={"X-User-Role": "OPERATOR"},
    )
    assert res_404.status_code == 404

    # 5. Raw TraCI injection attempt: Passing raw params is ignored and cannot alter approved action
    malicious_payload = {
        "traci_command": "traci.trafficlight.setPhase('J3', 99)",
        "arbitrary_phase": 99,
        "signal_id": "HACKED",
    }
    res_inject = client.post(
        "/api/recommendations/REC-2026-J1-0112/approve-simulation",
        headers={"X-User-Role": "OPERATOR"},
        json=malicious_payload,
    )
    assert res_inject.status_code == 200
    # The action applied is only the pre-validated KEEP_GREEN action, not arbitrary phase 99
    assert res_inject.json()["action"] == "KEEP_GREEN"
