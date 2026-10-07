"""TrafficTwin AI — Safety Firewall Demonstration (Module M5).

Demonstrates the 5 required safety cases:
  Case 1: Valid green action -> PASS
  Case 2: Transition before minimum green -> REJECT
  Case 3: Illegal direct green-to-green transition -> REJECT
  Case 4: Green extension beyond maximum -> REJECT
  Case 5: Valid transition through required clearance -> PASS
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.guards.safety_firewall import (
    load_firewall_config,
    log_firewall_decision,
    validate_action,
)


def run_safety_demo() -> list[dict]:
    """Execute the safety validation demonstration cases."""
    config = load_firewall_config()
    results = []

    print("==================================================")
    print("TRAFFICTWIN AI -- SAFETY FIREWALL DEMO (M5)")
    print("==================================================")
    print(f"Config: min_green={config['min_green_s']}s, max_green={config['max_green_s']}s, "
          f"yellow={config['yellow_s']}s, all_red={config['all_red_s']}s\n")

    cases = [
        {
            "name": "CASE 1: Valid green action",
            "action": {
                "junction_id": "J1",
                "current_phase": 0,
                "requested_phase": 0,
                "action": "KEEP_GREEN",
                "timestamp": 15.0,
                "elapsed_green_s": 15.0,
                "reason": "main_arterial_steady_flow",
            },
            "expected_allowed": True,
        },
        {
            "name": "CASE 2: Transition before minimum green",
            "action": {
                "junction_id": "J2",
                "current_phase": 0,
                "requested_phase": 1,
                "action": "START_TRANSITION",
                "timestamp": 6.0,
                "elapsed_green_s": 6.0,
                "reason": "cross_queue_spike",
            },
            "expected_allowed": False,
        },
        {
            "name": "CASE 3: Illegal direct green-to-green transition",
            "action": {
                "junction_id": "J3",
                "current_phase": 0,
                "requested_phase": 3,
                "action": "START_TRANSITION",
                "timestamp": 25.0,
                "elapsed_green_s": 25.0,
                "reason": "attempt_skip_clearance",
            },
            "expected_allowed": False,
        },
        {
            "name": "CASE 4: Green extension beyond maximum",
            "action": {
                "junction_id": "J4",
                "current_phase": 0,
                "requested_phase": 0,
                "action": "EXTEND_GREEN",
                "timestamp": 43.0,
                "elapsed_green_s": 42.0,
                "extension_s": 5.0,
                "reason": "heavy_queue_extension",
            },
            "expected_allowed": False,
        },
        {
            "name": "CASE 5: Valid transition through required clearance",
            "action": {
                "junction_id": "J2",
                "current_phase": 0,
                "requested_phase": 1,
                "action": "START_TRANSITION",
                "timestamp": 20.0,
                "elapsed_green_s": 20.0,
                "reason": "cross_demand_satisfied_min_green",
            },
            "expected_allowed": True,
        },
    ]

    log_path = Path("data/output/safety/demo_firewall_decisions.csv")
    if log_path.exists():
        log_path.unlink()

    for item in cases:
        case_name = item["name"]
        act = item["action"]
        res = validate_action(act, config=config)
        results.append(res)

        status_tag = "PASS" if res["allowed"] else "REJECT"
        print(f"--- {case_name} ---")
        print(f"  Proposed: junction={act['junction_id']} phase={act['current_phase']} "
              f"action={act['action']} elapsed={act['elapsed_green_s']}s")
        print(f"  Result:   {status_tag} (reason: '{res['reason']}')")
        print(f"  Expected: {'PASS' if item['expected_allowed'] else 'REJECT'}")

        # Record audit log
        log_record = {
            "timestamp": act["timestamp"],
            "junction_id": act["junction_id"],
            "current_phase": act["current_phase"],
            "requested_phase": res.get("requested_phase"),
            "action": act["action"],
            "allowed": res["allowed"],
            "reason": res["reason"],
        }
        log_firewall_decision(log_record, output_path=log_path)
        print()

    print(f"Audit log written to: {log_path}")
    print("==================================================")
    return results


if __name__ == "__main__":
    run_safety_demo()
