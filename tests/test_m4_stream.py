"""
TrafficTwin AI — Module M4 Acceptance Test Suite
Simulated GPS-Like Event Stream and Replay
"""

import json
from pathlib import Path

from backend.app.stream.gps_event import (
    build_gps_event,
    extract_location_context,
    validate_gps_event,
)
from experiments.replay_gps import replay_stream

# ── 1. Schema & Required Fields ─────────────────────────────────────────────

def test_gps_event_contains_all_required_fields():
    """Verify built event contains all 15 required fields with valid types."""
    event = build_gps_event(
        vehicle_id="car_1",
        vehicle_type="car",
        timestamp=10.0,
        x=205.5,
        y=150.0,
        speed_mps=13.89,
        heading=90.0,
        lane_id="W0_J1_0",
        road_id="W0_J1",
    )

    required_fields = [
        "event_type",
        "event_id",
        "vehicle_id",
        "vehicle_type",
        "timestamp",
        "corridor_id",
        "junction_id",
        "lane_id",
        "road_segment_id",
        "x",
        "y",
        "speed_kmph",
        "heading_degrees",
        "source",
        "freshness_seconds",
    ]
    for field in required_fields:
        assert field in event, f"Missing field: {field}"

    assert event["event_type"] == "vehicle_position"
    assert event["source"] == "simulated_sumo"
    assert event["corridor_id"] == "corridor_4j"
    assert event["freshness_seconds"] == 0.0


# ── 2. Speed Conversion ─────────────────────────────────────────────────────

def test_speed_conversion_mps_to_kmph():
    """Verify speed in m/s is correctly converted to km/h (speed * 3.6)."""
    # 10 m/s -> 36.0 km/h
    event = build_gps_event("v1", "car", 1.0, 0.0, 0.0, 10.0, 0.0, "l", "r")
    assert event["speed_kmph"] == 36.0

    # 13.8889 m/s (~50 km/h) -> 50.0 km/h
    event2 = build_gps_event("v2", "car", 1.0, 0.0, 0.0, 13.8889, 0.0, "l", "r")
    assert event2["speed_kmph"] == 50.0

    # 0 m/s -> 0.0 km/h
    event3 = build_gps_event("v3", "car", 1.0, 0.0, 0.0, 0.0, 0.0, "l", "r")
    assert event3["speed_kmph"] == 0.0


# ── 3. Deterministic Event ID ───────────────────────────────────────────────

def test_event_id_is_deterministic():
    """Verify event ID follows deterministic gps_<vehicle_id>_<timestamp> format."""
    e1 = build_gps_event("bus_42", "bus", 24.0, 100.0, 150.0, 8.5, 90.0, "l", "r")
    e2 = build_gps_event("bus_42", "bus", 24.0, 100.0, 150.0, 8.5, 90.0, "l", "r")
    assert e1["event_id"] == "gps_bus_42_24.0"
    assert e1["event_id"] == e2["event_id"]


# ── 4. Location Context Mapping ─────────────────────────────────────────────

def test_location_context_link_vs_junction():
    """Verify road segment and junction ID extraction."""
    # Free link between J1 and J2
    j_id, seg_id = extract_location_context("J1_J2", "J1_J2_0")
    assert j_id is None
    assert seg_id == "J1_J2"

    # Internal junction edge inside J3
    j_id_int, seg_id_int = extract_location_context(":J3_4", ":J3_4_0")
    assert j_id_int == "J3"
    assert seg_id_int == ":J3_4"


# ── 5. Validation Function ──────────────────────────────────────────────────

def test_validate_gps_event_accepts_valid():
    """Valid event passes schema validation."""
    event = build_gps_event("v1", "taxi", 5.0, 10.0, 20.0, 12.0, 180.0, "lane_1", "road_1")
    is_valid, msg = validate_gps_event(event)
    assert is_valid is True
    assert msg == ""


def test_validate_gps_event_rejects_malformed():
    """Malformed event is rejected with clear error message."""
    # Missing vehicle_id
    bad1 = {"event_type": "vehicle_position", "event_id": "gps_v1_1.0", "timestamp": 1.0}
    is_valid, msg = validate_gps_event(bad1)
    assert is_valid is False
    assert "vehicle_id" in msg

    # Invalid event_type
    bad2 = build_gps_event("v1", "car", 1.0, 0.0, 0.0, 10.0, 0.0, "l", "r")
    bad2["event_type"] = "unknown_event"
    is_valid, msg = validate_gps_event(bad2)
    assert is_valid is False
    assert "event_type" in msg

    # Negative speed
    bad3 = build_gps_event("v1", "car", 1.0, 0.0, 0.0, 10.0, 0.0, "l", "r")
    bad3["speed_kmph"] = -5.0
    is_valid, msg = validate_gps_event(bad3)
    assert is_valid is False
    assert "Speed" in msg


# ── 6. JSONL Writing and Reading ────────────────────────────────────────────

def test_jsonl_write_and_read(tmp_path):
    """Verify writing events to JSONL and reading back produces identical data."""
    out_file = tmp_path / "test_stream.jsonl"
    events = [
        build_gps_event("v1", "car", 2.0, 10.0, 20.0, 5.0, 90.0, "l1", "r1"),
        build_gps_event("v2", "bus", 2.0, 30.0, 40.0, 8.0, 180.0, "l2", "r2"),
        build_gps_event("v1", "car", 4.0, 25.0, 20.0, 6.0, 90.0, "l1", "r1"),
    ]

    with open(out_file, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")

    assert out_file.exists()

    with open(out_file, encoding="utf-8") as f:
        read_events = [json.loads(line) for line in f]

    assert len(read_events) == 3
    assert read_events[0]["event_id"] == "gps_v1_2.0"
    assert read_events[1]["vehicle_id"] == "v2"
    assert read_events[2]["timestamp"] == 4.0


# ── 7. Replay Functionality ─────────────────────────────────────────────────

def test_replay_processes_multiple_events(tmp_path):
    """Replay processes multiple events and returns accurate summary statistics."""
    stream_file = tmp_path / "stream.jsonl"
    events = [
        build_gps_event("c1", "car", 0.0, 1.0, 2.0, 10.0, 0.0, "l", "r"),
        build_gps_event("c2", "car", 0.0, 5.0, 6.0, 12.0, 0.0, "l", "r"),
        build_gps_event("c1", "car", 2.0, 15.0, 2.0, 14.0, 0.0, "l", "r"),
    ]
    with open(stream_file, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")

    summary = replay_stream(stream_file, quiet=True)
    assert summary["total_events"] == 3
    assert summary["valid_events"] == 3
    assert summary["invalid_events"] == 0
    assert summary["unique_vehicles"] == 2
    assert summary["start_time_s"] == 0.0
    assert summary["end_time_s"] == 2.0


def test_replay_empty_file_handled_cleanly(tmp_path):
    """Replay handles empty file cleanly without crashing."""
    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("", encoding="utf-8")

    summary = replay_stream(empty_file, quiet=True)
    assert summary["total_events"] == 0
    assert summary["valid_events"] == 0
    assert summary["unique_vehicles"] == 0


def test_replay_skips_malformed_lines(tmp_path):
    """Replay counts invalid lines and continues processing valid ones."""
    mixed_file = tmp_path / "mixed.jsonl"
    valid_e = build_gps_event("v1", "car", 1.0, 0.0, 0.0, 5.0, 0.0, "l", "r")
    with open(mixed_file, "w", encoding="utf-8") as f:
        f.write("not valid json\n")
        f.write(json.dumps(valid_e) + "\n")
        f.write('{"event_type": "unknown"}\n')

    summary = replay_stream(mixed_file, quiet=True)
    assert summary["total_events"] == 3
    assert summary["valid_events"] == 1
    assert summary["invalid_events"] == 2


def test_replay_duplicate_observations_do_not_crash(tmp_path):
    """Multiple observations for the same vehicle update state without crashing."""
    dup_file = tmp_path / "dup.jsonl"
    e1 = build_gps_event("v1", "car", 2.0, 10.0, 0.0, 10.0, 90.0, "l", "r")
    e2 = build_gps_event("v1", "car", 4.0, 25.0, 0.0, 12.0, 90.0, "l", "r")
    with open(dup_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(e1) + "\n")
        f.write(json.dumps(e2) + "\n")

    summary = replay_stream(dup_file, quiet=True)
    assert summary["valid_events"] == 2
    assert summary["unique_vehicles"] == 1


# ── 8. Integration Test with SUMO ───────────────────────────────────────────

def test_sumo_to_gps_event_generation_short(tmp_path):
    """Integration test: start SUMO, capture 5 steps of events, verify schema and JSONL."""
    import traci

    cfg_path = Path("sumo/scenarios/corridor_normal.sumocfg")
    assert cfg_path.exists()

    out_file = tmp_path / "test_sumo_gps.jsonl"
    cmd = ["sumo", "-c", str(cfg_path)]
    traci.start(cmd)

    events_captured = []
    try:
        for _ in range(10):
            sim_time = traci.simulation.getTime()
            traci.simulationStep()
            vids = traci.vehicle.getIDList()
            for vid in vids:
                pos = traci.vehicle.getPosition(vid)
                speed = traci.vehicle.getSpeed(vid)
                heading = traci.vehicle.getAngle(vid)
                lane = traci.vehicle.getLaneID(vid)
                road = traci.vehicle.getRoadID(vid)
                vtype = traci.vehicle.getTypeID(vid)

                event = build_gps_event(
                    vehicle_id=vid,
                    vehicle_type=vtype,
                    timestamp=sim_time,
                    x=pos[0],
                    y=pos[1],
                    speed_mps=speed,
                    heading=heading,
                    lane_id=lane,
                    road_id=road,
                )
                is_valid, msg = validate_gps_event(event)
                assert is_valid, f"Generated event failed validation: {msg}"
                events_captured.append(event)
    finally:
        traci.close()

    assert len(events_captured) > 0

    with open(out_file, "w", encoding="utf-8") as f:
        for e in events_captured:
            f.write(json.dumps(e) + "\n")

    summary = replay_stream(out_file, quiet=True)
    assert summary["valid_events"] == len(events_captured)
    assert summary["invalid_events"] == 0


def test_events_remain_ordered_by_timestamp():
    """Verify generated JSONL stream maintains non-decreasing timestamp ordering."""
    normal_stream = Path("data/output/gps/normal.jsonl")
    assert normal_stream.exists()

    last_ts = 0.0
    with open(normal_stream, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 500:
                break
            record = json.loads(line)
            ts = float(record["timestamp"])
            assert ts >= last_ts, f"Timestamp decreased: {ts} < {last_ts}"
            last_ts = ts


def test_all_scenario_gps_streams_exist_and_valid():
    """Verify all four scenario streams exist with real events in data/output/gps/."""
    gps_dir = Path("data/output/gps")
    for scenario in ["normal", "rush", "blocked_downstream", "ambulance"]:
        stream_path = gps_dir / f"{scenario}.jsonl"
        assert stream_path.exists(), f"Stream missing: {stream_path}"
        summary = replay_stream(stream_path, quiet=True)
        assert summary["total_events"] > 0
        assert summary["valid_events"] == summary["total_events"]
        assert summary["invalid_events"] == 0
        assert summary["unique_vehicles"] > 0

