"""TrafficTwin AI — Unit and Integration Tests for Spillback Controller (Module M6).

Verifies downstream capacity measurement, risk classification,
M3 -> M6 -> M5 -> TraCI control chain, safety firewall enforcement,
and real SUMO corridor integration under the blocked downstream scenario.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

import traci

from backend.app.guards.safety_firewall import validate_action
from experiments.reactive_controller import init_junction_states
from experiments.spillback_controller import (
    DOWNSTREAM_EDGES,
    apply_spillback_guard,
    calculate_spillback_risk,
    get_downstream_state,
    load_spillback_config,
    step_spillback_junction,
)

CORRIDOR_EDGES_XML = Path("sumo/net/corridor.edg.xml")
BLOCKED_SUMOCFG = Path("sumo/scenarios/corridor_blocked_downstream.sumocfg")


# ---------------------------------------------------------------------------
# Synthetic TraCI Mock Fixture
# ---------------------------------------------------------------------------
class DummyTraCIEdge:
    def __init__(self, lane_count=2, lane_length=200.0, veh_ids=None, raw_occ=0.0):
        self._lane_count = lane_count
        self._lane_length = lane_length
        self._veh_ids = veh_ids or []
        self._raw_occ = raw_occ

    def getLaneNumber(self, edge_id):
        return self._lane_count

    def getLastStepVehicleIDs(self, edge_id):
        return self._veh_ids

    def getLastStepVehicleNumber(self, edge_id):
        return len(self._veh_ids)

    def getLastStepOccupancy(self, edge_id):
        return self._raw_occ


class DummyTraCILane:
    def __init__(self, length=200.0):
        self._length = length

    def getLength(self, lane_id):
        return self._length

    def getLastStepHaltingNumber(self, lane_id):
        return 5


class DummyTraCIVehicle:
    def getLength(self, veh_id):
        return 4.5

    def getMinGap(self, veh_id):
        return 2.5


class DummyTraCITrafficLight:
    def __init__(self, phase=0):
        self.phase = phase
        self.set_phase_calls = []

    def getPhase(self, jid):
        return self.phase

    def setPhase(self, jid, p):
        self.phase = p
        self.set_phase_calls.append((jid, p))

    def setPhaseDuration(self, jid, d):
        pass


class DummyTraCIClient:
    def __init__(self, lane_count=2, lane_length=200.0, veh_ids=None, raw_occ=0.0):
        self.edge = DummyTraCIEdge(lane_count, lane_length, veh_ids, raw_occ)
        self.lane = DummyTraCILane(lane_length)
        self.vehicle = DummyTraCIVehicle()
        self.trafficlight = DummyTraCITrafficLight()


# ---------------------------------------------------------------------------
# 1. Normal downstream occupancy -> no spillback block
# ---------------------------------------------------------------------------
def test_normal_occupancy_no_spillback_block():
    downstream_state = {
        "edge_id": "J2_J3",
        "occupancy": 0.40,
        "vehicle_count": 10,
        "capacity": 53,
        "risk": "NORMAL",
    }
    m6_action, m6_reason, signal_action = apply_spillback_guard(
        proposed_action="EXTEND_GREEN",
        proposed_reason="high main queue (8), extending green",
        downstream_state=downstream_state,
        current_phase=0,
        green_duration=15.0,
        min_green=10.0,
    )
    assert m6_action == "EXTEND_GREEN"
    assert signal_action == "EXTEND_GREEN"
    assert "high main queue" in m6_reason


# ---------------------------------------------------------------------------
# 2. Warning occupancy -> warning state and extension avoided
# ---------------------------------------------------------------------------
def test_warning_occupancy_state():
    risk = calculate_spillback_risk(0.78, warning_threshold=0.75, critical_threshold=0.85)
    assert risk == "WARNING"

    downstream_state = {
        "edge_id": "J2_J3",
        "occupancy": 0.78,
        "vehicle_count": 40,
        "capacity": 53,
        "risk": "WARNING",
    }
    m6_action, m6_reason, signal_action = apply_spillback_guard(
        proposed_action="EXTEND_GREEN",
        proposed_reason="high main queue (6), extending green",
        downstream_state=downstream_state,
        current_phase=0,
        green_duration=15.0,
        min_green=10.0,
    )
    assert m6_action == "HOLD"
    assert signal_action == "HOLD"
    assert "warning: extension avoided" in m6_reason


# ---------------------------------------------------------------------------
# 3. Critical occupancy -> CRITICAL state
# ---------------------------------------------------------------------------
def test_critical_occupancy_state():
    risk = calculate_spillback_risk(0.88, warning_threshold=0.75, critical_threshold=0.85)
    assert risk == "CRITICAL"

    risk_high = calculate_spillback_risk(0.95, warning_threshold=0.75, critical_threshold=0.85)
    assert risk_high == "CRITICAL"


# ---------------------------------------------------------------------------
# 4. Critical downstream + upstream extension -> blocked
# ---------------------------------------------------------------------------
def test_critical_downstream_blocks_upstream_extension():
    downstream_state = {
        "edge_id": "J3_J4",
        "occupancy": 0.89,
        "vehicle_count": 47,
        "capacity": 53,
        "risk": "CRITICAL",
    }
    m6_action, m6_reason, signal_action = apply_spillback_guard(
        proposed_action="EXTEND_GREEN",
        proposed_reason="high main queue (14), extending green",
        downstream_state=downstream_state,
        current_phase=0,
        green_duration=12.0,
        min_green=10.0,
    )
    assert m6_action == "SPILLBACK_BLOCK"
    assert m6_reason == "downstream_occupancy_critical"
    assert signal_action == "START_TRANSITION"


# ---------------------------------------------------------------------------
# 5. Critical downstream + KEEP_GREEN -> correct behavior
# ---------------------------------------------------------------------------
def test_critical_downstream_keep_green_behavior():
    downstream_state = {
        "edge_id": "J3_J4",
        "occupancy": 0.90,
        "vehicle_count": 48,
        "capacity": 53,
        "risk": "CRITICAL",
    }
    # Case A: Min green already reached (12s >= 10s) -> initiate clearance transition
    m6_action, m6_reason, signal_action = apply_spillback_guard(
        proposed_action="KEEP_GREEN",
        proposed_reason="main demand below threshold",
        downstream_state=downstream_state,
        current_phase=0,
        green_duration=12.0,
        min_green=10.0,
    )
    assert m6_action == "SPILLBACK_BLOCK"
    assert signal_action == "START_TRANSITION"

    # Case B: Min green NOT yet reached (6s < 10s) -> preserve min green, do not transition early
    m6_action_early, _, signal_action_early = apply_spillback_guard(
        proposed_action="EXTEND_GREEN",
        proposed_reason="high queue",
        downstream_state=downstream_state,
        current_phase=0,
        green_duration=6.0,
        min_green=10.0,
    )
    assert m6_action_early == "SPILLBACK_BLOCK"
    assert signal_action_early == "HOLD"  # Prevents early transition violation in M5


# ---------------------------------------------------------------------------
# 6. Spillback block has clear reason
# ---------------------------------------------------------------------------
def test_spillback_block_has_clear_reason():
    downstream_state = {
        "edge_id": "J2_J3",
        "occupancy": 0.92,
        "vehicle_count": 49,
        "capacity": 53,
        "risk": "CRITICAL",
    }
    m6_action, m6_reason, _ = apply_spillback_guard(
        proposed_action="EXTEND_GREEN",
        proposed_reason="high queue",
        downstream_state=downstream_state,
        current_phase=0,
        green_duration=20.0,
        min_green=10.0,
    )
    assert m6_action == "SPILLBACK_BLOCK"
    assert m6_reason == "downstream_occupancy_critical"


# ---------------------------------------------------------------------------
# 7. Actual downstream edge mapping is valid in SUMO network
# ---------------------------------------------------------------------------
def test_actual_downstream_edge_mapping_is_valid():
    assert CORRIDOR_EDGES_XML.exists()
    tree = ET.parse(CORRIDOR_EDGES_XML)
    root = tree.getroot()
    edge_ids = {edge.attrib["id"] for edge in root.findall("edge")}

    for jid, edge_id in DOWNSTREAM_EDGES.items():
        assert edge_id in edge_ids, f"Downstream edge {edge_id} for {jid} not found in corridor.edg.xml"

    assert DOWNSTREAM_EDGES["J1"] == "J1_J2"
    assert DOWNSTREAM_EDGES["J2"] == "J2_J3"
    assert DOWNSTREAM_EDGES["J3"] == "J3_J4"
    assert DOWNSTREAM_EDGES["J4"] == "J4_E5"


# ---------------------------------------------------------------------------
# 8. Occupancy calculation handles zero capacity safely
# ---------------------------------------------------------------------------
def test_occupancy_calculation_handles_zero_capacity_safely():
    client_zero = DummyTraCIClient(lane_count=0, lane_length=0.0)
    state = get_downstream_state(client_zero, "J2")
    assert state["occupancy"] == 0.0
    assert state["capacity"] == 0
    assert state["risk"] == "NORMAL"

    # Edge with no vehicles
    client_empty = DummyTraCIClient(lane_count=2, lane_length=200.0, veh_ids=[])
    state_empty = get_downstream_state(client_empty, "J2")
    assert state_empty["occupancy"] == 0.0
    assert state_empty["capacity"] == 53
    assert state_empty["risk"] == "NORMAL"


# ---------------------------------------------------------------------------
# 9. Multiple junctions use correct downstream links
# ---------------------------------------------------------------------------
def test_multiple_junctions_use_correct_downstream_links():
    client = DummyTraCIClient()
    for jid, expected_edge in DOWNSTREAM_EDGES.items():
        state = get_downstream_state(client, jid)
        assert state["edge_id"] == expected_edge


# ---------------------------------------------------------------------------
# 10. M6 does not bypass M5 Safety Firewall
# ---------------------------------------------------------------------------
def test_m6_does_not_bypass_m5():
    # Set up junction in phase 0 at green time 15s (min_green=10s satisfied)
    # Downstream is critical (47 vehicles on 53 capacity link)
    veh_ids = [f"v_{i}" for i in range(47)]
    client = DummyTraCIClient(veh_ids=veh_ids, raw_occ=0.88)
    config = load_spillback_config()
    state = {
        "last_phase": 0,
        "phase_start": 0.0,
        "allocated_green": 10.0,
    }

    # Step junction: M3 proposes EXTEND_GREEN, M6 overrides to SPILLBACK_BLOCK, M5 validates transition
    record = step_spillback_junction(client, "J3", sim_time=15.0, state=state, config=config)

    assert record["action"] == "SPILLBACK_BLOCK"
    assert record["reason"] == "downstream_occupancy_critical"
    # Verify TraCI setPhase was called for yellow clearance (Phase 1)
    assert ("J3", 1) in client.trafficlight.set_phase_calls


# ---------------------------------------------------------------------------
# 11. M5 still rejects illegal signal actions under M6
# ---------------------------------------------------------------------------
def test_m5_still_rejects_illegal_signal_actions():
    config = load_spillback_config()

    # Attempt to transition before min_green is reached
    early_action = {
        "junction_id": "J2",
        "current_phase": 0,
        "requested_phase": 1,
        "action": "START_TRANSITION",
        "elapsed_green_s": 5.0,  # Below min_green 10s
    }
    result = validate_action(early_action, config)
    assert result["allowed"] is False
    assert result["reason"] == "minimum_green_not_reached"

    # Clearance bypass attempt
    bypass_action = {
        "junction_id": "J2",
        "current_phase": 0,
        "requested_phase": 2,  # Direct green -> all-red
        "action": "START_TRANSITION",
        "elapsed_green_s": 15.0,
    }
    result_bypass = validate_action(bypass_action, config)
    assert result_bypass["allowed"] is False
    assert result_bypass["reason"] == "yellow_clearance_required"


# ---------------------------------------------------------------------------
# 12. Spillback configuration loading from params.yaml
# ---------------------------------------------------------------------------
def test_spillback_config_loading():
    cfg = load_spillback_config()
    assert cfg["enabled"] is True
    assert cfg["warning_threshold"] == 0.75
    assert cfg["critical_threshold"] == 0.85
    assert cfg["min_green_s"] == 10.0
    assert cfg["max_green_s"] == 40.0


# ---------------------------------------------------------------------------
# 13. SUMO Real Integration Test: Blocked Downstream Scenario
# ---------------------------------------------------------------------------
def test_sumo_spillback_blocked_downstream_integration():
    """Runs the real SUMO corridor on blocked_downstream scenario and verifies M6 spillback detection."""
    assert BLOCKED_SUMOCFG.exists(), f"Config file not found: {BLOCKED_SUMOCFG}"

    sumo_cmd = ["sumo", "-c", str(BLOCKED_SUMOCFG)]
    traci.start(sumo_cmd)

    config = load_spillback_config()
    junction_ids = ["J1", "J2", "J3", "J4"]
    states = init_junction_states(junction_ids, config["min_green_s"])

    max_occupancies = {jid: 0.0 for jid in junction_ids}
    spillback_block_observed = False
    step_records = []

    try:
        # Run until t=350s (sufficient for downstream queue to build and trigger spillback block)
        for _ in range(350):
            sim_time = traci.simulation.getTime()
            traci.simulationStep()

            for jid in junction_ids:
                record = step_spillback_junction(traci, jid, sim_time, states[jid], config)
                step_records.append(record)

                occ = float(record["downstream_occupancy"])
                if occ > max_occupancies[jid]:
                    max_occupancies[jid] = occ

                if record["action"] == "SPILLBACK_BLOCK":
                    spillback_block_observed = True
                    assert record["spillback_risk"] == "CRITICAL"
                    assert record["reason"] == "downstream_occupancy_critical"
    finally:
        traci.close()

    # Verify that downstream occupancy on J3_J4 reached critical (> 0.85)
    assert max_occupancies["J3"] >= config["critical_threshold"], (
        f"Expected J3 downstream occupancy >= {config['critical_threshold']}, got {max_occupancies['J3']}"
    )

    # Verify that SPILLBACK_BLOCK was triggered during the simulation
    assert spillback_block_observed is True, "SPILLBACK_BLOCK was not triggered during blocked_downstream run"


# ---------------------------------------------------------------------------
# 14. Metric and CSV Output Existence Tests
# ---------------------------------------------------------------------------
def test_spillback_csv_outputs_exist():
    """Verify spillback CSV outputs exist for all four scenarios."""
    results_dir = Path("data/output/metrics")
    for scenario in ["normal", "rush", "blocked_downstream", "ambulance"]:
        for kind in ["summary", "trips", "queues", "decisions"]:
            path = results_dir / f"spillback_{scenario}_{kind}.csv"
            assert path.exists(), f"Missing spillback output: {path}"


def test_spillback_summary_csv_has_real_values():
    """Verify spillback summary CSVs contain non-zero throughput and controller tag."""
    import csv

    results_dir = Path("data/output/metrics")
    for scenario in ["normal", "rush", "blocked_downstream", "ambulance"]:
        path = results_dir / f"spillback_{scenario}_summary.csv"
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["controller"] == "spillback"
        assert int(rows[0]["throughput"]) > 0
        assert float(rows[0]["average_waiting_time"]) > 0.0


def test_m3_reactive_outputs_not_overwritten():
    """Verify prior M3 reactive outputs remain intact and unaltered."""
    import csv

    results_dir = Path("data/output/metrics")
    for scenario in ["normal", "rush"]:
        path = results_dir / f"reactive_{scenario}_summary.csv"
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["controller"] == "reactive"
        assert int(rows[0]["throughput"]) > 0
