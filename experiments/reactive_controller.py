"""TrafficTwin AI — Safe Queue-Reactive Traffic Signal Controller (Module M3).

Provides queue measurement, phase monitoring, bounded green extension,
and safe phase transitions via TraCI.
"""

from pathlib import Path

import yaml

from backend.app.guards.safety_firewall import validate_action

# Phase mapping for 6-phase program
PHASE_NAMES = {
    0: "MAIN_GREEN",
    1: "MAIN_YELLOW",
    2: "ALL_RED_1",
    3: "CROSS_GREEN",
    4: "CROSS_YELLOW",
    5: "ALL_RED_2",
}

# Next clearance phase when green ends
NEXT_CLEARANCE_PHASE = {
    0: 1,  # MAIN_GREEN -> MAIN_YELLOW
    3: 4,  # CROSS_GREEN -> CROSS_YELLOW
}

# Controlled incoming lanes per junction
INCOMING_LANES = {
    "J1": {
        "main": ["W0_J1_0", "W0_J1_1", "J2_J1_0", "J2_J1_1"],
        "cross": ["N1_J1_0", "S1_J1_0"],
    },
    "J2": {
        "main": ["J1_J2_0", "J1_J2_1", "J3_J2_0", "J3_J2_1"],
        "cross": ["N2_J2_0", "S2_J2_0"],
    },
    "J3": {
        "main": ["J2_J3_0", "J2_J3_1", "J4_J3_0", "J4_J3_1"],
        "cross": ["N3_J3_0", "S3_J3_0"],
    },
    "J4": {
        "main": ["J3_J4_0", "J3_J4_1", "E5_J4_0", "E5_J4_1"],
        "cross": ["N4_J4_0", "S4_J4_0"],
    },
}


def load_controller_config(config_path=None) -> dict:
    """Load reactive controller parameters from params.yaml."""
    if config_path is None:
        config_path = Path("backend/config/params.yaml")
    else:
        config_path = Path(config_path)

    defaults = {
        "min_green_s": 10.0,
        "max_green_s": 40.0,
        "extension_step_s": 5.0,
        "queue_threshold": 3,
        "yellow_s": 3.0,
        "all_red_s": 2.0,
    }

    if not config_path.exists():
        return defaults

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data and "reactive_controller" in data:
        cfg = data["reactive_controller"]
        return {
            "min_green_s": float(cfg.get("min_green_s", 10.0)),
            "max_green_s": float(cfg.get("max_green_s", 40.0)),
            "extension_step_s": float(cfg.get("extension_step_s", 5.0)),
            "queue_threshold": int(cfg.get("queue_threshold", 3)),
            "yellow_s": float(cfg.get("yellow_s", 3.0)),
            "all_red_s": float(cfg.get("all_red_s", 2.0)),
        }

    return defaults


def get_incoming_queues(traci_client, junction_id: str) -> tuple[int, int]:
    """Read stopped vehicle queues for main and cross approaches of a junction."""
    lanes = INCOMING_LANES.get(junction_id)
    if not lanes:
        raise ValueError(f"Unknown junction ID: {junction_id}")

    # Read queue lengths from TraCI
    q_main = sum(traci_client.lane.getLastStepHaltingNumber(lane) for lane in lanes["main"])
    q_cross = sum(traci_client.lane.getLastStepHaltingNumber(lane) for lane in lanes["cross"])
    return q_main, q_cross


def decide_action(
    current_phase: int,
    green_duration: float,
    queue_main: int,
    queue_cross: int,
    min_green: float = 10.0,
    max_green: float = 40.0,
    extension_step: float = 5.0,
    queue_threshold: int = 3,
) -> tuple[str, str]:
    """Decide controller action based on current phase, green time, and queues."""
    # Check clearance phase
    if current_phase not in (0, 3):
        return "HOLD", "clearance phase active"

    # Identify current approach
    if current_phase == 0:
        q_cur, q_opp = queue_main, queue_cross
        cur_name, opp_name = "main", "cross"
    else:
        q_cur, q_opp = queue_cross, queue_main
        cur_name, opp_name = "cross", "main"

    # Check minimum green
    if green_duration < min_green:
        return "KEEP_GREEN", f"minimum green not satisfied ({green_duration:.1f}s < {min_green:.1f}s)"

    # Check maximum green
    if green_duration >= max_green:
        return "START_TRANSITION", f"maximum green reached ({green_duration:.1f}s >= {max_green:.1f}s)"

    # Check opposing approach demand
    if q_opp > q_cur and q_opp >= queue_threshold:
        return "START_TRANSITION", f"{opp_name} queue ({q_opp}) exceeds {cur_name} queue ({q_cur})"

    # Check current approach demand for bounded extension
    if q_cur >= queue_threshold:
        return "EXTEND_GREEN", f"high {cur_name} queue ({q_cur}), extending green"

    # Check empty current queue with waiting opposing traffic
    if q_cur == 0 and q_opp > 0:
        return "START_TRANSITION", f"{cur_name} queue empty and {opp_name} queue waiting ({q_opp})"

    # If cross street has no demand, return to main arterial
    if current_phase == 3 and q_cur == 0:
        return "START_TRANSITION", "cross street empty, returning to main arterial"

    # Keep green if demand is balanced or low
    return "KEEP_GREEN", f"{cur_name} demand below threshold"


def init_junction_states(junction_ids: list[str], min_green: float) -> dict:
    """Initialize tracking state for all controlled junctions."""
    states = {}
    for jid in junction_ids:
        states[jid] = {
            "last_phase": 0,
            "phase_start": 0.0,
            "allocated_green": min_green,
        }
    return states


def step_junction(
    traci_client,
    junction_id: str,
    sim_time: float,
    state: dict,
    config: dict,
) -> dict:
    """Execute one simulation step for a single junction and return a decision log record."""
    # Read current phase
    cur_phase = traci_client.trafficlight.getPhase(junction_id)

    # Detect phase transition
    if cur_phase != state["last_phase"]:
        state["last_phase"] = cur_phase
        state["phase_start"] = sim_time
        if cur_phase in (0, 3):
            state["allocated_green"] = config["min_green_s"]
            traci_client.trafficlight.setPhaseDuration(junction_id, config["max_green_s"])

    # Read current queues
    q_main, q_cross = get_incoming_queues(traci_client, junction_id)
    phase_name = PHASE_NAMES.get(cur_phase, str(cur_phase))

    # Handle clearance phases
    if cur_phase not in (0, 3):
        return {
            "timestamp": sim_time,
            "junction_id": junction_id,
            "current_phase": phase_name,
            "queue_main": q_main,
            "queue_cross": q_cross,
            "action": "HOLD",
            "reason": "clearance phase active",
        }

    # Green phase decision
    green_time = sim_time - state["phase_start"]
    action, reason = decide_action(
        current_phase=cur_phase,
        green_duration=green_time,
        queue_main=q_main,
        queue_cross=q_cross,
        min_green=config["min_green_s"],
        max_green=config["max_green_s"],
        extension_step=config["extension_step_s"],
        queue_threshold=config["queue_threshold"],
    )

    # Validate proposed action through M5 Safety Firewall before execution
    proposed_action = {
        "junction_id": junction_id,
        "current_phase": cur_phase,
        "requested_phase": NEXT_CLEARANCE_PHASE.get(cur_phase) if action == "START_TRANSITION" else cur_phase,
        "action": action,
        "timestamp": sim_time,
        "elapsed_green_s": green_time,
        "extension_s": config.get("extension_step_s", 5.0) if action == "EXTEND_GREEN" else 0.0,
        "reason": reason,
    }
    fw_result = validate_action(proposed_action)

    # Apply decision only if approved by Safety Firewall
    if fw_result["allowed"]:
        if action == "START_TRANSITION":
            yellow_phase = NEXT_CLEARANCE_PHASE[cur_phase]
            traci_client.trafficlight.setPhase(junction_id, yellow_phase)
        elif action == "EXTEND_GREEN":
            # Keep green within bounded max limit
            if state["allocated_green"] < config["max_green_s"]:
                step_len = min(config["extension_step_s"], config["max_green_s"] - state["allocated_green"])
                state["allocated_green"] += step_len
    else:
        # Firewall rejected unsafe proposal — block command from reaching TraCI
        action = "HOLD"
        reason = f"firewall_blocked: {fw_result['reason']}"

    return {
        "timestamp": sim_time,
        "junction_id": junction_id,
        "current_phase": phase_name,
        "queue_main": q_main,
        "queue_cross": q_cross,
        "action": action,
        "reason": reason,
    }
