"""TrafficTwin AI — Spillback-Aware Traffic Signal Controller (Module M6).

Prevents upstream signal green extensions when downstream corridor links
are near capacity, protecting downstream bottlenecks from spillback saturation.

Runtime execution chain:
    M3 reactive proposal -> M6 spillback check -> M5 safety firewall -> TraCI
"""

from pathlib import Path

import yaml

from backend.app.guards.safety_firewall import validate_action
from experiments.reactive_controller import (
    NEXT_CLEARANCE_PHASE,
    decide_action,
    get_incoming_queues,
)

# Primary downstream corridor link for each controlled junction (Eastbound)
DOWNSTREAM_EDGES = {
    "J1": "J1_J2",
    "J2": "J2_J3",
    "J3": "J3_J4",
    "J4": "J4_E5",
}

# Default parameters if not present in config
DEFAULT_CONFIG = {
    "enabled": True,
    "warning_threshold": 0.75,
    "critical_threshold": 0.85,
    "effective_vehicle_len_m": 7.5,
    "min_green_s": 10.0,
    "max_green_s": 40.0,
    "extension_step_s": 5.0,
    "queue_threshold": 3,
    "yellow_s": 3.0,
    "all_red_s": 2.0,
}


def load_spillback_config(config_path=None) -> dict:
    """Load spillback controller parameters from params.yaml."""
    if config_path is None:
        config_path = Path("backend/config/params.yaml")
    else:
        config_path = Path(config_path)

    cfg = dict(DEFAULT_CONFIG)
    if not config_path.exists():
        return cfg

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data:
            if "network" in data:
                net_cfg = data["network"]
                cfg["effective_vehicle_len_m"] = float(
                    net_cfg.get("effective_vehicle_len_m", cfg["effective_vehicle_len_m"])
                )

            if "reactive_controller" in data:
                rc = data["reactive_controller"]
                cfg["min_green_s"] = float(rc.get("min_green_s", cfg["min_green_s"]))
                cfg["max_green_s"] = float(rc.get("max_green_s", cfg["max_green_s"]))
                cfg["extension_step_s"] = float(rc.get("extension_step_s", cfg["extension_step_s"]))
                cfg["queue_threshold"] = int(rc.get("queue_threshold", cfg["queue_threshold"]))
                cfg["yellow_s"] = float(rc.get("yellow_s", cfg["yellow_s"]))
                cfg["all_red_s"] = float(rc.get("all_red_s", cfg["all_red_s"]))

            if "spillback" in data:
                sc = data["spillback"]
                cfg["enabled"] = bool(sc.get("enabled", True))
                cfg["warning_threshold"] = float(
                    sc.get("warning_threshold", sc.get("occupancy_threshold", 0.75))
                )
                cfg["critical_threshold"] = float(sc.get("critical_threshold", 0.85))
    except (OSError, yaml.YAMLError, ValueError, KeyError):
        return cfg

    return cfg


def calculate_spillback_risk(
    occupancy: float,
    warning_threshold: float = 0.75,
    critical_threshold: float = 0.85,
) -> str:
    """Classify downstream occupancy into rule-based spillback risk levels."""
    if occupancy >= critical_threshold:
        return "CRITICAL"
    elif occupancy >= warning_threshold:
        return "WARNING"
    return "NORMAL"


def get_downstream_state(
    traci_client,
    junction_id: str,
    config: dict | None = None,
    downstream_edges: dict[str, str] | None = None,
) -> dict:
    """Measure actual downstream corridor state (occupancy, vehicle count, capacity, risk)."""
    edges_map = downstream_edges or DOWNSTREAM_EDGES
    edge_id = edges_map.get(junction_id)

    if not edge_id:
        return {
            "edge_id": "NONE",
            "occupancy": 0.0,
            "vehicle_count": 0,
            "capacity": 0,
            "risk": "NORMAL",
        }

    effective_veh_len = float(
        config.get("effective_vehicle_len_m", 7.5) if config else 7.5
    )
    warning_th = float(config.get("warning_threshold", 0.75) if config else 0.75)
    critical_th = float(config.get("critical_threshold", 0.85) if config else 0.85)

    # Inspect edge geometry and capacity
    lane_count = 1
    edge_length = 200.0

    try:
        lane_count = traci_client.edge.getLaneNumber(edge_id)
        lane_0 = f"{edge_id}_0"
        edge_length = traci_client.lane.getLength(lane_0)
    except Exception:
        # Fallback to standard 2-lane 200m corridor segment
        lane_count = 2
        edge_length = 200.0

    total_road_space_m = edge_length * max(lane_count, 1)
    if effective_veh_len > 0:
        capacity = int(round(total_road_space_m / effective_veh_len))
    else:
        capacity = 0

    if capacity <= 0 or total_road_space_m <= 0:
        return {
            "edge_id": edge_id,
            "occupancy": 0.0,
            "vehicle_count": 0,
            "capacity": 0,
            "risk": "NORMAL",
        }

    # Inspect vehicles on the downstream edge
    veh_count = 0
    occupied_space_m = 0.0
    raw_occ = 0.0

    try:
        veh_ids = traci_client.edge.getLastStepVehicleIDs(edge_id)
        veh_count = len(veh_ids)
        for v in veh_ids:
            try:
                v_len = traci_client.vehicle.getLength(v)
                v_gap = traci_client.vehicle.getMinGap(v)
                occupied_space_m += v_len + v_gap
            except Exception:
                occupied_space_m += effective_veh_len
    except Exception:
        # Fallback to getLastStepVehicleNumber if getLastStepVehicleIDs is unavailable
        try:
            veh_count = traci_client.edge.getLastStepVehicleNumber(edge_id)
            occupied_space_m = veh_count * effective_veh_len
        except Exception:
            veh_count = 0
            occupied_space_m = 0.0

    try:
        raw_occ = traci_client.edge.getLastStepOccupancy(edge_id)
    except Exception:
        raw_occ = 0.0

    # Occupancy percentage: max of physical space ratio, vehicle count ratio, and SUMO occupancy
    space_ratio = occupied_space_m / total_road_space_m if total_road_space_m > 0 else 0.0
    count_ratio = veh_count / capacity if capacity > 0 else 0.0
    occupancy = max(space_ratio, count_ratio, raw_occ)
    occupancy = min(max(occupancy, 0.0), 1.0)

    risk = calculate_spillback_risk(occupancy, warning_th, critical_th)

    return {
        "edge_id": edge_id,
        "occupancy": round(occupancy, 3),
        "vehicle_count": veh_count,
        "capacity": capacity,
        "risk": risk,
    }


def apply_spillback_guard(
    proposed_action: str,
    proposed_reason: str,
    downstream_state: dict,
    current_phase: int,
    green_duration: float,
    min_green: float = 10.0,
    config: dict | None = None,
) -> tuple[str, str, str]:
    """Evaluate proposed M3 action against downstream spillback risk.

    Returns:
        (m6_action, m6_reason, signal_action_for_firewall)
    """
    spillback_enabled = True if config is None else config.get("enabled", True)
    if not spillback_enabled:
        return proposed_action, proposed_reason, proposed_action

    risk = downstream_state.get("risk", "NORMAL")

    # Only guard main corridor green phase (phase 0) releasing vehicles into downstream link
    if current_phase != 0:
        return proposed_action, proposed_reason, proposed_action

    # Critical downstream occupancy: block green extension and protect downstream capacity
    if risk == "CRITICAL":
        if proposed_action == "EXTEND_GREEN":
            # Override M3 extension with explicit SPILLBACK_BLOCK
            m6_action = "SPILLBACK_BLOCK"
            m6_reason = "downstream_occupancy_critical"
            if green_duration >= min_green:
                signal_action = "START_TRANSITION"
            else:
                # Must satisfy minimum green before transitioning
                signal_action = "HOLD"
            return m6_action, m6_reason, signal_action
        elif proposed_action == "KEEP_GREEN" and green_duration >= min_green:
            # If minimum green is already met and link is critical, initiate safe transition
            m6_action = "SPILLBACK_BLOCK"
            m6_reason = "downstream_occupancy_critical"
            signal_action = "START_TRANSITION"
            return m6_action, m6_reason, signal_action

    # Warning downstream occupancy: avoid unnecessary green extension
    elif risk == "WARNING":
        if proposed_action == "EXTEND_GREEN":
            m6_action = "HOLD"
            m6_reason = "downstream_occupancy_warning: extension avoided"
            signal_action = "HOLD"
            return m6_action, m6_reason, signal_action

    # Normal conditions: allow proposed M3 action
    return proposed_action, proposed_reason, proposed_action


def step_spillback_junction(
    traci_client,
    junction_id: str,
    sim_time: float,
    state: dict,
    config: dict,
) -> dict:
    """Execute one simulation step for a junction with M3 -> M6 -> M5 -> TraCI flow."""
    # 1. Read current phase
    cur_phase = traci_client.trafficlight.getPhase(junction_id)

    # 2. Detect phase transitions and update internal timing
    if cur_phase != state["last_phase"]:
        state["last_phase"] = cur_phase
        state["phase_start"] = sim_time
        if cur_phase in (0, 3):
            state["allocated_green"] = config["min_green_s"]
            traci_client.trafficlight.setPhaseDuration(junction_id, config["max_green_s"])

    # 3. Read local incoming queues and downstream corridor state
    q_main, q_cross = get_incoming_queues(traci_client, junction_id)
    downstream = get_downstream_state(traci_client, junction_id, config)

    # 4. Handle clearance phases (phases 1, 2, 4, 5)
    if cur_phase not in (0, 3):
        return {
            "timestamp": sim_time,
            "junction_id": junction_id,
            "current_phase": cur_phase,
            "queue_main": q_main,
            "queue_cross": q_cross,
            "downstream_edge": downstream["edge_id"],
            "downstream_occupancy": downstream["occupancy"],
            "spillback_risk": downstream["risk"],
            "action": "HOLD",
            "reason": "clearance phase active",
        }

    green_time = sim_time - state["phase_start"]

    # 5. M3: Propose reactive action
    m3_action, m3_reason = decide_action(
        current_phase=cur_phase,
        green_duration=green_time,
        queue_main=q_main,
        queue_cross=q_cross,
        min_green=config["min_green_s"],
        max_green=config["max_green_s"],
        extension_step=config["extension_step_s"],
        queue_threshold=config["queue_threshold"],
    )

    # 6. M6: Evaluate spillback risk and override if needed
    m6_action, m6_reason, signal_action = apply_spillback_guard(
        proposed_action=m3_action,
        proposed_reason=m3_reason,
        downstream_state=downstream,
        current_phase=cur_phase,
        green_duration=green_time,
        min_green=config["min_green_s"],
        config=config,
    )

    # 7. M5: Validate signal action through Safety Firewall before TraCI execution
    firewall_action = {
        "junction_id": junction_id,
        "current_phase": cur_phase,
        "requested_phase": (
            NEXT_CLEARANCE_PHASE.get(cur_phase)
            if signal_action == "START_TRANSITION"
            else cur_phase
        ),
        "action": signal_action,
        "timestamp": sim_time,
        "elapsed_green_s": green_time,
        "extension_s": (
            config.get("extension_step_s", 5.0) if signal_action == "EXTEND_GREEN" else 0.0
        ),
        "reason": m6_reason,
    }
    fw_result = validate_action(firewall_action, config)

    # 8. TraCI: Actuate only if approved by M5 Safety Firewall
    if fw_result["allowed"]:
        if signal_action == "START_TRANSITION":
            yellow_phase = NEXT_CLEARANCE_PHASE[cur_phase]
            traci_client.trafficlight.setPhase(junction_id, yellow_phase)
        elif signal_action == "EXTEND_GREEN":
            if state["allocated_green"] < config["max_green_s"]:
                step_len = min(
                    config["extension_step_s"],
                    config["max_green_s"] - state["allocated_green"],
                )
                state["allocated_green"] += step_len
    else:
        # Firewall rejected proposal — fail closed, block TraCI actuation
        m6_action = "HOLD"
        m6_reason = f"firewall_blocked: {fw_result['reason']}"

    return {
        "timestamp": sim_time,
        "junction_id": junction_id,
        "current_phase": cur_phase,
        "queue_main": q_main,
        "queue_cross": q_cross,
        "downstream_edge": downstream["edge_id"],
        "downstream_occupancy": downstream["occupancy"],
        "spillback_risk": downstream["risk"],
        "action": m6_action,
        "reason": m6_reason,
    }
