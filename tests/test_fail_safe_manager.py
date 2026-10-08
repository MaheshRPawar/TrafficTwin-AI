"""TrafficTwin AI — Module M8 Fail-Safe Modes Acceptance Test Suite.

Verifies:
1. Operational mode definitions (PREDICTIVE, SAFE_ADAPTIVE, LOCAL_SAFE, SHADOW_RECOVERY).
2. Deterministic failure injection & mode transition rules.
3. Fallback plan retrieval from fallback_plan.json.
4. Transition validation & rejection of illegal phase/mode jumps.
5. Shadow recovery stability window verification.
6. Audit logging of all mode transitions.
"""


import pytest

from backend.app.reliability.fail_safe_manager import (
    FailSafeManager,
    FailSafeMode,
    load_fallback_plan,
)


# ---------------------------------------------------------------------------
# 1. State Machine Initialization & Fallback Plan Tests
# ---------------------------------------------------------------------------
def test_failsafe_manager_initialization():
    fsm = FailSafeManager()
    assert fsm.current_mode == FailSafeMode.PREDICTIVE
    assert len(fsm.transition_history) == 0
    assert fsm.shadow_start_time is None


def test_fallback_plan_loading():
    plan = load_fallback_plan()
    assert "phases" in plan
    assert plan["cycle_length_s"] == 60
    assert len(plan["phases"]) == 6
    # Verify fixed timing intervals
    phase_map = {p["index"]: p["duration_s"] for p in plan["phases"]}
    assert phase_map[0] == 30  # MAIN_GREEN
    assert phase_map[1] == 3   # MAIN_YELLOW
    assert phase_map[2] == 2   # ALL_RED_1
    assert phase_map[3] == 20  # CROSS_GREEN
    assert phase_map[4] == 3   # CROSS_YELLOW
    assert phase_map[5] == 2   # ALL_RED_2


def test_fallback_target_phase_calculation():
    fsm = FailSafeManager()
    # At t=0s -> Phase 0 (Main Green)
    assert fsm.get_fallback_target_phase(0.0) == 0
    assert fsm.get_fallback_target_phase(15.0) == 0
    # At t=31s -> Phase 1 (Main Yellow)
    assert fsm.get_fallback_target_phase(31.0) == 1
    # At t=34s -> Phase 2 (All Red 1)
    assert fsm.get_fallback_target_phase(34.0) == 2
    # At t=40s -> Phase 3 (Cross Green)
    assert fsm.get_fallback_target_phase(40.0) == 3
    # At t=56s -> Phase 4 (Cross Yellow)
    assert fsm.get_fallback_target_phase(56.0) == 4
    # At t=59s -> Phase 5 (All Red 2)
    assert fsm.get_fallback_target_phase(59.0) == 5
    # Cycle wrap around at t=60s -> Phase 0
    assert fsm.get_fallback_target_phase(60.0) == 0
    assert fsm.get_fallback_target_phase(65.0) == 0


# ---------------------------------------------------------------------------
# 2. Transition Validation & Illegal Transition Rejection
# ---------------------------------------------------------------------------
def test_valid_transitions():
    fsm = FailSafeManager()
    assert fsm.validate_transition(FailSafeMode.SAFE_ADAPTIVE) is True
    assert fsm.validate_transition(FailSafeMode.LOCAL_SAFE) is True


def test_illegal_transition_rejected():
    fsm = FailSafeManager(initial_mode=FailSafeMode.LOCAL_SAFE)
    # Direct jump from LOCAL_SAFE to PREDICTIVE without SHADOW_RECOVERY must be rejected
    assert fsm.validate_transition(FailSafeMode.PREDICTIVE) is False
    with pytest.raises(ValueError, match="Illegal state transition rejected"):
        fsm.execute_transition(FailSafeMode.PREDICTIVE, reason="invalid_direct_jump", sim_time=10.0)


# ---------------------------------------------------------------------------
# 3. Deterministic Failure Injection Tests
# ---------------------------------------------------------------------------
def test_planner_failure_triggers_safe_adaptive():
    fsm = FailSafeManager()
    res = fsm.evaluate_state(
        sim_time=10.0,
        telemetry_healthy=True,
        planner_healthy=False,  # Fault injected: planner down
        controller_healthy=True,
        trust_score=0.85,
        gps_age_s=1.0,
    )
    assert fsm.current_mode == FailSafeMode.SAFE_ADAPTIVE
    assert res["transition_event"] is not None
    assert res["transition_event"]["to_mode"] == "SAFE_ADAPTIVE"
    assert "planner_unavailable" in res["transition_event"]["reason"]


def test_stale_gps_telematics_triggers_safe_adaptive():
    fsm = FailSafeManager()
    res = fsm.evaluate_state(
        sim_time=12.0,
        telemetry_healthy=True,
        planner_healthy=True,
        controller_healthy=True,
        trust_score=0.85,
        gps_age_s=8.0,  # Fault: GPS stale (> 5s)
    )
    assert fsm.current_mode == FailSafeMode.SAFE_ADAPTIVE
    assert res["transition_event"] is not None
    assert res["transition_event"]["to_mode"] == "SAFE_ADAPTIVE"


def test_controller_failure_triggers_local_safe():
    fsm = FailSafeManager()
    res = fsm.evaluate_state(
        sim_time=20.0,
        telemetry_healthy=True,
        planner_healthy=True,
        controller_healthy=False,  # Fault: controller crash
        trust_score=0.85,
        gps_age_s=1.0,
    )
    assert fsm.current_mode == FailSafeMode.LOCAL_SAFE
    assert res["transition_event"]["to_mode"] == "LOCAL_SAFE"


def test_critical_trust_drop_triggers_local_safe():
    fsm = FailSafeManager()
    res = fsm.evaluate_state(
        sim_time=25.0,
        telemetry_healthy=True,
        planner_healthy=True,
        controller_healthy=True,
        trust_score=0.30,  # Critical trust drop (< 0.40)
        gps_age_s=1.0,
    )
    assert fsm.current_mode == FailSafeMode.LOCAL_SAFE
    assert res["transition_event"]["to_mode"] == "LOCAL_SAFE"


# ---------------------------------------------------------------------------
# 4. End-to-End Fault Recovery Cycle (Predictive -> Safe Adaptive -> Local Safe -> Shadow Recovery -> Predictive)
# ---------------------------------------------------------------------------
def test_full_fail_safe_lifecycle_and_stable_shadow_recovery(tmp_path):
    fsm = FailSafeManager()

    # 1. Healthy Predictive
    fsm.evaluate_state(sim_time=0.0, telemetry_healthy=True, planner_healthy=True, controller_healthy=True, trust_score=0.95)
    assert fsm.current_mode == FailSafeMode.PREDICTIVE

    # 2. Planner down -> SAFE_ADAPTIVE
    fsm.evaluate_state(sim_time=5.0, telemetry_healthy=True, planner_healthy=False, controller_healthy=True, trust_score=0.75)
    assert fsm.current_mode == FailSafeMode.SAFE_ADAPTIVE

    # 3. Controller failure -> LOCAL_SAFE
    fsm.evaluate_state(sim_time=10.0, telemetry_healthy=False, planner_healthy=False, controller_healthy=False, trust_score=0.20)
    assert fsm.current_mode == FailSafeMode.LOCAL_SAFE

    # 4. Services restored -> SHADOW_RECOVERY
    fsm.evaluate_state(sim_time=20.0, telemetry_healthy=True, planner_healthy=True, controller_healthy=True, trust_score=0.90)
    assert fsm.current_mode == FailSafeMode.SHADOW_RECOVERY
    assert fsm.shadow_start_time == 20.0

    # 5. During shadow window (at t=35s, elapsed 15s < 30s window) -> Still in SHADOW_RECOVERY
    fsm.evaluate_state(sim_time=35.0, telemetry_healthy=True, planner_healthy=True, controller_healthy=True, trust_score=0.92)
    assert fsm.current_mode == FailSafeMode.SHADOW_RECOVERY

    # 6. Stable window passed (at t=51s, elapsed 31s >= 30s window) -> Back to PREDICTIVE
    fsm.evaluate_state(sim_time=51.0, telemetry_healthy=True, planner_healthy=True, controller_healthy=True, trust_score=0.92)
    assert fsm.current_mode == FailSafeMode.PREDICTIVE

    # 7. Audit log verification
    audit_path = tmp_path / "mode_transitions.csv"
    fsm.log_transitions_to_csv(audit_path)
    assert audit_path.exists()
    content = audit_path.read_text(encoding="utf-8")
    assert "PREDICTIVE" in content
    assert "SAFE_ADAPTIVE" in content
    assert "LOCAL_SAFE" in content
    assert "SHADOW_RECOVERY" in content
    assert len(fsm.transition_history) == 4
