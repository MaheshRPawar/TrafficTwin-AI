#!/usr/bin/env python3
"""TrafficTwin AI — Spillback Controller Demonstration (Module M6).

Demonstrates the M3 -> M6 -> M5 -> TraCI control chain:
1. Upstream junction has an active queue demanding green extension.
2. Downstream corridor link is near capacity (critical occupancy).
3. M3 reactive controller proposes EXTEND_GREEN.
4. M6 spillback guard blocks the extension (SPILLBACK_BLOCK) to protect downstream capacity.
5. M5 safety firewall validates the safe clearance transition before actuation.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.guards.safety_firewall import validate_action
from experiments.reactive_controller import (
    NEXT_CLEARANCE_PHASE,
    decide_action,
)
from experiments.spillback_controller import (
    apply_spillback_guard,
    calculate_spillback_risk,
    load_spillback_config,
)


def run_demo() -> None:
    print("=" * 60)
    print(" TRAFFICTWIN AI - MODULE M6 SPILLBACK DEMONSTRATION")
    print("=" * 60)

    config = load_spillback_config()
    junction_id = "J3"
    downstream_edge = "J3_J4"
    current_phase = 0  # MAIN_GREEN
    green_duration = 15.0  # seconds elapsed (exceeds min_green 10s)
    queue_main = 12  # High upstream queue
    queue_cross = 2  # Low cross queue

    # Simulated actual conditions from blocked downstream link
    # Capacity = 53 vehicles (400m / 7.5m effective length)
    # 47 vehicles stopped on link -> occupancy = 0.887 (88.7%)
    downstream_occupancy = 0.887
    risk = calculate_spillback_risk(
        downstream_occupancy,
        warning_threshold=config["warning_threshold"],
        critical_threshold=config["critical_threshold"],
    )

    downstream_state = {
        "edge_id": downstream_edge,
        "occupancy": downstream_occupancy,
        "vehicle_count": 47,
        "capacity": 53,
        "risk": risk,
    }

    print(f"\n[Corridor State at {junction_id}]")
    print(f"  Current Phase:       {current_phase} (MAIN_GREEN)")
    print(f"  Elapsed Green:       {green_duration:.1f}s (min: {config['min_green_s']}s, max: {config['max_green_s']}s)")
    print(f"  Upstream Main Queue: {queue_main} vehicles")
    print(f"  Cross Street Queue:  {queue_cross} vehicles")
    print(f"  Downstream Link:     {downstream_edge}")
    print(f"  Downstream Capacity: {downstream_state['capacity']} vehicles")
    print(f"  Downstream Vehs:     {downstream_state['vehicle_count']} vehicles")
    print(f"  Downstream Occupancy:{downstream_occupancy * 100:.1f}%")
    print(f"  Spillback Risk:      {risk}")

    # Step 1: M3 Reactive Controller proposal
    m3_action, m3_reason = decide_action(
        current_phase=current_phase,
        green_duration=green_duration,
        queue_main=queue_main,
        queue_cross=queue_cross,
        min_green=config["min_green_s"],
        max_green=config["max_green_s"],
        extension_step=config["extension_step_s"],
        queue_threshold=config["queue_threshold"],
    )

    print("\n--- Step 1: M3 Reactive Controller Proposal ---")
    print(f"  M3 Proposed Action:  {m3_action}")
    print(f"  M3 Proposed Reason:  {m3_reason}")

    # Step 2: M6 Spillback Guard evaluation
    m6_action, m6_reason, signal_action = apply_spillback_guard(
        proposed_action=m3_action,
        proposed_reason=m3_reason,
        downstream_state=downstream_state,
        current_phase=current_phase,
        green_duration=green_duration,
        min_green=config["min_green_s"],
        config=config,
    )

    print("\n--- Step 2: M6 Spillback Controller Check ---")
    print(f"  Downstream State:    {risk} ({downstream_occupancy * 100:.1f}% >= {config['critical_threshold'] * 100:.0f}%)")
    print(f"  M6 Override Action:  {m6_action}")
    print(f"  M6 Decision Reason:  {m6_reason}")
    print(f"  M6 Target Signal:    {signal_action} (clearance transition requested)")

    # Step 3: M5 Safety Firewall validation
    firewall_action = {
        "junction_id": junction_id,
        "current_phase": current_phase,
        "requested_phase": NEXT_CLEARANCE_PHASE.get(current_phase),
        "action": signal_action,
        "timestamp": 120.0,
        "elapsed_green_s": green_duration,
        "extension_s": 0.0,
        "reason": m6_reason,
    }
    fw_result = validate_action(firewall_action, config)

    print("\n--- Step 3: M5 Safety Firewall Validation ---")
    print(f"  Firewall Target:     Phase {current_phase} -> Phase {firewall_action['requested_phase']}")
    print(f"  Firewall Allowed:    {fw_result['allowed']}")
    print(f"  Firewall Reason:     {fw_result['reason']}")

    # Step 4: TraCI Actuation Result
    print("\n--- Step 4: TraCI Signal Execution ---")
    if fw_result["allowed"]:
        print(f"  TraCI Command:       setPhase('{junction_id}', {firewall_action['requested_phase']})")
        print("  Outcome:             SAFE TRANSITION EXECUTED. Downstream bottleneck protected.")
    else:
        print("  Outcome:             FIREWALL REJECTED ACTION. Command blocked.")

    print("\n" + "=" * 60)
    print(" DEMONSTRATION COMPLETE: M3 -> M6 -> M5 -> TraCI VERIFIED")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
