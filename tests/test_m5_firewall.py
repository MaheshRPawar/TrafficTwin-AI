"""TrafficTwin AI — Module M5 Acceptance Test Suite.

Signal Safety Firewall tests covering junction validation, phase limits,
clearance intervals, conflict protection, audit logging, and SUMO integration.
"""

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

from backend.app.guards.safety_firewall import (
    is_conflicting_phase,
    is_legal_transition,
    load_firewall_config,
    log_firewall_decision,
    validate_action,
)
from experiments.reactive_controller import decide_action

# ── 1. Junction Validation Tests ────────────────────────────────────────────

def test_valid_junction_accepted():
    """Firewall accepts any of the 4 defined junctions (J1-J4)."""
    for jid in ["J1", "J2", "J3", "J4"]:
        action = {
            "junction_id": jid,
            "current_phase": 0,
            "requested_phase": 0,
            "action": "KEEP_GREEN",
            "elapsed_green_s": 15.0,
        }
        res = validate_action(action)
        assert res["allowed"] is True
        assert res["junction_id"] == jid


def test_invalid_junction_rejected():
    """Firewall rejects unknown junction IDs with specific reason."""
    for bad_jid in ["J0", "J5", "J9", "unknown_junction", ""]:
        action = {
            "junction_id": bad_jid,
            "current_phase": 0,
            "requested_phase": 0,
            "action": "KEEP_GREEN",
            "elapsed_green_s": 15.0,
        }
        res = validate_action(action)
        assert res["allowed"] is False
        assert res["reason"] == "invalid_junction"


# ── 2. Phase Validation Tests ───────────────────────────────────────────────

def test_valid_phase_accepted():
    """Phases 0 through 5 are accepted as valid signal program phases."""
    for p in range(6):
        action = {
            "junction_id": "J1",
            "current_phase": p,
            "requested_phase": p,
            "action": "HOLD",
            "elapsed_green_s": 12.0,
        }
        res = validate_action(action)
        assert res["allowed"] is True


def test_invalid_phase_rejected():
    """Negative, out-of-range, or non-integer phases must be rejected."""
    for bad_phase in [-1, 6, 99, "phase_0"]:
        action = {
            "junction_id": "J1",
            "current_phase": bad_phase,
            "requested_phase": 0,
            "action": "HOLD",
        }
        res = validate_action(action)
        assert res["allowed"] is False
        assert res["reason"] == "invalid_phase"

    # Also test invalid requested_phase
    action_bad_req = {
        "junction_id": "J1",
        "current_phase": 0,
        "requested_phase": 7,
        "action": "START_TRANSITION",
        "elapsed_green_s": 15.0,
    }
    res_req = validate_action(action_bad_req)
    assert res_req["allowed"] is False
    assert res_req["reason"] == "invalid_phase"


# ── 3. Action Validation Tests ──────────────────────────────────────────────

def test_invalid_action_rejected():
    """Unknown actions outside the defined vocabulary must be rejected."""
    for bad_act in ["FORCE_GREEN", "OVERRIDE", "KILL_SIGNAL", "SKIP", ""]:
        action = {
            "junction_id": "J1",
            "current_phase": 0,
            "requested_phase": 0,
            "action": bad_act,
            "elapsed_green_s": 15.0,
        }
        res = validate_action(action)
        assert res["allowed"] is False
        assert res["reason"] == "invalid_action"


# ── 4. Minimum Green Tests ──────────────────────────────────────────────────

def test_transition_before_min_green_rejected():
    """Early transition request prior to min_green must be rejected."""
    action = {
        "junction_id": "J1",
        "current_phase": 0,
        "requested_phase": 1,
        "action": "START_TRANSITION",
        "elapsed_green_s": 6.0,
    }
    cfg = {"min_green_s": 10.0, "max_green_s": 45.0}
    res = validate_action(action, config=cfg)
    assert res["allowed"] is False
    assert res["reason"] == "minimum_green_not_reached"


def test_transition_after_min_green_accepted():
    """Transition request at or after min_green is accepted."""
    action = {
        "junction_id": "J1",
        "current_phase": 0,
        "requested_phase": 1,
        "action": "START_TRANSITION",
        "elapsed_green_s": 10.0,
    }
    cfg = {"min_green_s": 10.0, "max_green_s": 45.0}
    res = validate_action(action, config=cfg)
    assert res["allowed"] is True
    assert res["reason"] == "valid_transition"


# ── 5. Maximum Green Tests (40.0s Project Cap) ──────────────────────────────

def test_forty_second_max_green_cases():
    """Verify boundary enforcement for 40.0s maximum green:
    Case A: elapsed_green_s = 35, extension_s = 5 (35 + 5 = 40) -> ALLOWED
    Case B: elapsed_green_s = 36, extension_s = 5 (36 + 5 = 41) -> REJECTED
    Case C: elapsed_green_s = 40, extension_s = 1 (40 + 1 = 41) -> REJECTED
    """
    # Case A: 35 + 5 = 40 -> ALLOWED
    res_a = validate_action({
        "junction_id": "J1",
        "current_phase": 0,
        "requested_phase": 0,
        "action": "EXTEND_GREEN",
        "elapsed_green_s": 35.0,
        "extension_s": 5.0,
    })
    assert res_a["allowed"] is True
    assert res_a["reason"] == "valid_action"

    # Case B: 36 + 5 = 41 -> REJECTED
    res_b = validate_action({
        "junction_id": "J1",
        "current_phase": 0,
        "requested_phase": 0,
        "action": "EXTEND_GREEN",
        "elapsed_green_s": 36.0,
        "extension_s": 5.0,
    })
    assert res_b["allowed"] is False
    assert res_b["reason"] == "maximum_green_exceeded"

    # Case C: 40 + 1 = 41 -> REJECTED
    res_c = validate_action({
        "junction_id": "J1",
        "current_phase": 0,
        "requested_phase": 0,
        "action": "EXTEND_GREEN",
        "elapsed_green_s": 40.0,
        "extension_s": 1.0,
    })
    assert res_c["allowed"] is False
    assert res_c["reason"] == "maximum_green_exceeded"


def test_firewall_configuration_consistency():
    """Verify that firewall configuration matches project params.yaml."""
    cfg = load_firewall_config()
    assert cfg["min_green_s"] == 10.0
    assert cfg["max_green_s"] == 40.0
    assert cfg["yellow_s"] == 3.0
    assert cfg["all_red_s"] == 2.0


# ── 6. Yellow Clearance Tests ───────────────────────────────────────────────

def test_yellow_clearance_bypass_rejected():
    """Skipping the yellow phase (e.g. green directly to all-red) must be rejected."""
    # From MAIN_GREEN (0) directly to ALL_RED_1 (2), skipping MAIN_YELLOW (1)
    action_main = {
        "junction_id": "J2",
        "current_phase": 0,
        "requested_phase": 2,
        "action": "START_TRANSITION",
        "elapsed_green_s": 20.0,
    }
    res_main = validate_action(action_main)
    assert res_main["allowed"] is False
    assert res_main["reason"] == "yellow_clearance_required"

    # From CROSS_GREEN (3) directly to ALL_RED_2 (5), skipping CROSS_YELLOW (4)
    action_cross = {
        "junction_id": "J2",
        "current_phase": 3,
        "requested_phase": 5,
        "action": "START_TRANSITION",
        "elapsed_green_s": 20.0,
    }
    res_cross = validate_action(action_cross)
    assert res_cross["allowed"] is False
    assert res_cross["reason"] == "yellow_clearance_required"


# ── 7. All-Red Clearance Tests ──────────────────────────────────────────────

def test_all_red_clearance_bypass_rejected():
    """Skipping all-red interval (e.g. yellow directly to opposing green) must be rejected."""
    # From MAIN_YELLOW (1) directly to CROSS_GREEN (3), skipping ALL_RED_1 (2)
    action_main = {
        "junction_id": "J3",
        "current_phase": 1,
        "requested_phase": 3,
        "action": "START_TRANSITION",
        "elapsed_green_s": 0.0,
    }
    res_main = validate_action(action_main)
    assert res_main["allowed"] is False
    assert res_main["reason"] == "all_red_clearance_required"

    # From CROSS_YELLOW (4) directly to MAIN_GREEN (0), skipping ALL_RED_2 (5)
    action_cross = {
        "junction_id": "J3",
        "current_phase": 4,
        "requested_phase": 0,
        "action": "START_TRANSITION",
        "elapsed_green_s": 0.0,
    }
    res_cross = validate_action(action_cross)
    assert res_cross["allowed"] is False
    assert res_cross["reason"] == "all_red_clearance_required"


# ── 8. Conflict Protection Tests ────────────────────────────────────────────

def test_conflicting_phase_rejected():
    """Direct transition between conflicting greens (0 <-> 3) is rejected."""
    assert is_conflicting_phase(0, 3) is True
    assert is_conflicting_phase(3, 0) is True

    # Main Green -> Cross Green directly
    action_main = {
        "junction_id": "J1",
        "current_phase": 0,
        "requested_phase": 3,
        "action": "START_TRANSITION",
        "elapsed_green_s": 25.0,
    }
    res_main = validate_action(action_main)
    assert res_main["allowed"] is False
    assert res_main["reason"] == "conflicting_phase"

    # Cross Green -> Main Green directly
    action_cross = {
        "junction_id": "J1",
        "current_phase": 3,
        "requested_phase": 0,
        "action": "START_TRANSITION",
        "elapsed_green_s": 25.0,
    }
    res_cross = validate_action(action_cross)
    assert res_cross["allowed"] is False
    assert res_cross["reason"] == "conflicting_phase"


# ── 9. Legal Progression Tests ──────────────────────────────────────────────

def test_illegal_phase_jump_rejected():
    """Arbitrary non-consecutive phase transitions must be rejected."""
    # 0 -> 4 (jump to cross yellow)
    action_0_4 = {
        "junction_id": "J1",
        "current_phase": 0,
        "requested_phase": 4,
        "action": "START_TRANSITION",
        "elapsed_green_s": 20.0,
    }
    res_0_4 = validate_action(action_0_4)
    assert res_0_4["allowed"] is False
    assert res_0_4["reason"] == "illegal_phase_transition"

    # 2 -> 5 (jump between all-red phases)
    action_2_5 = {
        "junction_id": "J1",
        "current_phase": 2,
        "requested_phase": 5,
        "action": "START_TRANSITION",
    }
    res_2_5 = validate_action(action_2_5)
    assert res_2_5["allowed"] is False
    assert res_2_5["reason"] == "illegal_phase_transition"


def test_valid_legal_transition_accepted():
    """Every valid step in the 6-phase cycle is accepted when min_green is met."""
    cycle = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]
    for cur, req in cycle:
        assert is_legal_transition(cur, req) is True
        action = {
            "junction_id": "J1",
            "current_phase": cur,
            "requested_phase": req,
            "action": "START_TRANSITION",
            "elapsed_green_s": 20.0,
        }
        res = validate_action(action)
        assert res["allowed"] is True
        assert res["reason"] == "valid_transition"


def test_legal_transitions_and_direct_bypasses():
    """Confirm 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 0 is legal, and all direct bypasses fail:
    0 -> 3 (conflicting_phase)
    0 -> 2 (yellow_clearance_required)
    1 -> 3 (all_red_clearance_required)
    3 -> 5 (yellow_clearance_required)
    4 -> 0 (all_red_clearance_required)
    """
    # 0 -> 3 must fail
    res_0_3 = validate_action({
        "junction_id": "J1",
        "current_phase": 0,
        "requested_phase": 3,
        "action": "START_TRANSITION",
        "elapsed_green_s": 20.0,
    })
    assert res_0_3["allowed"] is False
    assert res_0_3["reason"] == "conflicting_phase"

    # 0 -> 2 must fail
    res_0_2 = validate_action({
        "junction_id": "J1",
        "current_phase": 0,
        "requested_phase": 2,
        "action": "START_TRANSITION",
        "elapsed_green_s": 20.0,
    })
    assert res_0_2["allowed"] is False
    assert res_0_2["reason"] == "yellow_clearance_required"

    # 1 -> 3 must fail
    res_1_3 = validate_action({
        "junction_id": "J1",
        "current_phase": 1,
        "requested_phase": 3,
        "action": "START_TRANSITION",
    })
    assert res_1_3["allowed"] is False
    assert res_1_3["reason"] == "all_red_clearance_required"

    # 3 -> 5 must fail
    res_3_5 = validate_action({
        "junction_id": "J1",
        "current_phase": 3,
        "requested_phase": 5,
        "action": "START_TRANSITION",
        "elapsed_green_s": 20.0,
    })
    assert res_3_5["allowed"] is False
    assert res_3_5["reason"] == "yellow_clearance_required"

    # 4 -> 0 must fail
    res_4_0 = validate_action({
        "junction_id": "J1",
        "current_phase": 4,
        "requested_phase": 0,
        "action": "START_TRANSITION",
    })
    assert res_4_0["allowed"] is False
    assert res_4_0["reason"] == "all_red_clearance_required"


# ── 10. Clearance Phase Restrictions ────────────────────────────────────────

def test_clearance_phase_cannot_receive_green_extension():
    """Yellow and all-red clearance intervals must not receive green extensions."""
    for c_phase in [1, 2, 4, 5]:
        action = {
            "junction_id": "J1",
            "current_phase": c_phase,
            "requested_phase": c_phase,
            "action": "EXTEND_GREEN",
            "elapsed_green_s": 1.0,
            "extension_s": 5.0,
        }
        res = validate_action(action)
        assert res["allowed"] is False
        assert res["reason"] == "action_not_valid_for_clearance_phase"


def test_clearance_phase_hold_accepted():
    """Holding state during active clearance interval is safe and accepted."""
    for c_phase in [1, 2, 4, 5]:
        action = {
            "junction_id": "J2",
            "current_phase": c_phase,
            "requested_phase": c_phase,
            "action": "HOLD",
            "elapsed_green_s": 0.0,
        }
        res = validate_action(action)
        assert res["allowed"] is True
        assert res["reason"] == "valid_action"


def test_clearance_hold_distinguished_from_extend_green():
    """HOLD preserves current clearance state; EXTEND_GREEN is strictly rejected."""
    for c_phase in [1, 2, 4, 5]:
        res_hold = validate_action({
            "junction_id": "J1",
            "current_phase": c_phase,
            "action": "HOLD",
        })
        assert res_hold["allowed"] is True
        assert res_hold["reason"] == "valid_action"

        res_ext = validate_action({
            "junction_id": "J1",
            "current_phase": c_phase,
            "action": "EXTEND_GREEN",
            "extension_s": 5.0,
        })
        assert res_ext["allowed"] is False
        assert res_ext["reason"] == "action_not_valid_for_clearance_phase"


# ── 11. Specificity and Audit Logging ───────────────────────────────────────

def test_rejection_reason_is_specific():
    """Firewall never returns generic 'error' or blank reason on failure."""
    test_cases = [
        ({"junction_id": "BAD"}, "invalid_junction"),
        ({"junction_id": "J1", "current_phase": 99}, "invalid_phase"),
        ({"junction_id": "J1", "current_phase": 0, "action": "BAD_ACT"}, "invalid_action"),
        ({"junction_id": "J1", "current_phase": 0, "action": "START_TRANSITION", "elapsed_green_s": 2.0}, "minimum_green_not_reached"),
        ({"junction_id": "J1", "current_phase": 0, "requested_phase": 3, "action": "START_TRANSITION", "elapsed_green_s": 20.0}, "conflicting_phase"),
    ]
    for act, expected_reason in test_cases:
        res = validate_action(act)
        assert res["allowed"] is False
        assert res["reason"] == expected_reason
        assert res["reason"] != "error"
        assert len(res["reason"]) > 0


def test_audit_decision_logging_and_fields(tmp_path):
    """Audit log writes decision records with all required columns."""
    log_file = tmp_path / "test_firewall_audit.csv"

    record = {
        "timestamp": 120.0,
        "junction_id": "J2",
        "current_phase": 0,
        "requested_phase": 3,
        "action": "START_TRANSITION",
        "allowed": False,
        "reason": "conflicting_phase",
    }
    log_firewall_decision(record, output_path=log_file)

    assert log_file.exists()
    with open(log_file, encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 1
    row = reader[0]
    assert float(row["timestamp"]) == 120.0
    assert row["junction_id"] == "J2"
    assert int(row["current_phase"]) == 0
    assert int(row["requested_phase"]) == 3
    assert row["action"] == "START_TRANSITION"
    assert row["allowed"] == "False"
    assert row["reason"] == "conflicting_phase"


# ── 12. Integration with M3 Controller ──────────────────────────────────────

def test_m3_controller_decision_validated_by_firewall():
    """Verify that decisions produced by M3 controller pass firewall validation."""
    # M3 decides KEEP_GREEN while under min_green
    m3_act, m3_reason = decide_action(
        current_phase=0,
        green_duration=5.0,
        queue_main=0,
        queue_cross=10,
        min_green=10.0,
        max_green=40.0,
    )
    assert m3_act == "KEEP_GREEN"

    firewall_action = {
        "junction_id": "J1",
        "current_phase": 0,
        "requested_phase": 0,
        "action": m3_act,
        "elapsed_green_s": 5.0,
    }
    fw_res = validate_action(firewall_action)
    assert fw_res["allowed"] is True

    # M3 decides START_TRANSITION after max_green
    m3_act2, m3_reason2 = decide_action(
        current_phase=0,
        green_duration=40.0,
        queue_main=5,
        queue_cross=0,
        min_green=10.0,
        max_green=40.0,
    )
    assert m3_act2 == "START_TRANSITION"

    firewall_action2 = {
        "junction_id": "J1",
        "current_phase": 0,
        "requested_phase": 1,  # Yellow clearance phase
        "action": m3_act2,
        "elapsed_green_s": 40.0,
    }
    fw_res2 = validate_action(firewall_action2)
    assert fw_res2["allowed"] is True
    assert fw_res2["reason"] == "valid_transition"


def test_m3_runtime_firewall_blocks_unsafe_action_before_traci():
    """Verify that M3 step_junction routes through M5 and blocks unsafe TraCI actuation."""
    from experiments.reactive_controller import step_junction

    class MockTraCI:
        def __init__(self):
            self.phase_set = None
            self.duration_set = None

            class MockTL:
                def __init__(self, outer):
                    self.outer = outer

                def getPhase(self, jid):
                    return 0  # MAIN_GREEN

                def setPhase(self, jid, phase):
                    self.outer.phase_set = phase

                def setPhaseDuration(self, jid, dur):
                    self.outer.duration_set = dur

            class MockLane:
                def getLastStepHaltingNumber(self, lane):
                    return 10  # high queue on all lanes

            self.trafficlight = MockTL(self)
            self.lane = MockLane()

    mock_traci = MockTraCI()
    state = {"last_phase": 0, "phase_start": 0.0, "allocated_green": 10.0}
    cfg = {
        "min_green_s": 10.0,
        "max_green_s": 40.0,
        "extension_step_s": 5.0,
        "queue_threshold": 3,
    }

    # At sim_time=5.0 (< min_green), controller keeps green, TraCI setPhase not called
    rec = step_junction(mock_traci, "J1", 5.0, state, cfg)
    assert rec["action"] == "KEEP_GREEN"
    assert mock_traci.phase_set is None

    # At sim_time=40.0 (max_green), controller transitions to yellow (phase 1)
    rec2 = step_junction(mock_traci, "J1", 40.0, state, cfg)
    assert rec2["action"] == "START_TRANSITION"
    assert mock_traci.phase_set == 1  # Allowed yellow phase reached TraCI

    # Simulate an upstream controller attempting an unsafe green extension beyond firewall cap
    mock_traci_bad = MockTraCI()
    bad_cfg = {
        "min_green_s": 10.0,
        "max_green_s": 50.0,  # Misconfigured upstream controller allowing up to 50s
        "extension_step_s": 5.0,
        "queue_threshold": 3,
    }
    state_bad = {"last_phase": 0, "phase_start": 0.0, "allocated_green": 42.0}
    rec_bad = step_junction(mock_traci_bad, "J1", 42.0, state_bad, bad_cfg)
    assert rec_bad["action"] == "HOLD"
    assert "firewall_blocked: maximum_green_exceeded" in rec_bad["reason"]
    assert state_bad["allocated_green"] == 42.0  # Extension was blocked by firewall


# ── 13. SUMO Real Corridor Signal Integration ───────────────────────────────

def test_sumo_corridor_signal_program_integration():
    """Verify that firewall phase structure matches the real SUMO corridor network."""
    tll_path = Path("sumo/net/corridor.tll.xml")
    assert tll_path.exists(), "Corridor signal definition file missing"

    tree = ET.parse(tll_path)
    root = tree.getroot()

    tl_logics = root.findall("tlLogic")
    assert len(tl_logics) == 4, "Expected 4 signal-controlled junctions"

    junction_ids = [tl.get("id") for tl in tl_logics]
    assert sorted(junction_ids) == ["J1", "J2", "J3", "J4"]

    for tl in tl_logics:
        phases = tl.findall("phase")
        assert len(phases) == 6, f"Junction {tl.get('id')} must have 6 phases"

        # Check phase names and durations match expected cycle
        assert phases[0].get("name") == "MAIN_GREEN"
        assert int(phases[0].get("duration")) == 30
        assert phases[1].get("name") == "MAIN_YELLOW"
        assert int(phases[1].get("duration")) == 3
        assert phases[2].get("name") == "ALL_RED_1"
        assert int(phases[2].get("duration")) == 2
        assert phases[3].get("name") == "CROSS_GREEN"
        assert int(phases[3].get("duration")) == 20
        assert phases[4].get("name") == "CROSS_YELLOW"
        assert int(phases[4].get("duration")) == 3
        assert phases[5].get("name") == "ALL_RED_2"
        assert int(phases[5].get("duration")) == 2

    # Verify firewall accepts legal progression for real corridor
    for jid in junction_ids:
        res_legal = validate_action({
            "junction_id": jid,
            "current_phase": 0,
            "requested_phase": 1,
            "action": "START_TRANSITION",
            "elapsed_green_s": 30.0,
        })
        assert res_legal["allowed"] is True

        # Verify firewall rejects unsafe direct jump to conflicting cross green
        res_illegal = validate_action({
            "junction_id": jid,
            "current_phase": 0,
            "requested_phase": 3,
            "action": "START_TRANSITION",
            "elapsed_green_s": 30.0,
        })
        assert res_illegal["allowed"] is False
        assert res_illegal["reason"] == "conflicting_phase"
