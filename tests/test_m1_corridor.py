"""
M1 Acceptance Gate Test Suite — Four-Junction SUMO Corridor
"""

import importlib.util
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

# Load gen_routes dynamically to avoid collision with installed eclipse-sumo package
spec = importlib.util.spec_from_file_location("gen_routes", Path("sumo/scripts/gen_routes.py"))
assert spec is not None and spec.loader is not None
gen_routes_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen_routes_mod)
generate_routes = gen_routes_mod.generate_routes


def test_corridor_network_structure():
    """Verify corridor.net.xml contains J1-J4 with 6-phase safe traffic signals."""
    net_path = Path("sumo/net/corridor.net.xml")
    assert net_path.exists(), f"Missing network file: {net_path}"

    tree = ET.parse(net_path)
    root = tree.getroot()

    # Verify junction nodes
    junctions = {j.attrib["id"]: j.attrib for j in root.findall("junction")}
    for j_id in ["J1", "J2", "J3", "J4"]:
        assert j_id in junctions, f"Junction {j_id} not found in net.xml"
        assert junctions[j_id]["type"] == "traffic_light", f"Junction {j_id} must be traffic_light"

    # Verify traffic light programs and phases
    tl_logics = {tl.attrib["id"]: tl for tl in root.findall("tlLogic")}
    for tl_id in ["J1", "J2", "J3", "J4"]:
        assert tl_id in tl_logics, f"Traffic light logic {tl_id} not found"
        phases = tl_logics[tl_id].findall("phase")
        assert len(phases) == 6, f"Expected 6 phases for {tl_id}, found {len(phases)}"

        # Check phase names and durations
        phase_names = [p.attrib.get("name", "") for p in phases]
        assert "MAIN_GREEN" in phase_names
        assert "MAIN_YELLOW" in phase_names
        assert "ALL_RED_1" in phase_names
        assert "CROSS_GREEN" in phase_names
        assert "CROSS_YELLOW" in phase_names
        assert "ALL_RED_2" in phase_names

        # Total cycle length must be 60s
        total_duration = sum(int(p.attrib["duration"]) for p in phases)
        assert total_duration == 60, f"Cycle duration should be 60s, got {total_duration}"


def test_vehicle_types_and_routes_exist():
    """Verify all 4 vehicle types and 4 scenario route files exist."""
    routes_dir = Path("sumo/routes")
    scenarios = ["normal", "rush", "blocked_downstream", "ambulance"]

    for sc in scenarios:
        route_file = routes_dir / f"corridor_{sc}.rou.xml"
        assert route_file.exists(), f"Missing route file: {route_file}"

        tree = ET.parse(route_file)
        root = tree.getroot()

        vtypes = {vt.attrib["id"]: vt.attrib for vt in root.findall("vType")}
        for vt_id in ["car", "taxi", "bus", "ambulance"]:
            assert vt_id in vtypes, f"Vehicle type {vt_id} missing in {route_file.name}"

        vehicles = root.findall("vehicle")
        assert len(vehicles) > 0, f"No vehicles defined in {route_file.name}"

    # Verify specific scenario properties
    # 1. Ambulance scenario contains emerg_1
    amb_tree = ET.parse(routes_dir / "corridor_ambulance.rou.xml")
    amb_veh_ids = [v.attrib["id"] for v in amb_tree.getroot().findall("vehicle")]
    assert "emerg_1" in amb_veh_ids, "emerg_1 vehicle not found in ambulance scenario"

    # 2. Blocked downstream contains incident bottleneck vehicle with stop
    blocked_tree = ET.parse(routes_dir / "corridor_blocked_downstream.rou.xml")
    blocked_stops = blocked_tree.getroot().findall(".//stop")
    assert len(blocked_stops) >= 1, "Bottleneck stop element missing in blocked_downstream scenario"


def test_sumo_configurations_valid():
    """Verify .sumocfg files exist and reference valid network and route files."""
    scenarios_dir = Path("sumo/scenarios")
    cfg_files = [
        "corridor_normal.sumocfg",
        "corridor_rush.sumocfg",
        "corridor_blocked_downstream.sumocfg",
        "corridor_ambulance.sumocfg",
    ]

    for cfg_name in cfg_files:
        cfg_path = scenarios_dir / cfg_name
        assert cfg_path.exists(), f"Config file missing: {cfg_path}"

        tree = ET.parse(cfg_path)
        net_val = tree.find(".//net-file").attrib["value"]
        route_val = tree.find(".//route-files").attrib["value"]

        resolved_net = (scenarios_dir / net_val).resolve()
        resolved_route = (scenarios_dir / route_val).resolve()

        assert resolved_net.exists(), f"Referenced net file does not exist: {resolved_net}"
        assert resolved_route.exists(), f"Referenced route file does not exist: {resolved_route}"


def test_deterministic_route_generation(tmp_path):
    """Verify route generation is deterministic with fixed seed."""
    file1 = tmp_path / "seed42_a.rou.xml"
    file2 = tmp_path / "seed42_b.rou.xml"

    generate_routes(profile="normal", seed=42, duration=100, output_path=file1)
    generate_routes(profile="normal", seed=42, duration=100, output_path=file2)

    with open(file1, encoding="utf-8") as f1, open(file2, encoding="utf-8") as f2:
        assert f1.read() == f2.read(), "Generated route files with same seed must be byte-for-byte identical"


def test_headless_sumo_simulation():
    """Verify SUMO headless execution completes cleanly with zero errors."""
    cfg_path = Path("sumo/scenarios/corridor_normal.sumocfg")
    res = subprocess.run(
        ["sumo", "-c", str(cfg_path), "--end", "30", "--no-warnings"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert res.returncode == 0
    assert "Simulation ended at time: 30.00" in res.stdout


def test_fallback_plan_json_schema():
    """Verify backend/app/reliability/fallback_plan.json exists and defines a safe 6-phase plan."""
    plan_path = Path("backend/app/reliability/fallback_plan.json")
    assert plan_path.exists(), f"Missing fallback plan: {plan_path}"

    with open(plan_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["cycle_length_s"] == 60
    assert len(data["phases"]) == 6
    assert data["junctions"] == ["J1", "J2", "J3", "J4"]

    phase_names = [p["name"] for p in data["phases"]]
    assert "MAIN_GREEN" in phase_names
    assert "MAIN_YELLOW" in phase_names
    assert "ALL_RED_1" in phase_names
    assert "CROSS_GREEN" in phase_names
    assert "CROSS_YELLOW" in phase_names
    assert "ALL_RED_2" in phase_names
