"""
M2 Acceptance Gate Test Suite — Fixed-Time Baseline and Metrics
"""

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

from experiments.metrics.calculate_metrics import (
    calc_metrics,
    percentile,
    save_queues_csv,
    save_summary_csv,
    save_trips_csv,
)
from experiments.metrics.queue_parser import parse_queue
from experiments.metrics.tripinfo_parser import parse_tripinfo

# ── Tripinfo Parser ──────────────────────────────────────────────────────────

def _make_tripinfo_xml(tmp_path: Path, trips: list[dict]) -> Path:
    """Write a minimal tripinfo XML file from a list of trip dicts."""
    root = ET.Element("tripinfos")
    for t in trips:
        ET.SubElement(root, "tripinfo", {
            "id": t["id"],
            "depart": str(t["depart"]),
            "arrival": str(t.get("arrival", t["depart"] + t["duration"])),
            "duration": str(t["duration"]),
            "waitingTime": str(t["waitingTime"]),
            "routeLength": str(t.get("routeLength", 200.0)),
            "vType": t.get("vType", "car"),
        })
    path = tmp_path / "tripinfo_test.xml"
    ET.ElementTree(root).write(str(path), encoding="unicode", xml_declaration=True)
    return path


def test_tripinfo_parser_returns_completed_trips(tmp_path):
    """Parser only returns trips that have an arrival attribute."""
    sample = [
        {"id": "v1", "depart": 1.0, "duration": 30.0, "waitingTime": 10.0, "arrival": 31.0},
        {"id": "v2", "depart": 2.0, "duration": 50.0, "waitingTime": 5.0, "arrival": 52.0},
    ]
    path = _make_tripinfo_xml(tmp_path, sample)
    trips = parse_tripinfo(path)
    assert len(trips) == 2
    ids = [t["id"] for t in trips]
    assert "v1" in ids
    assert "v2" in ids


def test_tripinfo_parser_extracts_waiting_time(tmp_path):
    sample = [{"id": "v1", "depart": 0.0, "duration": 60.0, "waitingTime": 15.0, "arrival": 60.0}]
    path = _make_tripinfo_xml(tmp_path, sample)
    trips = parse_tripinfo(path)
    assert trips[0]["waiting_time"] == 15.0


# ── Queue Parser ─────────────────────────────────────────────────────────────

def _make_queue_xml(tmp_path: Path, timestep_lanes: list[tuple[float, list[dict]]]) -> Path:
    """Write a minimal queue XML file."""
    root = ET.Element("queue-export")
    for ts, lanes in timestep_lanes:
        data_elem = ET.SubElement(root, "data", {"timestep": str(ts)})
        lanes_elem = ET.SubElement(data_elem, "lanes")
        for lane in lanes:
            ET.SubElement(lanes_elem, "lane", {
                "id": lane["id"],
                "queueing_length": str(lane["queueing_length"]),
                "queueing_time": str(lane.get("queueing_time", 0.0)),
            })
    path = tmp_path / "queue_test.xml"
    ET.ElementTree(root).write(str(path), encoding="unicode", xml_declaration=True)
    return path


def test_queue_parser_returns_nonzero_queues(tmp_path):
    """Parser must only return lanes where queueing_length > 0."""
    data = [
        (1.0, [{"id": "lane_A", "queueing_length": 5.0}]),
        (2.0, [{"id": "lane_B", "queueing_length": 0.0}]),
        (3.0, [{"id": "lane_A", "queueing_length": 12.3}]),
    ]
    path = _make_queue_xml(tmp_path, data)
    records = parse_queue(path)
    assert len(records) == 2
    lengths = [r["queueing_length"] for r in records]
    assert 5.0 in lengths
    assert 12.3 in lengths


# ── Metric Calculation ───────────────────────────────────────────────────────

def test_metric_calculation_basic():
    trips = [
        {"id": "v1", "waiting_time": 10.0, "travel_time": 50.0},
        {"id": "v2", "waiting_time": 20.0, "travel_time": 80.0},
        {"id": "v3", "waiting_time": 30.0, "travel_time": 60.0},
    ]
    queues = [
        {"queueing_length": 5.0, "queueing_time": 1.0},
        {"queueing_length": 15.0, "queueing_time": 2.0},
    ]
    m = calc_metrics(trips, queues, "normal")
    assert m["throughput"] == 3
    assert m["average_waiting_time"] == 20.0
    assert m["average_travel_time"] == round((50 + 80 + 60) / 3, 2)
    assert m["mean_queue_length"] == 10.0
    assert m["maximum_queue_length"] == 15.0
    assert m["scenario"] == "normal"
    assert m["controller"] == "fixed"


def test_metric_calculation_empty_trips():
    m = calc_metrics([], [], "normal")
    assert m["throughput"] == 0
    assert m["average_waiting_time"] == 0.0
    assert m["mean_queue_length"] == 0.0


def test_emergency_delay_only_in_ambulance_scenario():
    trips = [{"id": "emerg_1", "waiting_time": 18.0, "travel_time": 90.0}]
    m = calc_metrics(trips, [], "ambulance")
    assert "emergency_delay" in m
    assert m["emergency_delay"] == 18.0

    m2 = calc_metrics(trips, [], "normal")
    assert "emergency_delay" not in m2


# ── Percentile ───────────────────────────────────────────────────────────────

def test_percentile_p95():
    values = list(range(1, 101))  # 1..100
    p95 = percentile(values, 95)
    # Nearest-rank method: rank = ceil(0.95 * 100 + 0.5) = 96, value = 96
    assert p95 == 96


def test_percentile_single_value():
    assert percentile([42.0], 95) == 42.0


def test_percentile_empty():
    assert percentile([], 95) == 0.0


# ── CSV Export ───────────────────────────────────────────────────────────────

def test_summary_csv_export(tmp_path):
    metrics = {
        "scenario": "normal",
        "controller": "fixed",
        "throughput": 194,
        "average_waiting_time": 20.04,
        "p95_waiting_time": 46.0,
        "average_travel_time": 78.91,
        "mean_queue_length": 13.73,
        "maximum_queue_length": 48.54,
    }
    out_path = tmp_path / "test_summary.csv"
    save_summary_csv(metrics, out_path)
    assert out_path.exists()

    with open(out_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["scenario"] == "normal"
    assert rows[0]["throughput"] == "194"
    assert rows[0]["average_waiting_time"] == "20.04"


def test_trips_csv_export(tmp_path):
    trips = [
        {"id": "v1", "vtype": "car", "depart": 1.0, "arrival": 61.0,
         "duration": 60.0, "waiting_time": 10.0, "route_length": 800.0},
    ]
    out_path = tmp_path / "test_trips.csv"
    save_trips_csv(trips, out_path)
    assert out_path.exists()
    with open(out_path, encoding="utf-8") as f:
        content = f.read()
    assert "v1" in content
    assert "car" in content


def test_queues_csv_export(tmp_path):
    records = [
        {"timestep": 5.0, "lane_id": "J1_J2_0", "queueing_length": 7.5, "queueing_time": 2.0},
    ]
    out_path = tmp_path / "test_queues.csv"
    save_queues_csv(records, out_path)
    assert out_path.exists()
    with open(out_path, encoding="utf-8") as f:
        content = f.read()
    assert "J1_J2_0" in content
    assert "7.5" in content


# ── M2 Output Existence ──────────────────────────────────────────────────────

def test_m2_csv_outputs_exist():
    """Verify M2 CSV results exist for both required scenarios."""
    results_dir = Path("data/output/metrics")
    for scenario in ["normal", "rush"]:
        for kind in ["summary", "trips", "queues"]:
            path = results_dir / f"fixed_{scenario}_{kind}.csv"
            assert path.exists(), f"Missing M2 output: {path}"


def test_m2_summary_csv_has_real_values():
    """Verify summary CSVs contain non-zero throughput from actual SUMO runs."""
    results_dir = Path("data/output/metrics")
    for scenario in ["normal", "rush"]:
        path = results_dir / f"fixed_{scenario}_summary.csv"
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert int(rows[0]["throughput"]) > 0, f"Zero throughput in {path}"
        assert float(rows[0]["average_waiting_time"]) > 0.0


def test_m2_chart_exists():
    """Verify the baseline chart was generated."""
    chart = Path("data/demo_assets/fixed_baseline_waiting_time.png")
    assert chart.exists(), f"Baseline chart missing: {chart}"
