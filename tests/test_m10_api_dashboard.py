"""TrafficTwin AI — Module M10 API & Dashboard Integration Tests.

Verifies FastAPI endpoints, corridor state snapshots, M9 plan results,
audit logging, replay traces, and role-based operator authorization.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import AUDIT_LOG, RECOMMENDATIONS, app


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_health_endpoints(client):
    """Verify /health and /api/health return expected engine and safety metadata."""
    for path in ("/health", "/api/health"):
        res = client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "connected"
        assert data["sim_engine"] == "SUMO 1.27.1"
        assert data["firewall_active"] is True
        assert data["spillback_guard_active"] is True
        assert data["planner_active"] is True
        assert data["fail_safe_mode"] == "PREDICTIVE"


def test_scenarios_listing(client):
    """Verify scenario listing and summary retrieval."""
    res = client.get("/api/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) == 4
    scenario_ids = [s["id"] for s in scenarios]
    assert "blocked_downstream" in scenario_ids
    assert "normal" in scenario_ids
    assert "rush" in scenario_ids
    assert "ambulance" in scenario_ids


def test_scenario_summary_404(client):
    """Verify 404 on non-existent scenario."""
    res = client.get("/api/scenarios/invalid_scenario_id/summary")
    assert res.status_code == 404


def test_corridor_state_snapshot(client):
    """Verify /api/corridor/state exposes all required corridor, safety, and M9 plan attributes."""
    res = client.get("/api/corridor/state?scenario=blocked_downstream")
    assert res.status_code == 200
    data = res.json()

    # Corridor and junctions
    assert data["scenario"] == "blocked_downstream"
    assert data["controller_mode"] == "PREDICTIVE"
    assert "J1" in data and "J2" in data and "J3" in data and "J4" in data
    assert data["J3"]["status"] == "CRITICAL"
    assert data["J3"]["occupancy"] > 85.0
    assert data["J3"]["m6_override"] is True
    assert data["risk"] == "CRITICAL"

    # Queues, Phases, and Downstream
    assert "queue" in data
    assert "signal_phase" in data
    assert "downstream_occupancy" in data

    # M7 states
    assert "fairness_state" in data
    assert "emergency_state" in data

    # M9 selected plan
    assert "selected_plan" in data
    selected = data["selected_plan"]
    assert "PLAN" in selected["plan_name"].upper() or "CLEARING" in selected["plan_name"].upper()
    assert "total_score" in selected
    assert "scores" in selected
    assert "all_plans" in selected
    assert len(selected["all_plans"]) == 3


def test_current_recommendation(client):
    """Verify /api/recommendations/current returns structured recommendation with M3, M5, M6, M7, M9 traces."""
    res = client.get("/api/recommendations/current?scenario=blocked_downstream")
    assert res.status_code == 200
    rec = res.json()

    assert "recommendation_id" in rec
    assert rec["junction"] == "J3"
    assert "proposed_action" in rec
    assert "reason" in rec
    assert "m3_decision" in rec
    assert "m6_decision" in rec
    assert "m5_validation" in rec
    assert "m7_fairness_emergency_state" in rec
    assert "m9_selected_plan" in rec
    assert rec["m5_validation"]["allowed"] is True


def test_audit_events_endpoint(client):
    """Verify /api/audit-events returns immutable operational log entries."""
    res = client.get("/api/audit-events?limit=10")
    assert res.status_code == 200
    events = res.json()
    assert isinstance(events, list)
    assert len(events) >= 1
    sample = events[0]
    assert "event_id" in sample
    assert "timestamp" in sample
    assert "event_type" in sample
    assert "junction_id" in sample
    assert "details" in sample


def test_replay_trace_endpoint(client):
    """Verify /api/replay returns chronological 7-layer control chain steps."""
    res = client.get("/api/replay?scenario=blocked_downstream")
    assert res.status_code == 200
    steps = res.json()
    assert len(steps) == 7
    layers = [s["layer"] for s in steps]
    assert "TRAFFIC STATE" in layers
    assert "REACTIVE CONTROL" in layers
    assert "DOWNSTREAM CHECK" in layers
    assert "SPILLBACK PROTECTION" in layers
    assert "DIGITAL TWIN EVALUATOR" in layers
    assert "SAFETY FIREWALL" in layers
    assert "SIGNAL ACTION" in layers


def test_approval_viewer_forbidden(client):
    """Verify VIEWER role receives HTTP 403 Forbidden on approval attempt."""
    res = client.post(
        "/api/recommendations/REC-2026-J3-0887/approve-simulation",
        headers={"X-User-Role": "VIEWER"},
        json={"notes": "Viewer attempt"},
    )
    assert res.status_code == 403
    assert "VIEWER" in res.json()["detail"]


def test_approval_unknown_recommendation_404(client):
    """Verify HTTP 404 when approving non-existent recommendation ID."""
    res = client.post(
        "/api/recommendations/REC-NONEXISTENT-9999/approve-simulation",
        headers={"X-User-Role": "OPERATOR"},
        json={"notes": "Valid role, invalid ID"},
    )
    assert res.status_code == 404


def test_approval_operator_success(client):
    """Verify OPERATOR and ADMIN roles can successfully authorize pre-validated recommendations."""
    target_id = "REC-2026-J3-0887"
    initial_audits_count = len(AUDIT_LOG)

    res = client.post(
        f"/api/recommendations/{target_id}/approve-simulation",
        headers={"X-User-Role": "OPERATOR"},
        json={"notes": "Authorized by duty traffic operator"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "APPROVED"
    assert body["recommendation_id"] == target_id
    assert body["approved_by"] == "OPERATOR"
    assert "audit_event_id" in body

    # Verify recommendation status updated in store
    assert RECOMMENDATIONS[target_id]["status"] == "APPROVED"
    # Verify audit event was logged
    assert len(AUDIT_LOG) == initial_audits_count + 1
    latest_audit = AUDIT_LOG[-1]
    assert latest_audit["event_type"] == "operator_approval"
    assert latest_audit["junction_id"] == "J3"


def test_approval_rejects_unauthorized_role(client):
    """Verify arbitrary unrecognized roles are rejected."""
    res = client.post(
        "/api/recommendations/REC-2026-J3-0887/approve-simulation",
        headers={"X-User-Role": "PUBLIC_USER"},
    )
    assert res.status_code == 403
