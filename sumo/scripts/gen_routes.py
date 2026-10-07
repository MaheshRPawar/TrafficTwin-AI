#!/usr/bin/env python3
"""
TrafficTwin AI - Deterministic Route Generator (Module M1)

Generates reproducible SUMO route files (.rou.xml) across 4 profiles:
- normal: balanced multi-modal urban traffic
- rush: directional rush-hour surge with heavy queueing
- blocked_downstream: downstream bottleneck on J4_E5 causing spillback on J3_J4
- ambulance: background traffic with an emergency ambulance dispatched at t=50s

Usage:
  python sumo/scripts/gen_routes.py --profile normal --seed 42
  python sumo/scripts/gen_routes.py --profile rush --seed 42
  python sumo/scripts/gen_routes.py --profile blocked_downstream --seed 42
  python sumo/scripts/gen_routes.py --profile ambulance --seed 42
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path


def generate_routes(profile: str, seed: int = 42, duration: int = 360, output_path: Path | None = None) -> Path:
    rng = random.Random(seed)  # nosec B311

    if output_path is None:
        output_path = Path("sumo/routes") / f"corridor_{profile}.rou.xml"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">',
        '    <!-- Vehicle Type Definitions -->',
        '    <vType id="car" vClass="passenger" length="4.5" maxSpeed="13.89" accel="2.6" decel="4.5" sigma="0.5" color="0.7,0.7,0.7" />',
        '    <vType id="taxi" vClass="taxi" length="4.8" maxSpeed="13.89" accel="2.8" decel="4.5" sigma="0.5" color="1.0,0.8,0.0" />',
        '    <vType id="bus" vClass="bus" length="12.0" maxSpeed="11.11" accel="1.2" decel="3.5" sigma="0.5" color="0.2,0.6,1.0" />',
        '    <vType id="ambulance" vClass="emergency" guiShape="emergency" length="6.5" maxSpeed="16.67" accel="3.5" decel="5.0" sigma="0.2" color="1.0,0.0,0.0" />',
        '',
        '    <!-- Route Definitions -->',
        '    <route id="r_corridor_EB" edges="W0_J1 J1_J2 J2_J3 J3_J4 J4_E5" />',
        '    <route id="r_corridor_WB" edges="E5_J4 J4_J3 J3_J2 J2_J1 J1_W0" />',
        '    <route id="r_cross_J1_NS" edges="N1_J1 J1_S1" />',
        '    <route id="r_cross_J1_SN" edges="S1_J1 J1_N1" />',
        '    <route id="r_cross_J2_NS" edges="N2_J2 J2_S2" />',
        '    <route id="r_cross_J2_SN" edges="S2_J2 J2_N2" />',
        '    <route id="r_cross_J3_NS" edges="N3_J3 J3_S3" />',
        '    <route id="r_cross_J3_SN" edges="S3_J3 J3_N3" />',
        '    <route id="r_cross_J4_NS" edges="N4_J4 J4_S4" />',
        '    <route id="r_cross_J4_SN" edges="S4_J4 J4_N4" />',
        '',
        '    <!-- Vehicle Trips -->'
    ]

    def pick_vtype() -> str:
        r = rng.random()
        if r < 0.70:
            return "car"
        elif r < 0.85:
            return "taxi"
        else:
            return "bus"

    veh_count = 0

    # Traffic demand parameters per profile (vehicles per hour)
    if profile == "normal":
        rate_eb = 720   # Eastbound: 1 veh every ~5.0s
        rate_wb = 540   # Westbound: 1 veh every ~6.6s
        rate_cross = 180  # Each cross street: 1 veh every ~20s
    elif profile == "rush":
        rate_eb = 1600  # Directional surge Eastbound: 1 veh every ~2.25s
        rate_wb = 600
        rate_cross = 320
    elif profile == "blocked_downstream":
        rate_eb = 1400  # High Eastbound inflow
        rate_wb = 500
        rate_cross = 240
    elif profile == "ambulance":
        rate_eb = 900
        rate_wb = 540
        rate_cross = 240
    else:
        raise ValueError(f"Unknown profile: {profile}")

    prob_eb = rate_eb / 3600.0
    prob_wb = rate_wb / 3600.0
    prob_cross = rate_cross / 3600.0

    cross_routes = [
        "r_cross_J1_NS", "r_cross_J1_SN",
        "r_cross_J2_NS", "r_cross_J2_SN",
        "r_cross_J3_NS", "r_cross_J3_SN",
        "r_cross_J4_NS", "r_cross_J4_SN",
    ]

    vehicles: list[tuple[float, str]] = []

    # For blocked_downstream scenario, add stalled bottleneck vehicles on the exit edge J4_E5
    if profile == "blocked_downstream":
        v1 = (
            '    <vehicle id="incident_bottleneck_1" type="car" route="r_corridor_EB" depart="20.0" departLane="0" departSpeed="10.0">\n'
            '        <stop edge="J4_E5" lane="J4_E5_0" startPos="50.0" endPos="60.0" duration="280.0" />\n'
            '    </vehicle>'
        )
        vehicles.append((20.0, v1))

        v2 = (
            '    <vehicle id="incident_bottleneck_2" type="car" route="r_corridor_EB" depart="25.0" departLane="1" departSpeed="10.0">\n'
            '        <stop edge="J4_E5" lane="J4_E5_1" startPos="70.0" endPos="80.0" duration="280.0" />\n'
            '    </vehicle>'
        )
        vehicles.append((25.0, v2))

    # For ambulance scenario, inject emergency vehicle at t=50s
    if profile == "ambulance":
        v_amb = '    <vehicle id="emerg_1" type="ambulance" route="r_corridor_EB" depart="50.0" departLane="best" departSpeed="13.89" />'
        vehicles.append((50.0, v_amb))

    for t in range(1, duration):
        # Eastbound arrivals
        if rng.random() < prob_eb:
            veh_count += 1
            vtype = pick_vtype()
            vehicles.append((
                float(t),
                f'    <vehicle id="veh_eb_{veh_count}" type="{vtype}" route="r_corridor_EB" depart="{t:.1f}" departLane="best" departSpeed="max" />'
            ))

        # Westbound arrivals
        if rng.random() < prob_wb:
            veh_count += 1
            vtype = pick_vtype()
            vehicles.append((
                float(t),
                f'    <vehicle id="veh_wb_{veh_count}" type="{vtype}" route="r_corridor_WB" depart="{t:.1f}" departLane="best" departSpeed="max" />'
            ))

        # Cross street arrivals
        for cr in cross_routes:
            if rng.random() < prob_cross:
                veh_count += 1
                vtype = pick_vtype()
                vehicles.append((
                    float(t),
                    f'    <vehicle id="veh_cr_{veh_count}" type="{vtype}" route="{cr}" depart="{t:.1f}" departLane="best" departSpeed="max" />'
                ))

    # Sort all vehicles strictly by depart time to guarantee zero route-sort warnings in SUMO
    vehicles.sort(key=lambda x: x[0])
    for _, xml_str in vehicles:
        lines.append(xml_str)

    lines.append('</routes>')
    lines.append('')

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Generated {veh_count} vehicles for profile '{profile}' (seed={seed}) -> {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic routes for TrafficTwin SUMO corridor")
    parser.add_argument("--profile", choices=["normal", "rush", "blocked_downstream", "ambulance", "all"], default="normal")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--duration", type=int, default=360)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    profiles = ["normal", "rush", "blocked_downstream", "ambulance"] if args.profile == "all" else [args.profile]
    for p in profiles:
        out = Path(args.output) if args.output else None
        generate_routes(p, seed=args.seed, duration=args.duration, output_path=out)


if __name__ == "__main__":
    main()
