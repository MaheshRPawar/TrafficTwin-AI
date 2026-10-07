#!/usr/bin/env python3
"""
TrafficTwin AI — Simulated GPS Event Generator (Module M4)

Extracts live vehicle state from SUMO through TraCI, converts it into
normalized GPS-like events, and writes them to a JSONL stream file.

Usage:
    python experiments/generate_gps_events.py --scenario normal
    python experiments/generate_gps_events.py --scenario rush
    python experiments/generate_gps_events.py --all
"""

import argparse
import json
import math
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import traci
import yaml

from backend.app.stream.gps_event import build_gps_event

SCENARIOS_DIR = Path("sumo/scenarios")
DEFAULT_OUTPUT_DIR = Path("data/output/gps")
PARAMS_PATH = Path("backend/config/params.yaml")

VALID_SCENARIOS = ["normal", "rush", "blocked_downstream", "ambulance"]


def load_telematics_interval(default: float = 2.0) -> float:
    """Read telematics_interval_s from params.yaml if available."""
    if not PARAMS_PATH.exists():
        return default
    try:
        with open(PARAMS_PATH, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data and "simulation" in data:
            return float(data["simulation"].get("telematics_interval_s", default))
    except (OSError, yaml.YAMLError, ValueError, KeyError):
        return default
    return default


def generate_scenario_events(
    scenario: str,
    output_dir: Path,
    interval_s: float = 2.0,
    max_duration_s: float = 360.0,
) -> Path:
    """Run SUMO for one scenario, observe vehicles, and write GPS events to JSONL."""
    cfg_path = SCENARIOS_DIR / f"corridor_{scenario}.sumocfg"
    if not cfg_path.exists():
        print(f"ERROR: Configuration not found: {cfg_path}")
        sys.exit(1)

    print(f"\n--- Generating GPS event stream: {scenario} (interval={interval_s}s) ---")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{scenario}.jsonl"

    # Start SUMO via TraCI
    sumo_cmd = ["sumo", "-c", str(cfg_path)]
    try:
        traci.start(sumo_cmd)
    except Exception as exc:
        print(f"ERROR: TraCI connection failed: {exc}")
        sys.exit(1)

    events_count = 0
    unique_vehicles = set()

    try:
        with open(out_file, "w", encoding="utf-8") as f:
            while traci.simulation.getMinExpectedNumber() > 0:
                sim_time = traci.simulation.getTime()
                traci.simulationStep()

                if sim_time > max_duration_s:
                    break

                # Sample telemetry at configured interval
                remainder = sim_time % interval_s
                if not (math.isclose(remainder, 0.0, abs_tol=1e-4) or math.isclose(remainder, interval_s, abs_tol=1e-4)):
                    continue

                # Read all active vehicles in current step
                veh_ids = traci.vehicle.getIDList()
                for vid in veh_ids:
                    pos = traci.vehicle.getPosition(vid)
                    speed = traci.vehicle.getSpeed(vid)
                    heading = traci.vehicle.getAngle(vid)
                    lane_id = traci.vehicle.getLaneID(vid)
                    road_id = traci.vehicle.getRoadID(vid)
                    vtype = traci.vehicle.getTypeID(vid)

                    # Build normalized event
                    event = build_gps_event(
                        vehicle_id=vid,
                        vehicle_type=vtype,
                        timestamp=sim_time,
                        x=pos[0],
                        y=pos[1],
                        speed_mps=speed,
                        heading=heading,
                        lane_id=lane_id,
                        road_id=road_id,
                    )

                    # Write single JSON line
                    f.write(json.dumps(event) + "\n")
                    events_count += 1
                    unique_vehicles.add(vid)
    finally:
        # Safely close TraCI
        traci.close()

    print(f"  Stream written to: {out_file}")
    print(f"  Total events: {events_count}, unique vehicles: {len(unique_vehicles)}")

    return out_file


def main() -> None:
    default_interval = load_telematics_interval(2.0)

    parser = argparse.ArgumentParser(description="Generate simulated GPS event stream from SUMO")
    parser.add_argument(
        "--scenario",
        choices=VALID_SCENARIOS,
        help="Scenario to run",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate streams for all scenarios",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to save JSONL streams",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=default_interval,
        help=f"Telemetry interval in seconds (default: {default_interval})",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=360.0,
        help="Maximum simulation duration in seconds (default: 360.0)",
    )
    args = parser.parse_args()

    if not args.all and not args.scenario:
        parser.print_help()
        sys.exit(1)

    scenarios = VALID_SCENARIOS if args.all else [args.scenario]
    for sc in scenarios:
        generate_scenario_events(
            scenario=sc,
            output_dir=args.output_dir,
            interval_s=args.interval,
            max_duration_s=args.duration,
        )


if __name__ == "__main__":
    main()
