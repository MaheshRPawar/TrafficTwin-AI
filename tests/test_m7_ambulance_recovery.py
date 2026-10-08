"""TrafficTwin AI — Module M7 Acceptance Test Suite.

Verifies:
1. Fairness Debt calculation, missed cycle tracking, and side-street starvation prevention.
2. Staged Ambulance Priority, ETA calculation, and downstream capacity gating.
3. Post-Emergency Bounded Recovery, delay compensation, and return to normal mode.
4. M3 -> M7 -> M6 -> M5 -> TraCI safety hierarchy and firewall compliance.
"""

from pathlib import Path

import pytest
import traci

from experiments.emergency_controller import (
    AmbulancePreemptionManager,
    FairnessTracker,
    PostEmergencyRecoveryManager,
    load_m7_config,
    step_m7_junction,
)
from experiments.reactive_controller import init_junction_states

AMBULANCE_SUMOCFG = Path("sumo/scenarios/corridor_ambulance.sumocfg")


# ---------------------------------------------------------------------------
# TraCI Mock Classes for Fast Unit Testing
# ---------------------------------------------------------------------------
class MockTraCIEdge:
    def __init__(self, lane_count: int = 2, lane_length: float = 200.0, veh_ids: list[str] | None = None, raw_occ: float = 0.0):
        self._lane_count = lane_count
        self._lane_length = lane_length
        self._veh_ids = veh_ids or []
        self._raw_occ = raw_occ

    def getLaneNumber(self, edge_id: str) -> int:
        return self._lane_count

    def getLastStepVehicleIDs(self, edge_id: str) -> list[str]:
        return self._veh_ids

    def getLastStepVehicleNumber(self, edge_id: str) -> int:
        return len(self._veh_ids)

    def getLastStepOccupancy(self, edge_id: str) -> float:
        return self._raw_occ


class MockTraCILane:
    def __init__(self, halting: int = 3, veh_ids: list[str] | None = None):
        self.halting = halting
        self.veh_ids = veh_ids or []

    def getLastStepHaltingNumber(self, lane_id: str) -> int:
        return self.halting

    def getLastStepVehicleIDs(self, lane_id: str) -> list[str]:
        return self.veh_ids

    def getLength(self, lane_id: str) -> float:
        return 200.0


class MockTraCIVehicle:
    def __init__(self, speeds: dict[str, float] | None = None, wait_times: dict[str, float] | None = None):
        self.speeds = speeds or {}
        self.wait_times = wait_times or {}

    def getSpeed(self, vid: str) -> float:
        return self.speeds.get(vid, 0.0)

    def getWaitingTime(self, vid: str) -> float:
        return self.wait_times.get(vid, 0.0)

    def getLength(self, vid: str) -> float:
        return 4.5

    def getMinGap(self, vid: str) -> float:
        return 2.5


class MockTraCITrafficLight:
    def __init__(self, phase: int = 0):
        self.phase = phase
        self.phase_duration = 40.0
        self.set_phase_calls: list[tuple[str, int]] = []

    def getPhase(self, jid: str) -> int:
        return self.phase

    def setPhase(self, jid: str, p: int) -> None:
        self.phase = p
        self.set_phase_calls.append((jid, p))

    def setPhaseDuration(self, jid: str, d: float) -> None:
        self.phase_duration = d


class MockTraCIClient:
    def __init__(self, phase: int = 0, raw_occ: float = 0.0):
        self.edge = MockTraCIEdge(raw_occ=raw_occ)
        self.lane = MockTraCILane()
        self.vehicle = MockTraCIVehicle()
        self.trafficlight = MockTraCITrafficLight(phase=phase)


# ---------------------------------------------------------------------------
# 1. Fairness Debt Unit Tests
# ---------------------------------------------------------------------------
def test_fairness_tracker_initialization():
    tracker = FairnessTracker(["J1", "J2", "J3", "J4"])
    assert "J1" in tracker.state
    assert tracker.state["J1"]["cross"]["fairness_debt"] == 0.0
    assert tracker.state["J1"]["cross"]["missed_cycles"] == 0
    assert tracker.state["J1"]["cross"]["starvation_risk"] is False


def test_fairness_debt_accumulation_and_starvation():
    cfg = load_m7_config()
    cfg["starvation_threshold"] = 20.0
    tracker = FairnessTracker(["J1"], cfg)

    client = MockTraCIClient()
    client.lane.veh_ids = ["veh_w1", "veh_w2"]
    client.vehicle.speeds = {"veh_w1": 0.1, "veh_w2": 0.2}
    client.vehicle.wait_times = {"veh_w1": 40.0, "veh_w2": 60.0}

    # Simulate cycle progress under main green (cross waiting)
    metrics = tracker.update(client, "J1", current_phase=0, sim_time=30.0)
    assert metrics["cross_avg_wait"] == 50.0
    assert metrics["cross_max_wait"] == 60.0
    assert metrics["cross_debt"] >= 40.0  # 0.4*50 + 0.4*60 = 44.0
    assert metrics["cross_starvation_risk"] is True


def test_fairness_reset_on_service():
    tracker = FairnessTracker(["J1"])
    tracker.state["J1"]["cross"]["fairness_debt"] = 55.0
    tracker.state["J1"]["cross"]["missed_cycles"] = 3
    tracker.state["J1"]["cross"]["starvation_risk"] = True

    tracker.reset_cross_debt("J1")
    assert tracker.state["J1"]["cross"]["fairness_debt"] == 0.0
    assert tracker.state["J1"]["cross"]["missed_cycles"] == 0
    assert tracker.state["J1"]["cross"]["starvation_risk"] is False


# ---------------------------------------------------------------------------
# 2. Ambulance Priority & ETA Unit Tests
# ---------------------------------------------------------------------------
def test_ambulance_priority_staged_when_downstream_safe():
    amb_manager = AmbulancePreemptionManager()
    amb_info = {
        "vehicle_id": "emerg_1",
        "edge": "W0_J1",
        "target_junction": "J1",
        "eta_s": 8.0,
    }
    downstream_safe = {"risk": "NORMAL", "occupancy": 0.25}

    # If current phase is Main Green (Phase 0) -> KEEP_GREEN
    status, action, reason = amb_manager.evaluate_priority_request(
        junction_id="J1",
        amb_info=amb_info,
        downstream_state=downstream_safe,
        current_phase=0,
        green_duration=15.0,
    )
    assert status == "PRIORITY_STAGED"
    assert action == "KEEP_GREEN"
    assert "DOWNSTREAM_CAPACITY_SUFFICIENT" in reason


def test_ambulance_priority_delayed_when_downstream_critical():
    amb_manager = AmbulancePreemptionManager()
    amb_info = {
        "vehicle_id": "emerg_1",
        "edge": "W0_J1",
        "target_junction": "J1",
        "eta_s": 6.0,
    }
    # Critical downstream link (occupancy >= 85%)
    downstream_critical = {"risk": "CRITICAL", "occupancy": 0.90}

    status, action, reason = amb_manager.evaluate_priority_request(
        junction_id="J1",
        amb_info=amb_info,
        downstream_state=downstream_critical,
        current_phase=0,
        green_duration=15.0,
    )
    assert status == "PRIORITY_DELAYED"
    assert action == "HOLD"
    assert "DOWNSTREAM_CAPACITY_CRITICAL" in reason


def test_ambulance_priority_respects_cross_min_green():
    amb_manager = AmbulancePreemptionManager()
    amb_info = {
        "vehicle_id": "emerg_1",
        "edge": "W0_J1",
        "target_junction": "J1",
        "eta_s": 8.0,
    }
    downstream_safe = {"risk": "NORMAL", "occupancy": 0.20}

    # Cross Green (Phase 3) active for only 4.0s (< min_green 10s)
    status, action, reason = amb_manager.evaluate_priority_request(
        junction_id="J1",
        amb_info=amb_info,
        downstream_state=downstream_safe,
        current_phase=3,
        green_duration=4.0,
    )
    assert status == "PRIORITY_STAGED"
    assert action == "HOLD"  # Must wait for min green before switching
    assert "waiting for cross min green" in reason

    # Cross Green (Phase 3) active for 11.0s (>= min_green 10s) -> safe transition
    status, action, reason = amb_manager.evaluate_priority_request(
        junction_id="J1",
        amb_info=amb_info,
        downstream_state=downstream_safe,
        current_phase=3,
        green_duration=11.0,
    )
    assert status == "PRIORITY_STAGED"
    assert action == "START_TRANSITION"


# ---------------------------------------------------------------------------
# 3. Post-Emergency Bounded Recovery Tests
# ---------------------------------------------------------------------------
def test_post_emergency_recovery_flow():
    rec_manager = PostEmergencyRecoveryManager()
    fairness = FairnessTracker(["J1"])
    fairness.state["J1"]["cross"]["fairness_debt"] = 30.0

    # Trigger recovery after preemption ends
    rec_manager.trigger_recovery("J1", sim_time=65.0, cross_debt=30.0)
    assert rec_manager.recovery_state["J1"]["active"] is True
    assert rec_manager.recovery_state["J1"]["allocated_green"] >= 10.0
    assert rec_manager.recovery_state["J1"]["allocated_green"] <= 25.0

    # Main Green active -> transition to Cross Green
    in_rec, act, rsn = rec_manager.evaluate_recovery_policy(
        junction_id="J1",
        current_phase=0,
        green_duration=12.0,
        sim_time=66.0,
        fairness_tracker=fairness,
    )
    assert in_rec is True
    assert act == "START_TRANSITION"
    assert "RECOVERY_DISPATCH" in rsn

    # Cross Green servicing
    in_rec, act, rsn = rec_manager.evaluate_recovery_policy(
        junction_id="J1",
        current_phase=3,
        green_duration=5.0,
        sim_time=72.0,
        fairness_tracker=fairness,
    )
    assert in_rec is True
    assert act == "KEEP_GREEN"

    # Cross Green completed allocated duration -> return to normal
    in_rec, act, rsn = rec_manager.evaluate_recovery_policy(
        junction_id="J1",
        current_phase=3,
        green_duration=26.0,
        sim_time=93.0,
        fairness_tracker=fairness,
    )
    assert in_rec is True
    assert act == "START_TRANSITION"
    assert "RECOVERY_COMPLETE" in rsn
    assert rec_manager.recovery_state["J1"]["active"] is False


# ---------------------------------------------------------------------------
# 4. Integrated Decision Chain & Firewall Verification
# ---------------------------------------------------------------------------
def test_step_m7_junction_firewall_validation():
    cfg = load_m7_config()
    fairness = FairnessTracker(["J1"], cfg)
    amb_manager = AmbulancePreemptionManager(cfg)
    rec_manager = PostEmergencyRecoveryManager(cfg)
    state = {"last_phase": 0, "phase_start": 0.0, "allocated_green": 10.0}

    client = MockTraCIClient(phase=0)

    # Step at t=5s (min green not satisfied yet)
    record = step_m7_junction(
        traci_client=client,
        junction_id="J1",
        sim_time=5.0,
        state=state,
        config=cfg,
        fairness_tracker=fairness,
        ambulance_manager=amb_manager,
        recovery_manager=rec_manager,
        amb_info=None,
    )
    assert record["action"] == "KEEP_GREEN"
    assert "minimum green not satisfied" in record["reason"]


# ---------------------------------------------------------------------------
# 5. Full Corridor SUMO Integration Test
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not AMBULANCE_SUMOCFG.exists(), reason="Corridor ambulance scenario sumocfg missing")
def test_sumo_corridor_ambulance_simulation_run(tmp_path):
    """Run full headless SUMO corridor simulation with M7 controller and verify metrics."""
    out_trip = tmp_path / "test_m7_tripinfo.xml"
    out_queue = tmp_path / "test_m7_queue.xml"
    out_summary = tmp_path / "test_m7_summary.xml"

    sumo_cmd = [
        "sumo",
        "-c",
        str(AMBULANCE_SUMOCFG),
        "--tripinfo-output",
        str(out_trip),
        "--queue-output",
        str(out_queue),
        "--summary-output",
        str(out_summary),
    ]

    traci.start(sumo_cmd)
    cfg = load_m7_config()
    junction_ids = ["J1", "J2", "J3", "J4"]

    fairness = FairnessTracker(junction_ids, cfg)
    amb_manager = AmbulancePreemptionManager(cfg)
    rec_manager = PostEmergencyRecoveryManager(cfg)
    states = init_junction_states(junction_ids, cfg["min_green_s"])

    for jid in junction_ids:
        traci.trafficlight.setPhaseDuration(jid, cfg["max_green_s"])

    staged_priority_seen = False
    step = 0

    try:
        while traci.simulation.getMinExpectedNumber() > 0 and step < 200:
            sim_time = traci.simulation.getTime()
            traci.simulationStep()

            amb_info = amb_manager.detect_ambulance(traci, sim_time)

            for jid in junction_ids:
                rec = step_m7_junction(
                    traci_client=traci,
                    junction_id=jid,
                    sim_time=sim_time,
                    state=states[jid],
                    config=cfg,
                    fairness_tracker=fairness,
                    ambulance_manager=amb_manager,
                    recovery_manager=rec_manager,
                    amb_info=amb_info,
                )
                if rec["emergency_status"] == "PRIORITY_STAGED":
                    staged_priority_seen = True

            step += 1
    finally:
        traci.close()

    assert step > 50
    assert staged_priority_seen is True, "Expected staged ambulance priority to be triggered during corridor transit"
