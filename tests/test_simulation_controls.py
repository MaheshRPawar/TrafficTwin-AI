"""Regression and end-to-end tests for interactive simulation controls,
corridor road links, vehicle streams, and locate endpoints.
"""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_simulation_status_endpoint():
    response = client.get("/api/simulation/status")
    assert response.status_code == 200
    data = response.json()
    assert "sim_state" in data
    assert "sim_time_s" in data
    assert "total_time_s" in data
    assert "speed_multiplier" in data
    assert data["sim_state"] in ["RUNNING", "PAUSED", "STOPPED"]


def test_simulation_control_play_and_pause():
    # Pause
    res_pause = client.post(
        "/api/simulation/control",
        json={"action": "pause", "speed": 1.0, "step": 1},
    )
    assert res_pause.status_code == 200
    assert res_pause.json()["sim_state"] == "PAUSED"

    # Play
    res_play = client.post(
        "/api/simulation/control",
        json={"action": "play", "speed": 2.0, "step": 1},
    )
    assert res_play.status_code == 200
    assert res_play.json()["sim_state"] == "RUNNING"
    assert res_play.json()["speed_multiplier"] == 2.0


def test_simulation_control_step_and_reset():
    # Step
    res_step = client.post(
        "/api/simulation/control",
        json={"action": "step", "speed": 1.0, "step": 1},
    )
    assert res_step.status_code == 200
    assert res_step.json()["status"] in ["PAUSED", "RUNNING"]

    # Reset
    res_reset = client.post(
        "/api/simulation/control",
        json={"action": "reset", "speed": 1.0, "step": 1},
    )
    assert res_reset.status_code == 200
    assert res_reset.json()["sim_time_s"] == 0.0


def test_scenarios_roads_endpoint():
    response = client.get("/api/scenarios/blocked_downstream/roads")
    assert response.status_code == 200
    roads = response.json()
    assert isinstance(roads, list)
    assert len(roads) == 5

    road_ids = [r["road_id"] for r in roads]
    assert "W0_J1" in road_ids
    assert "J1_J2" in road_ids
    assert "J2_J3" in road_ids
    assert "J3_J4" in road_ids
    assert "J4_E5" in road_ids

    # Bottleneck road J3_J4 in blocked_downstream has high occupancy
    bottleneck = next(r for r in roads if r["road_id"] == "J3_J4")
    assert bottleneck["occupancy_percent"] >= 80.0
    assert bottleneck["status"] == "SPILLBACK RISK"


def test_scenarios_vehicles_endpoint():
    response = client.get("/api/scenarios/blocked_downstream/vehicles")
    assert response.status_code == 200
    vehicles = response.json()
    assert isinstance(vehicles, list)
    assert len(vehicles) >= 3

    veh_ids = [v["vehicle_id"] for v in vehicles]
    assert "amb_1" in veh_ids
    assert "veh_eb_12" in veh_ids
    assert "veh_eb_18" in veh_ids

    amb = next(v for v in vehicles if v["vehicle_id"] == "amb_1")
    assert amb["type"] == "emergency"
    assert amb["speed_kmh"] > 0
