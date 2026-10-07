"""
Calculate baseline metrics from parsed SUMO output.

Definitions used:
  average_waiting_time   = sum(waitingTime per trip) / completed trips
  p95_waiting_time       = 95th percentile of per-trip waitingTime values
  average_travel_time    = sum(duration per trip) / completed trips
  throughput             = number of trips that completed their route
  mean_queue_length      = mean queueing_length across all recorded queue snapshots
  maximum_queue_length   = max queueing_length across all recorded queue snapshots
  emergency_delay        = waiting_time of the vehicle with id 'emerg_1' (ambulance scenario only)
"""

import statistics
from pathlib import Path


def calc_metrics(
    trips: list[dict],
    queue_records: list[dict],
    scenario: str,
    controller: str = "fixed",
) -> dict:
    """Compute metrics from parsed trip and queue data.

    Args:
        trips:         output of tripinfo_parser.parse_tripinfo()
        queue_records: output of queue_parser.parse_queue()
        scenario:      scenario name string (used for labeling and emergency lookup)
        controller:    controller name string (fixed, reactive, traffictwin)

    Returns:
        dict with metric name -> value (float or int), rounded to 2 decimal places.
    """
    # Throughput is the count of completed trips
    throughput = len(trips)

    # Waiting time metrics
    if trips:
        waiting_times = [t["waiting_time"] for t in trips]
        avg_wait = statistics.mean(waiting_times)
        p95_wait = percentile(waiting_times, 95)
    else:
        avg_wait = 0.0
        p95_wait = 0.0

    # Travel time metrics
    if trips:
        travel_times = [t["travel_time"] for t in trips]
        avg_travel = statistics.mean(travel_times)
    else:
        avg_travel = 0.0

    # Queue length metrics
    if queue_records:
        all_q_lengths = [r["queueing_length"] for r in queue_records]
        mean_queue = statistics.mean(all_q_lengths)
        max_queue = max(all_q_lengths)
    else:
        mean_queue = 0.0
        max_queue = 0.0

    # Emergency delay — only meaningful in ambulance scenario
    emergency_delay = None
    if scenario == "ambulance":
        for trip in trips:
            if trip["id"] == "emerg_1":
                emergency_delay = trip["waiting_time"]
                break

    result = {
        "scenario": scenario,
        "controller": controller,
        "throughput": throughput,
        "average_waiting_time": round(avg_wait, 2),
        "p95_waiting_time": round(p95_wait, 2),
        "average_travel_time": round(avg_travel, 2),
        "mean_queue_length": round(mean_queue, 2),
        "maximum_queue_length": round(max_queue, 2),
    }

    if emergency_delay is not None:
        result["emergency_delay"] = round(emergency_delay, 2)

    return result


def percentile(values: list[float], pct: int) -> float:
    """Return the pct-th percentile of a list of floats.

    Uses nearest-rank method. Requires at least one value.
    """
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    # Nearest rank: rank = ceil(pct/100 * n), 1-indexed
    rank = max(1, int(round(pct / 100.0 * n + 0.5)))
    rank = min(rank, n)
    return sorted_vals[rank - 1]


def save_summary_csv(metrics: dict, output_path: Path) -> None:
    """Write a single-row summary CSV with column headers."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "scenario", "controller",
        "throughput", "average_waiting_time", "p95_waiting_time",
        "average_travel_time", "mean_queue_length", "maximum_queue_length",
    ]
    # Include emergency_delay column if present
    if "emergency_delay" in metrics:
        columns.append("emergency_delay")

    header = ",".join(columns)
    row = ",".join(str(metrics.get(c, "")) for c in columns)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + "\n")
        f.write(row + "\n")


def save_trips_csv(trips: list[dict], output_path: Path) -> None:
    """Write per-vehicle trip records to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["id", "vtype", "depart", "arrival", "duration", "waiting_time", "route_length"]
    header = ",".join(columns)
    rows = [",".join(str(t.get(c, "")) for c in columns) for t in trips]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + "\n")
        f.write("\n".join(rows) + "\n")


def save_queues_csv(queue_records: list[dict], output_path: Path) -> None:
    """Write per-timestep queue records to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = ["timestep", "lane_id", "queueing_length", "queueing_time"]
    header = ",".join(columns)
    rows = [",".join(str(r.get(c, "")) for c in columns) for r in queue_records]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + "\n")
        f.write("\n".join(rows) + "\n")
