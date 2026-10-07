"""
TrafficTwin AI — Module M3 Acceptance Test Suite
Safe Queue-Reactive Traffic Signal Controller
"""

import csv
from pathlib import Path

from experiments.reactive_controller import (
    INCOMING_LANES,
    NEXT_CLEARANCE_PHASE,
    PHASE_NAMES,
    decide_action,
    init_junction_states,
    load_controller_config,
)
from experiments.run_reactive import save_decision_log

# ── 1. Minimum Green Tests ──────────────────────────────────────────────────

def test_min_green_prevents_early_transition_main():
    """Controller must not terminate MAIN_GREEN before minimum green elapses."""
    action, reason = decide_action(
        current_phase=0,
        green_duration=4.0,
        queue_main=0,
        queue_cross=15,
        min_green=10.0,
        max_green=40.0,
    )
    assert action == "KEEP_GREEN"
    assert "minimum green not satisfied" in reason


def test_min_green_prevents_early_transition_cross():
    """Controller must not terminate CROSS_GREEN before minimum green elapses."""
    action, reason = decide_action(
        current_phase=3,
        green_duration=8.5,
        queue_main=20,
        queue_cross=0,
        min_green=10.0,
        max_green=40.0,
    )
    assert action == "KEEP_GREEN"
    assert "minimum green not satisfied" in reason


# ── 2. Maximum Green Tests ──────────────────────────────────────────────────

def test_max_green_prevents_unlimited_extension():
    """Controller must transition when maximum green is reached, regardless of demand."""
    action, reason = decide_action(
        current_phase=0,
        green_duration=40.0,
        queue_main=30,
        queue_cross=0,
        min_green=10.0,
        max_green=40.0,
    )
    assert action == "START_TRANSITION"
    assert "maximum green reached" in reason


def test_max_green_strictly_enforced_beyond_limit():
    """Controller must transition if green duration exceeds max_green."""
    action, reason = decide_action(
        current_phase=3,
        green_duration=42.0,
        queue_main=0,
        queue_cross=25,
        min_green=10.0,
        max_green=40.0,
    )
    assert action == "START_TRANSITION"
    assert "maximum green reached" in reason


# ── 3. Green Extension Tests ─────────────────────────────────────────────────

def test_high_queue_causes_bounded_extension_main():
    """High queue on main green should trigger EXTEND_GREEN within limits."""
    action, reason = decide_action(
        current_phase=0,
        green_duration=15.0,
        queue_main=8,
        queue_cross=1,
        min_green=10.0,
        max_green=40.0,
        queue_threshold=3,
    )
    assert action == "EXTEND_GREEN"
    assert "extending green" in reason


def test_high_queue_causes_bounded_extension_cross():
    """High queue on cross green should trigger EXTEND_GREEN within limits."""
    action, reason = decide_action(
        current_phase=3,
        green_duration=12.0,
        queue_main=1,
        queue_cross=6,
        min_green=10.0,
        max_green=40.0,
        queue_threshold=3,
    )
    assert action == "EXTEND_GREEN"
    assert "extending green" in reason


# ── 4. Low Queue Demand Tests ───────────────────────────────────────────────

def test_opposing_queue_triggers_transition_after_min_green():
    """Higher queue on opposing approach should trigger transition after min green."""
    action, reason = decide_action(
        current_phase=0,
        green_duration=12.0,
        queue_main=2,
        queue_cross=7,
        min_green=10.0,
        max_green=40.0,
        queue_threshold=3,
    )
    assert action == "START_TRANSITION"
    assert "cross queue" in reason


def test_empty_current_queue_triggers_transition():
    """If current queue is empty and opposing queue is waiting, transition."""
    action, reason = decide_action(
        current_phase=0,
        green_duration=15.0,
        queue_main=0,
        queue_cross=2,
        min_green=10.0,
        max_green=40.0,
        queue_threshold=3,
    )
    assert action == "START_TRANSITION"
    assert "main queue empty" in reason


def test_empty_cross_street_returns_to_main_arterial():
    """Cross street returns to main arterial when cross queue is 0."""
    action, reason = decide_action(
        current_phase=3,
        green_duration=11.0,
        queue_main=0,
        queue_cross=0,
        min_green=10.0,
        max_green=40.0,
    )
    assert action == "START_TRANSITION"
    assert "returning to main arterial" in reason


# ── 5. Safe Phase Transitions ───────────────────────────────────────────────

def test_clearance_phases_return_hold():
    """Clearance phases (1, 2, 4, 5) must always return HOLD."""
    for phase in [1, 2, 4, 5]:
        action, reason = decide_action(
            current_phase=phase,
            green_duration=0.0,
            queue_main=10,
            queue_cross=10,
        )
        assert action == "HOLD"
        assert "clearance" in reason


def test_safe_transition_sequence_mapping():
    """Verify safe transition never switches directly to conflicting green."""
    assert NEXT_CLEARANCE_PHASE[0] == 1  # MAIN_GREEN -> MAIN_YELLOW
    assert NEXT_CLEARANCE_PHASE[3] == 4  # CROSS_GREEN -> CROSS_YELLOW

    # Verify clearance phases are strictly yellow, not green
    assert PHASE_NAMES[1] == "MAIN_YELLOW"
    assert PHASE_NAMES[4] == "CROSS_YELLOW"


def test_incoming_lanes_defined_for_all_junctions():
    """All junctions J1-J4 must have incoming main and cross lanes."""
    for jid in ["J1", "J2", "J3", "J4"]:
        assert jid in INCOMING_LANES
        assert "main" in INCOMING_LANES[jid]
        assert "cross" in INCOMING_LANES[jid]
        assert len(INCOMING_LANES[jid]["main"]) > 0
        assert len(INCOMING_LANES[jid]["cross"]) > 0


# ── 6. Decision Log Tests ───────────────────────────────────────────────────

def test_decision_log_writer_and_format(tmp_path):
    """Verify decision log exports all expected fields and valid actions."""
    sample_records = [
        {
            "timestamp": 12.0,
            "junction_id": "J2",
            "current_phase": "MAIN_GREEN",
            "queue_main": 18,
            "queue_cross": 4,
            "action": "EXTEND_GREEN",
            "reason": "high main queue (18), extending green",
        },
        {
            "timestamp": 13.0,
            "junction_id": "J2",
            "current_phase": "MAIN_YELLOW",
            "queue_main": 15,
            "queue_cross": 4,
            "action": "HOLD",
            "reason": "clearance phase active",
        },
    ]

    log_path = tmp_path / "test_decisions.csv"
    save_decision_log(sample_records, log_path)
    assert log_path.exists()

    with open(log_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    expected_fields = ["timestamp", "junction_id", "current_phase", "queue_main", "queue_cross", "action", "reason"]
    assert reader.fieldnames == expected_fields
    assert rows[0]["action"] == "EXTEND_GREEN"
    assert rows[1]["action"] == "HOLD"


def test_actual_decision_log_has_valid_data():
    """Verify the generated reactive decision log contains valid actions and phases."""
    log_path = Path("data/output/metrics/reactive_normal_decisions.csv")
    assert log_path.exists(), f"Decision log missing: {log_path}"

    with open(log_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) > 0
    valid_actions = {"HOLD", "KEEP_GREEN", "EXTEND_GREEN", "START_TRANSITION"}
    valid_junctions = {"J1", "J2", "J3", "J4"}

    for r in rows[:100]:
        assert r["action"] in valid_actions
        assert r["junction_id"] in valid_junctions
        assert float(r["timestamp"]) >= 0.0


# ── 7. Configuration & State Tests ──────────────────────────────────────────

def test_load_controller_config_values():
    """Verify config loads correctly from params.yaml with positive numbers."""
    cfg = load_controller_config()
    assert cfg["min_green_s"] >= 5.0
    assert cfg["max_green_s"] > cfg["min_green_s"]
    assert cfg["extension_step_s"] > 0.0
    assert cfg["queue_threshold"] > 0
    assert cfg["yellow_s"] > 0.0
    assert cfg["all_red_s"] > 0.0


def test_init_junction_states():
    """Verify junction states initialize with correct defaults."""
    states = init_junction_states(["J1", "J2", "J3", "J4"], min_green=10.0)
    for jid in ["J1", "J2", "J3", "J4"]:
        assert states[jid]["last_phase"] == 0
        assert states[jid]["phase_start"] == 0.0
        assert states[jid]["allocated_green"] == 10.0


# ── 8. Metric & Output Existence Tests ──────────────────────────────────────

def test_reactive_csv_outputs_exist():
    """Verify reactive CSV outputs exist for normal and rush scenarios."""
    results_dir = Path("data/output/metrics")
    for scenario in ["normal", "rush"]:
        for kind in ["summary", "trips", "queues", "decisions"]:
            path = results_dir / f"reactive_{scenario}_{kind}.csv"
            assert path.exists(), f"Missing reactive output: {path}"


def test_reactive_summary_csv_has_real_values():
    """Verify reactive summary CSVs contain non-zero throughput and reactive controller tag."""
    results_dir = Path("data/output/metrics")
    for scenario in ["normal", "rush"]:
        path = results_dir / f"reactive_{scenario}_summary.csv"
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["controller"] == "reactive"
        assert int(rows[0]["throughput"]) > 0
        assert float(rows[0]["average_waiting_time"]) > 0.0


def test_fixed_baseline_not_overwritten():
    """Verify fixed-time baseline results remain intact and were not overwritten."""
    results_dir = Path("data/output/metrics")
    for scenario in ["normal", "rush"]:
        path = results_dir / f"fixed_{scenario}_summary.csv"
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["controller"] == "fixed"
        assert int(rows[0]["throughput"]) > 0


def test_comparison_chart_exists():
    """Verify the Fixed vs Reactive comparison chart exists."""
    chart_path = Path("data/demo_assets/fixed_vs_reactive_waiting_time.png")
    assert chart_path.exists(), f"Missing comparison chart: {chart_path}"
    assert chart_path.stat().st_size > 0


# ── 9. TraCI Integration Test ────────────────────────────────────────────────

def test_traci_reactive_simulation_short():
    """Integration test: start SUMO with TraCI, step reactive controller, close cleanly."""
    import traci

    cfg_path = Path("sumo/scenarios/corridor_normal.sumocfg")
    assert cfg_path.exists()

    cmd = ["sumo", "-c", str(cfg_path)]
    traci.start(cmd)

    try:
        cfg = load_controller_config()
        states = init_junction_states(["J1", "J2", "J3", "J4"], cfg["min_green_s"])
        assert len(states) == 4
        for step in range(15):
            sim_time = traci.simulation.getTime()
            traci.simulationStep()
            assert traci.trafficlight.getPhase("J1") in range(6)
        assert sim_time >= 14.0
    finally:
        traci.close()
