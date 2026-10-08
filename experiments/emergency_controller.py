"""TrafficTwin AI — Fairness, Staged Ambulance Priority, and Recovery Controller (Module M7).

Implements:
1. Fairness Debt: Deterministic tracking of approach delays, max wait, missed cycles,
   and starvation prevention for side-streets.
2. Staged Ambulance Priority: Route-aware emergency preemption along J1->J2->J3->J4,
   calculating ETA, verifying downstream capacity before preemption, and staging green.
3. Post-Emergency Bounded Recovery: Bounded green service for delayed side-streets
   to normalize fairness debt before returning to standard adaptive control.

Authoritative Runtime Execution Chain:
    M3 (Queue-Reactive) -> M7 (Fairness & Emergency Policy) -> M6 (Downstream Guard) -> M5 (Safety Firewall) -> TraCI
"""

from pathlib import Path
from typing import Any

import yaml

from backend.app.guards.safety_firewall import validate_action
from experiments.reactive_controller import (
    INCOMING_LANES,
    NEXT_CLEARANCE_PHASE,
    decide_action,
    get_incoming_queues,
)
from experiments.spillback_controller import (
    apply_spillback_guard,
    get_downstream_state,
)

# Route sequence for Eastbound corridor
CORRIDOR_EB_SEQUENCE = [
    {"edge": "W0_J1", "target_junction": "J1", "downstream_edge": "J1_J2"},
    {"edge": "J1_J2", "target_junction": "J2", "downstream_edge": "J2_J3"},
    {"edge": "J2_J3", "target_junction": "J3", "downstream_edge": "J3_J4"},
    {"edge": "J3_J4", "target_junction": "J4", "downstream_edge": "J4_E5"},
]

DEFAULT_M7_CONFIG = {
    "min_green_s": 10.0,
    "max_green_s": 40.0,
    "yellow_s": 3.0,
    "all_red_s": 2.0,
    "extension_step_s": 5.0,
    "queue_threshold": 3,
    "alpha_avg_wait": 0.4,
    "beta_max_wait": 0.4,
    "gamma_missed_cycles": 0.2,
    "starvation_threshold": 35.0,
    "max_wait_threshold_s": 90.0,
    "lead_time_s": 15.0,
    "pass_window_s": 10.0,  # nosec B105
    "recovery_max_green_s": 25.0,
    "recovery_cap_s": 60.0,
    "warning_threshold": 0.75,
    "critical_threshold": 0.85,
}


def load_m7_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """Load configuration parameters for M7 from params.yaml with authoritative defaults."""
    if config_path is None:
        config_path = Path("backend/config/params.yaml")
    else:
        config_path = Path(config_path)

    cfg = dict(DEFAULT_M7_CONFIG)
    if not config_path.exists():
        return cfg

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data:
            if "safety_firewall" in data:
                sf = data["safety_firewall"]
                cfg["min_green_s"] = float(sf.get("min_green_s", cfg["min_green_s"]))
                cfg["max_green_s"] = float(sf.get("max_green_s", cfg["max_green_s"]))
                cfg["yellow_s"] = float(sf.get("yellow_s", cfg["yellow_s"]))
                cfg["all_red_s"] = float(sf.get("all_red_s", cfg["all_red_s"]))
                cfg["max_wait_threshold_s"] = float(
                    sf.get("max_wait_threshold_s", cfg["max_wait_threshold_s"])
                )

            if "reactive_controller" in data:
                rc = data["reactive_controller"]
                cfg["extension_step_s"] = float(
                    rc.get("extension_step_s", cfg["extension_step_s"])
                )
                cfg["queue_threshold"] = int(
                    rc.get("queue_threshold", cfg["queue_threshold"])
                )

            if "spillback" in data:
                sc = data["spillback"]
                cfg["warning_threshold"] = float(
                    sc.get("warning_threshold", cfg["warning_threshold"])
                )
                cfg["critical_threshold"] = float(
                    sc.get("critical_threshold", cfg["critical_threshold"])
                )

            if "fairness" in data:
                fc = data["fairness"]
                cfg["alpha_avg_wait"] = float(
                    fc.get("alpha_avg_wait", cfg["alpha_avg_wait"])
                )
                cfg["beta_max_wait"] = float(
                    fc.get("beta_max_wait", cfg["beta_max_wait"])
                )
                cfg["gamma_missed_cycles"] = float(
                    fc.get("gamma_missed_cycles", cfg["gamma_missed_cycles"])
                )
                cfg["starvation_threshold"] = float(
                    fc.get("starvation_threshold", cfg["starvation_threshold"])
                )

            if "emergency_preemption" in data:
                ep = data["emergency_preemption"]
                cfg["lead_time_s"] = float(ep.get("lead_time_s", cfg["lead_time_s"]))
                cfg["pass_window_s"] = float(
                    ep.get("pass_window_s", cfg["pass_window_s"])
                )
                cfg["recovery_max_green_s"] = float(
                    ep.get("recovery_max_green_s", cfg["recovery_max_green_s"])
                )
                cfg["recovery_cap_s"] = float(
                    ep.get("recovery_cap_s", cfg["recovery_cap_s"])
                )
    except (OSError, yaml.YAMLError, ValueError, KeyError):
        return cfg

    return cfg


# ---------------------------------------------------------------------------
# Part A: Fairness Debt Tracker
# ---------------------------------------------------------------------------
class FairnessTracker:
    """Tracks waiting times, missed cycles, and fairness debt per approach."""

    def __init__(self, junction_ids: list[str], config: dict[str, Any] | None = None):
        self.junction_ids = junction_ids
        self.config = config or DEFAULT_M7_CONFIG
        self.state: dict[str, dict[str, Any]] = {}
        for jid in junction_ids:
            self.state[jid] = {
                "cross": {
                    "avg_wait": 0.0,
                    "max_wait": 0.0,
                    "missed_cycles": 0,
                    "fairness_debt": 0.0,
                    "starvation_risk": False,
                    "waiting_vehs": 0,
                    "last_serviced_time": 0.0,
                },
                "main": {
                    "avg_wait": 0.0,
                    "max_wait": 0.0,
                    "missed_cycles": 0,
                    "fairness_debt": 0.0,
                    "starvation_risk": False,
                    "waiting_vehs": 0,
                    "last_serviced_time": 0.0,
                },
                "last_active_green": 0,  # 0: Main, 3: Cross
                "cycle_count": 0,
            }

    def update(
        self,
        traci_client: Any,
        junction_id: str,
        current_phase: int,
        sim_time: float,
    ) -> dict[str, Any]:
        """Update waiting times, missed cycles, and fairness debt for junction approaches."""
        j_state = self.state[junction_id]
        lanes = INCOMING_LANES.get(junction_id, {"main": [], "cross": []})

        # Calculate waiting time metrics per approach
        for approach, lane_ids in [("main", lanes["main"]), ("cross", lanes["cross"])]:
            waiting_times: list[float] = []
            for lane in lane_ids:
                try:
                    veh_ids = traci_client.lane.getLastStepVehicleIDs(lane)
                except Exception:
                    veh_ids = []
                for vid in veh_ids:
                    try:
                        # Halted or waiting vehicle
                        speed = traci_client.vehicle.getSpeed(vid)
                        if speed < 0.5:
                            wt = traci_client.vehicle.getWaitingTime(vid)
                            waiting_times.append(float(wt))
                    except Exception:  # nosec B112
                        continue

            app_state = j_state[approach]
            if waiting_times:
                app_state["avg_wait"] = round(sum(waiting_times) / len(waiting_times), 2)
                app_state["max_wait"] = round(max(waiting_times), 2)
                app_state["waiting_vehs"] = len(waiting_times)
            else:
                app_state["avg_wait"] = 0.0
                app_state["max_wait"] = 0.0
                app_state["waiting_vehs"] = 0

        # Detect cycle progression and missed cycles
        # Phase 0 = MAIN_GREEN, Phase 3 = CROSS_GREEN
        if current_phase == 0 and j_state["last_active_green"] != 0:
            j_state["last_active_green"] = 0
            j_state["main"]["last_serviced_time"] = sim_time
            if j_state["cross"]["waiting_vehs"] > 0:
                j_state["cross"]["missed_cycles"] += 1
            else:
                j_state["cross"]["missed_cycles"] = max(0, j_state["cross"]["missed_cycles"] - 1)

        elif current_phase == 3 and j_state["last_active_green"] != 3:
            j_state["last_active_green"] = 3
            j_state["cross"]["last_serviced_time"] = sim_time
            j_state["cross"]["missed_cycles"] = 0  # Serviced!
            if j_state["main"]["waiting_vehs"] > 0:
                j_state["main"]["missed_cycles"] += 1
            else:
                j_state["main"]["missed_cycles"] = max(0, j_state["main"]["missed_cycles"] - 1)

        # Compute deterministic fairness debt
        alpha = self.config["alpha_avg_wait"]
        beta = self.config["beta_max_wait"]
        gamma = self.config["gamma_missed_cycles"]
        starvation_th = self.config["starvation_threshold"]
        max_wait_th = self.config["max_wait_threshold_s"]

        for app_name in ["cross", "main"]:
            app = j_state[app_name]
            debt = (
                alpha * app["avg_wait"]
                + beta * app["max_wait"]
                + gamma * (app["missed_cycles"] * 10.0)
            )
            app["fairness_debt"] = round(debt, 2)
            app["starvation_risk"] = bool(debt >= starvation_th or app["max_wait"] >= max_wait_th)

        return {
            "cross_debt": j_state["cross"]["fairness_debt"],
            "cross_avg_wait": j_state["cross"]["avg_wait"],
            "cross_max_wait": j_state["cross"]["max_wait"],
            "cross_missed_cycles": j_state["cross"]["missed_cycles"],
            "cross_starvation_risk": j_state["cross"]["starvation_risk"],
            "main_debt": j_state["main"]["fairness_debt"],
            "main_avg_wait": j_state["main"]["avg_wait"],
            "main_max_wait": j_state["main"]["max_wait"],
            "main_missed_cycles": j_state["main"]["missed_cycles"],
            "main_starvation_risk": j_state["main"]["starvation_risk"],
        }

    def reset_cross_debt(self, junction_id: str) -> None:
        """Reset cross approach debt upon successful recovery/service."""
        if junction_id in self.state:
            self.state[junction_id]["cross"]["missed_cycles"] = 0
            self.state[junction_id]["cross"]["fairness_debt"] = 0.0
            self.state[junction_id]["cross"]["starvation_risk"] = False


# ---------------------------------------------------------------------------
# Part B: Staged Ambulance Priority Manager
# ---------------------------------------------------------------------------
class AmbulancePreemptionManager:
    """Manages staged corridor priority for emergency vehicles."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or DEFAULT_M7_CONFIG
        self.ambulance_id: str | None = None
        self.has_entered = False
        self.has_exited = False
        self.entry_time: float | None = None
        self.exit_time: float | None = None
        self.preemption_state: dict[str, dict[str, Any]] = {
            "J1": {"status": "INACTIVE", "eta": None, "was_staged": False},
            "J2": {"status": "INACTIVE", "eta": None, "was_staged": False},
            "J3": {"status": "INACTIVE", "eta": None, "was_staged": False},
            "J4": {"status": "INACTIVE", "eta": None, "was_staged": False},
        }

    def detect_ambulance(self, traci_client: Any, sim_time: float) -> dict[str, Any] | None:
        """Detect active emergency vehicle and track its corridor trajectory."""
        try:
            veh_ids = traci_client.vehicle.getIDList()
        except Exception:
            return None

        amb_id = None
        for vid in veh_ids:
            if vid == "emerg_1":
                amb_id = vid
                break
            try:
                vtype = traci_client.vehicle.getTypeID(vid)
                vclass = traci_client.vehicle.getVehicleClass(vid)
                if "ambulance" in vtype.lower() or vclass == "emergency":
                    amb_id = vid
                    break
            except Exception:  # nosec B112
                continue

        if not amb_id:
            if self.has_entered and not self.has_exited:
                self.has_exited = True
                self.exit_time = sim_time
            return None

        self.ambulance_id = amb_id
        if not self.has_entered:
            self.has_entered = True
            self.entry_time = sim_time

        try:
            cur_edge = traci_client.vehicle.getRoadID(amb_id)
            cur_pos = traci_client.vehicle.getLanePosition(amb_id)
            speed = traci_client.vehicle.getSpeed(amb_id)
            lane_id = traci_client.vehicle.getLaneID(amb_id)
            lane_len = traci_client.lane.getLength(lane_id) if lane_id else 200.0
            dist_to_end = max(0.0, lane_len - cur_pos)
            eta = round(dist_to_end / max(speed, 2.0), 1)
        except Exception:
            return None

        target_junction = None
        downstream_edge = None
        for seg in CORRIDOR_EB_SEQUENCE:
            if seg["edge"] == cur_edge:
                target_junction = seg["target_junction"]
                downstream_edge = seg["downstream_edge"]
                break

        if cur_edge == "J4_E5":
            target_junction = None
            if not self.has_exited:
                self.has_exited = True
                self.exit_time = sim_time

        return {
            "vehicle_id": amb_id,
            "edge": cur_edge,
            "position_m": round(cur_pos, 1),
            "speed_mps": round(speed, 1),
            "distance_to_junction_m": round(dist_to_end, 1),
            "target_junction": target_junction,
            "downstream_edge": downstream_edge,
            "eta_s": eta,
            "sim_time": sim_time,
        }

    def evaluate_priority_request(
        self,
        junction_id: str,
        amb_info: dict[str, Any] | None,
        downstream_state: dict[str, Any],
        current_phase: int,
        green_duration: float,
    ) -> tuple[str, str, str]:
        """Evaluate staged preemption policy for a junction.

        Returns:
            (priority_status, preemption_action, reason)
        """
        if not amb_info or amb_info.get("target_junction") != junction_id:
            # Junction is not currently the direct target
            prev_status = self.preemption_state[junction_id]["status"]
            if prev_status == "PRIORITY_STAGED":
                self.preemption_state[junction_id]["was_staged"] = True
            self.preemption_state[junction_id]["status"] = "INACTIVE"
            self.preemption_state[junction_id]["eta"] = None
            return "INACTIVE", "NONE", "no_active_emergency_approach"

        eta = amb_info.get("eta_s", 999.0)
        lead_time = self.config["lead_time_s"]
        min_green = self.config["min_green_s"]
        self.preemption_state[junction_id]["eta"] = eta

        # 1. Staged timing check: Preempt only when within lead time horizon
        if eta > lead_time:
            self.preemption_state[junction_id]["status"] = "STANDBY"
            return (
                "STANDBY",
                "HOLD",
                f"AMBULANCE_APPROACHING: eta={eta}s > lead_time={lead_time}s",
            )

        # 2. Downstream capacity check (M6 Protection Integration)
        # Never stage priority into a completely saturated downstream link
        ds_risk = downstream_state.get("risk", "NORMAL")
        ds_occ = downstream_state.get("occupancy", 0.0)
        if ds_risk == "CRITICAL" or ds_occ >= self.config["critical_threshold"]:
            self.preemption_state[junction_id]["status"] = "PRIORITY_DELAYED"
            return (
                "PRIORITY_DELAYED",
                "HOLD",
                f"DOWNSTREAM_CAPACITY_CRITICAL: occ={ds_occ} >= {self.config['critical_threshold']:.2f}, clearing bottleneck first",
            )

        # 3. Safe staged priority actuation
        self.preemption_state[junction_id]["status"] = "PRIORITY_STAGED"
        self.preemption_state[junction_id]["was_staged"] = True

        # Goal is Main Corridor Green (Phase 0)
        if current_phase == 0:
            # Already on main green — maintain it for ambulance
            return (
                "PRIORITY_STAGED",
                "KEEP_GREEN",
                f"DOWNSTREAM_CAPACITY_SUFFICIENT: staging EB main green (eta={eta}s)",
            )
        elif current_phase == 3:
            # Currently on cross green — transition to yellow/red then main green
            if green_duration >= min_green:
                return (
                    "PRIORITY_STAGED",
                    "START_TRANSITION",
                    f"AMBULANCE_PREEMPTION: cross min green satisfied ({green_duration:.1f}s >= {min_green}s), switching to main green",
                )
            else:
                return (
                    "PRIORITY_STAGED",
                    "HOLD",
                    f"AMBULANCE_PREEMPTION_PENDING: waiting for cross min green ({green_duration:.1f}s < {min_green}s)",
                )
        else:
            # Clearance phase (1, 2, 4, 5) — let it progress naturally through legal cycle
            return (
                "PRIORITY_STAGED",
                "HOLD",
                f"AMBULANCE_PREEMPTION_CLEARANCE: advancing clearance phase {current_phase}",
            )


# ---------------------------------------------------------------------------
# Part C: Post-Emergency Bounded Recovery Manager
# ---------------------------------------------------------------------------
class PostEmergencyRecoveryManager:
    """Provides bounded recovery green time to delayed approaches after preemption."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or DEFAULT_M7_CONFIG
        self.recovery_state: dict[str, dict[str, Any]] = {
            "J1": {"active": False, "start_time": 0.0, "allocated_green": 0.0, "served_green": 0.0},
            "J2": {"active": False, "start_time": 0.0, "allocated_green": 0.0, "served_green": 0.0},
            "J3": {"active": False, "start_time": 0.0, "allocated_green": 0.0, "served_green": 0.0},
            "J4": {"active": False, "start_time": 0.0, "allocated_green": 0.0, "served_green": 0.0},
        }
        self.total_recovery_actions = 0

    def trigger_recovery(
        self,
        junction_id: str,
        sim_time: float,
        cross_debt: float,
    ) -> None:
        """Initiate bounded recovery after emergency vehicle passage."""
        rec = self.recovery_state[junction_id]
        if not rec["active"]:
            rec["active"] = True
            rec["start_time"] = sim_time
            # Bounded recovery calculation: allocate between min_green and recovery_max_green_s
            rec_green = max(
                self.config["min_green_s"],
                min(max(cross_debt * 0.8, 12.0), self.config["recovery_max_green_s"]),
            )
            rec["allocated_green"] = round(rec_green, 1)
            rec["served_green"] = 0.0
            self.total_recovery_actions += 1

    def evaluate_recovery_policy(
        self,
        junction_id: str,
        current_phase: int,
        green_duration: float,
        sim_time: float,
        fairness_tracker: FairnessTracker,
    ) -> tuple[bool, str, str]:
        """Evaluate recovery state and determine if recovery action should be taken.

        Returns:
            (is_in_recovery, recovery_action, reason)
        """
        rec = self.recovery_state[junction_id]
        if not rec["active"]:
            return False, "NONE", "recovery_inactive"

        # Check recovery cap timeout
        if (sim_time - rec["start_time"]) > self.config["recovery_cap_s"]:
            rec["active"] = False
            fairness_tracker.reset_cross_debt(junction_id)
            return False, "NONE", "recovery_cap_timeout_reached"

        # If currently on Main Green (Phase 0), transition to Cross Green (Phase 3)
        if current_phase == 0:
            if green_duration >= self.config["min_green_s"]:
                return (
                    True,
                    "START_TRANSITION",
                    f"RECOVERY_DISPATCH: switching to cross road (allocated={rec['allocated_green']}s)",
                )
            else:
                return (
                    True,
                    "HOLD",
                    "RECOVERY_PENDING: satisfying main min green before recovery transition",
                )

        # If currently on Cross Green (Phase 3), service recovery green
        elif current_phase == 3:
            if green_duration < rec["allocated_green"]:
                return (
                    True,
                    "KEEP_GREEN",
                    f"RECOVERY_ACTIVE: servicing delayed cross approach ({green_duration:.1f}s / {rec['allocated_green']}s)",
                )
            else:
                # Recovery green fulfilled — complete recovery and transition back to normal
                rec["active"] = False
                fairness_tracker.reset_cross_debt(junction_id)
                return (
                    True,
                    "START_TRANSITION",
                    f"RECOVERY_COMPLETE: cross approach received {green_duration:.1f}s recovery service",
                )

        # Clearance phases
        return True, "HOLD", f"RECOVERY_CLEARANCE: advancing phase {current_phase}"


# ---------------------------------------------------------------------------
# Integrated M7 Step Function
# ---------------------------------------------------------------------------
def step_m7_junction(
    traci_client: Any,
    junction_id: str,
    sim_time: float,
    state: dict[str, Any],
    config: dict[str, Any],
    fairness_tracker: FairnessTracker,
    ambulance_manager: AmbulancePreemptionManager,
    recovery_manager: PostEmergencyRecoveryManager,
    amb_info: dict[str, Any] | None,
) -> dict[str, Any]:
    """Execute complete M3 -> M7 -> M6 -> M5 -> TraCI control step for one junction."""
    # 1. Read current signal phase
    cur_phase = traci_client.trafficlight.getPhase(junction_id)

    # 2. Detect phase transitions and update internal timing
    if cur_phase != state["last_phase"]:
        state["last_phase"] = cur_phase
        state["phase_start"] = sim_time
        if cur_phase in (0, 3):
            state["allocated_green"] = config["min_green_s"]
            traci_client.trafficlight.setPhaseDuration(junction_id, config["max_green_s"])

    # 3. Update queues, downstream link status, and fairness debt
    q_main, q_cross = get_incoming_queues(traci_client, junction_id)
    downstream = get_downstream_state(traci_client, junction_id, config)
    fairness = fairness_tracker.update(traci_client, junction_id, cur_phase, sim_time)

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
            "cross_debt": fairness["cross_debt"],
            "cross_starvation_risk": fairness["cross_starvation_risk"],
            "emergency_status": ambulance_manager.preemption_state[junction_id]["status"],
            "recovery_active": recovery_manager.recovery_state[junction_id]["active"],
            "action": "HOLD",
            "reason": "clearance phase active",
        }

    green_time = sim_time - state["phase_start"]

    # 5. M3: Propose reactive action based on local queues
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

    # 6. M7: Evaluate Policy (Ambulance Priority -> Recovery -> Fairness Debt)
    # Check if preemption just ended at this junction -> trigger recovery
    if (
        ambulance_manager.preemption_state[junction_id].get("was_staged")
        and (amb_info is None or amb_info.get("target_junction") != junction_id)
        and not recovery_manager.recovery_state[junction_id]["active"]
    ):
        ambulance_manager.preemption_state[junction_id]["was_staged"] = False
        recovery_manager.trigger_recovery(junction_id, sim_time, fairness["cross_debt"])

    # 6a. Ambulance Priority Check
    p_status, p_action, p_reason = ambulance_manager.evaluate_priority_request(
        junction_id=junction_id,
        amb_info=amb_info,
        downstream_state=downstream,
        current_phase=cur_phase,
        green_duration=green_time,
    )

    m7_action = m3_action
    m7_reason = m3_reason
    emergency_active = False

    if p_status in ("PRIORITY_STAGED", "PRIORITY_DELAYED", "STANDBY"):
        if p_status == "PRIORITY_STAGED" and p_action != "NONE":
            m7_action = p_action
            m7_reason = p_reason
            emergency_active = True
        elif p_status == "PRIORITY_DELAYED":
            m7_action = "HOLD"
            m7_reason = p_reason
            emergency_active = True

    # 6b. Post-Emergency Recovery Check (if not preempted)
    if not emergency_active:
        in_rec, rec_action, rec_reason = recovery_manager.evaluate_recovery_policy(
            junction_id=junction_id,
            current_phase=cur_phase,
            green_duration=green_time,
            sim_time=sim_time,
            fairness_tracker=fairness_tracker,
        )
        if in_rec and rec_action != "NONE":
            m7_action = rec_action
            m7_reason = rec_reason

        # 6c. Side-Street Fairness & Starvation Prevention Check
        elif fairness["cross_starvation_risk"]:
            if cur_phase == 0:
                if green_time >= config["min_green_s"]:
                    m7_action = "START_TRANSITION"
                    m7_reason = f"SIDE_STREET_FAIRNESS_DEBT_HIGH: debt={fairness['cross_debt']}, missed={fairness['cross_missed_cycles']} cycles"
                else:
                    m7_action = "HOLD"
                    m7_reason = "FAIRNESS_STARVATION_PENDING: waiting for main min green"
            elif cur_phase == 3:
                if green_time < config["max_green_s"] and q_cross > 0:
                    m7_action = "EXTEND_GREEN"
                    m7_reason = f"FAIRNESS_DEBT_SERVICE: clearing cross debt ({fairness['cross_debt']})"

    # 7. M6: Downstream Capacity Protection Guard
    m6_action, m6_reason, signal_action = apply_spillback_guard(
        proposed_action=m7_action,
        proposed_reason=m7_reason,
        downstream_state=downstream,
        current_phase=cur_phase,
        green_duration=green_time,
        min_green=config["min_green_s"],
        config=config,
    )

    # 8. M5: Signal Safety Firewall Validation
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

    # 9. TraCI: Actuate only if approved by M5 Safety Firewall
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
        # Firewall rejection — fail closed safely
        signal_action = "HOLD"
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
        "cross_debt": fairness["cross_debt"],
        "cross_starvation_risk": fairness["cross_starvation_risk"],
        "emergency_status": p_status,
        "recovery_active": recovery_manager.recovery_state[junction_id]["active"],
        "action": m6_action,
        "reason": m6_reason,
    }
