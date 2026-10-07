"""TrafficTwin AI — Signal Safety Firewall (Module M5).

Validates proposed signal-control actions against safety constraints:
junction validity, phase numbering, legal progression, minimum green,
maximum green, clearance intervals, and conflicting movement protection.
"""

import csv
from pathlib import Path

import yaml

# Controlled junctions in the 4-junction corridor
VALID_JUNCTIONS = ["J1", "J2", "J3", "J4"]

# Recognized signal control actions
VALID_ACTIONS = ["KEEP_GREEN", "EXTEND_GREEN", "START_TRANSITION", "HOLD"]

# Signal phases in 6-phase SUMO corridor program
# 0: MAIN_GREEN   (30s default)
# 1: MAIN_YELLOW  (3s clearance)
# 2: ALL_RED_1    (2s clearance)
# 3: CROSS_GREEN  (20s default)
# 4: CROSS_YELLOW (3s clearance)
# 5: ALL_RED_2    (2s clearance)
PHASE_NAMES = {
    0: "MAIN_GREEN",
    1: "MAIN_YELLOW",
    2: "ALL_RED_1",
    3: "CROSS_GREEN",
    4: "CROSS_YELLOW",
    5: "ALL_RED_2",
}

GREEN_PHASES = {0, 3}
CLEARANCE_PHASES = {1, 2, 4, 5}
YELLOW_PHASES = {1, 4}
ALL_RED_PHASES = {2, 5}

# Strictly legal forward phase transitions
LEGAL_NEXT_PHASE = {
    0: 1,  # MAIN_GREEN -> MAIN_YELLOW
    1: 2,  # MAIN_YELLOW -> ALL_RED_1
    2: 3,  # ALL_RED_1 -> CROSS_GREEN
    3: 4,  # CROSS_GREEN -> CROSS_YELLOW
    4: 5,  # CROSS_YELLOW -> ALL_RED_2
    5: 0,  # ALL_RED_2 -> MAIN_GREEN
}

# Conflicting green movement pairs
CONFLICTING_GREENS = {
    (0, 3),
    (3, 0),
}


def load_firewall_config(config_path=None) -> dict:
    """Load safety firewall parameters from params.yaml."""
    if config_path is None:
        config_path = Path("backend/config/params.yaml")
    else:
        config_path = Path(config_path)

    defaults = {
        "min_green_s": 10.0,
        "max_green_s": 45.0,
        "yellow_s": 3.0,
        "all_red_s": 2.0,
    }

    if not config_path.exists():
        return defaults

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data and "safety_firewall" in data:
            cfg = data["safety_firewall"]
            return {
                "min_green_s": float(cfg.get("min_green_s", 10.0)),
                "max_green_s": float(cfg.get("max_green_s", 45.0)),
                "yellow_s": float(cfg.get("yellow_s", 3.0)),
                "all_red_s": float(cfg.get("all_red_s", 2.0)),
            }
    except (OSError, yaml.YAMLError, ValueError, KeyError):
        return defaults

    return defaults


def is_conflicting_phase(phase_a: int, phase_b: int) -> bool:
    """Return True if phase_a and phase_b are conflicting signal movements."""
    return (phase_a, phase_b) in CONFLICTING_GREENS


def is_legal_transition(current_phase: int, requested_phase: int) -> bool:
    """Check if requested_phase directly succeeds current_phase in the cycle."""
    return LEGAL_NEXT_PHASE.get(current_phase) == requested_phase


def validate_action(action: dict, config: dict | None = None) -> dict:
    """Validate a proposed signal action against safety rules.

    Returns a dict with 'allowed' (bool) and 'reason' (str).
    """
    if config is None:
        config = load_firewall_config()

    min_green_s = float(config.get("min_green_s", 10.0))
    max_green_s = float(config.get("max_green_s", 45.0))

    # Check action dictionary structure
    if not isinstance(action, dict):
        return {
            "allowed": False,
            "reason": "malformed_action",
            "junction_id": None,
            "current_phase": None,
            "requested_phase": None,
        }

    junction_id = action.get("junction_id")
    current_phase = action.get("current_phase")
    requested_phase = action.get("requested_phase")
    action_name = action.get("action")
    elapsed_green_s = float(action.get("elapsed_green_s", 0.0) or 0.0)
    extension_s = float(action.get("extension_s", 0.0) or 0.0)

    # 1. Junction validation
    if junction_id not in VALID_JUNCTIONS:
        return {
            "allowed": False,
            "reason": "invalid_junction",
            "junction_id": junction_id,
            "current_phase": current_phase,
            "requested_phase": requested_phase,
        }

    # 2. Phase number validation
    if not isinstance(current_phase, int) or current_phase not in PHASE_NAMES:
        return {
            "allowed": False,
            "reason": "invalid_phase",
            "junction_id": junction_id,
            "current_phase": current_phase,
            "requested_phase": requested_phase,
        }

    if requested_phase is not None:
        if not isinstance(requested_phase, int) or requested_phase not in PHASE_NAMES:
            return {
                "allowed": False,
                "reason": "invalid_phase",
                "junction_id": junction_id,
                "current_phase": current_phase,
                "requested_phase": requested_phase,
            }

    # 3. Action type validation
    if action_name not in VALID_ACTIONS:
        return {
            "allowed": False,
            "reason": "invalid_action",
            "junction_id": junction_id,
            "current_phase": current_phase,
            "requested_phase": requested_phase,
        }

    # 4. Clearance phase restrictions
    if current_phase in CLEARANCE_PHASES:
        if action_name in ("EXTEND_GREEN", "KEEP_GREEN"):
            return {
                "allowed": False,
                "reason": "action_not_valid_for_clearance_phase",
                "junction_id": junction_id,
                "current_phase": current_phase,
                "requested_phase": requested_phase,
            }

    # 5. Resolve target phase for transition
    effective_target = requested_phase
    if action_name == "START_TRANSITION" and effective_target is None:
        effective_target = LEGAL_NEXT_PHASE.get(current_phase)

    # 6. Phase transition and clearance sequence checks
    if effective_target is not None and effective_target != current_phase:
        # Check direct conflicting green transition
        if (current_phase, effective_target) in CONFLICTING_GREENS:
            return {
                "allowed": False,
                "reason": "conflicting_phase",
                "junction_id": junction_id,
                "current_phase": current_phase,
                "requested_phase": effective_target,
            }

        # Check yellow clearance bypass (green directly to all-red)
        if (current_phase == 0 and effective_target == 2) or (current_phase == 3 and effective_target == 5):
            return {
                "allowed": False,
                "reason": "yellow_clearance_required",
                "junction_id": junction_id,
                "current_phase": current_phase,
                "requested_phase": effective_target,
            }

        # Check all-red clearance bypass (yellow directly to green)
        if (current_phase == 1 and effective_target == 3) or (current_phase == 4 and effective_target == 0):
            return {
                "allowed": False,
                "reason": "all_red_clearance_required",
                "junction_id": junction_id,
                "current_phase": current_phase,
                "requested_phase": effective_target,
            }

        # Check general legal sequence progression
        if effective_target != LEGAL_NEXT_PHASE.get(current_phase):
            return {
                "allowed": False,
                "reason": "illegal_phase_transition",
                "junction_id": junction_id,
                "current_phase": current_phase,
                "requested_phase": effective_target,
            }

    # 7. Minimum green validation
    if current_phase in GREEN_PHASES:
        if action_name == "START_TRANSITION" or (effective_target is not None and effective_target != current_phase):
            if elapsed_green_s < min_green_s:
                return {
                    "allowed": False,
                    "reason": "minimum_green_not_reached",
                    "junction_id": junction_id,
                    "current_phase": current_phase,
                    "requested_phase": effective_target,
                }

    # 8. Maximum green validation
    if current_phase in GREEN_PHASES:
        if action_name == "EXTEND_GREEN":
            if elapsed_green_s >= max_green_s or (elapsed_green_s + extension_s) > max_green_s:
                return {
                    "allowed": False,
                    "reason": "maximum_green_exceeded",
                    "junction_id": junction_id,
                    "current_phase": current_phase,
                    "requested_phase": effective_target,
                }
        elif action_name == "KEEP_GREEN":
            if elapsed_green_s > max_green_s:
                return {
                    "allowed": False,
                    "reason": "maximum_green_exceeded",
                    "junction_id": junction_id,
                    "current_phase": current_phase,
                    "requested_phase": effective_target,
                }

    # 9. All safety checks passed
    if action_name == "START_TRANSITION" or (effective_target is not None and effective_target != current_phase):
        decision_reason = "valid_transition"
    else:
        decision_reason = "valid_action"

    return {
        "allowed": True,
        "reason": decision_reason,
        "junction_id": junction_id,
        "current_phase": current_phase,
        "requested_phase": effective_target if effective_target is not None else current_phase,
    }


def log_firewall_decision(record: dict, output_path=None) -> None:
    """Append a firewall audit record to CSV log file."""
    if output_path is None:
        output_path = Path("data/output/safety/firewall_decisions.csv")
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = output_path.exists() and output_path.stat().st_size > 0

    fields = [
        "timestamp",
        "junction_id",
        "current_phase",
        "requested_phase",
        "action",
        "allowed",
        "reason",
    ]

    with open(output_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": record.get("timestamp", 0.0),
            "junction_id": record.get("junction_id", ""),
            "current_phase": record.get("current_phase", ""),
            "requested_phase": record.get("requested_phase", ""),
            "action": record.get("action", ""),
            "allowed": record.get("allowed", False),
            "reason": record.get("reason", ""),
        })
