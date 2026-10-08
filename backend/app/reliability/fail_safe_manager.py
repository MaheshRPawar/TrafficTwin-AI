"""TrafficTwin AI — Fail-Safe Modes State Machine (Module M8).

Manages high-availability operational modes and fault tolerance for the corridor:
- PREDICTIVE: Full telemetry, wave forecasting, and Plan A/B/C available.
- SAFE_ADAPTIVE: Fallback to local Queue + Spillback + Fairness control (M3+M6+M7).
- LOCAL_SAFE: Fallback to approved fixed-time cycle from fallback_plan.json.
- SHADOW_RECOVERY: Shadow execution validating stability before re-engaging predictive mode.

Transition Chain:
    PREDICTIVE -> SAFE_ADAPTIVE -> LOCAL_SAFE -> SHADOW_RECOVERY -> PREDICTIVE
"""

import csv
import json
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml


class FailSafeMode(StrEnum):
    """Operational reliability modes for TrafficTwin AI corridor."""

    PREDICTIVE = "PREDICTIVE"
    SAFE_ADAPTIVE = "SAFE_ADAPTIVE"
    LOCAL_SAFE = "LOCAL_SAFE"
    SHADOW_RECOVERY = "SHADOW_RECOVERY"


# Valid deterministic state transitions
PERMITTED_TRANSITIONS = {
    (FailSafeMode.PREDICTIVE, FailSafeMode.SAFE_ADAPTIVE),
    (FailSafeMode.PREDICTIVE, FailSafeMode.LOCAL_SAFE),
    (FailSafeMode.SAFE_ADAPTIVE, FailSafeMode.LOCAL_SAFE),
    (FailSafeMode.SAFE_ADAPTIVE, FailSafeMode.SHADOW_RECOVERY),
    (FailSafeMode.LOCAL_SAFE, FailSafeMode.SHADOW_RECOVERY),
    (FailSafeMode.SHADOW_RECOVERY, FailSafeMode.PREDICTIVE),
    (FailSafeMode.SHADOW_RECOVERY, FailSafeMode.LOCAL_SAFE),
    (FailSafeMode.SHADOW_RECOVERY, FailSafeMode.SAFE_ADAPTIVE),
}

DEFAULT_RELIABILITY_CONFIG = {
    "gps_stale_threshold_s": 5.0,
    "trust_predictive_threshold": 0.70,
    "trust_local_threshold": 0.40,
    "trust_resume_threshold": 0.80,
    "shadow_recovery_stable_window_s": 30.0,
}


def load_reliability_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """Load reliability thresholds from params.yaml."""
    if config_path is None:
        config_path = Path("backend/config/params.yaml")
    else:
        config_path = Path(config_path)

    cfg = dict(DEFAULT_RELIABILITY_CONFIG)
    if not config_path.exists():
        return cfg

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data and "reliability" in data:
            rc = data["reliability"]
            cfg["gps_stale_threshold_s"] = float(
                rc.get("gps_stale_threshold_s", cfg["gps_stale_threshold_s"])
            )
            cfg["trust_predictive_threshold"] = float(
                rc.get("trust_predictive_threshold", cfg["trust_predictive_threshold"])
            )
            cfg["trust_local_threshold"] = float(
                rc.get("trust_local_threshold", cfg["trust_local_threshold"])
            )
            cfg["trust_resume_threshold"] = float(
                rc.get("trust_resume_threshold", cfg["trust_resume_threshold"])
            )
            cfg["shadow_recovery_stable_window_s"] = float(
                rc.get(
                    "shadow_recovery_stable_window_s",
                    cfg["shadow_recovery_stable_window_s"],
                )
            )
    except (OSError, yaml.YAMLError, ValueError, KeyError):
        return cfg

    return cfg


def load_fallback_plan(plan_path: Path | str | None = None) -> dict[str, Any]:
    """Load authoritative fixed fallback plan from fallback_plan.json."""
    if plan_path is None:
        plan_path = Path("backend/app/reliability/fallback_plan.json")
    else:
        plan_path = Path(plan_path)

    if not plan_path.exists():
        # Fallback default structure
        return {
            "description": "Default Fixed Plan",
            "cycle_length_s": 60,
            "phases": [
                {"index": 0, "name": "MAIN_GREEN", "duration_s": 30},
                {"index": 1, "name": "MAIN_YELLOW", "duration_s": 3},
                {"index": 2, "name": "ALL_RED_1", "duration_s": 2},
                {"index": 3, "name": "CROSS_GREEN", "duration_s": 20},
                {"index": 4, "name": "CROSS_YELLOW", "duration_s": 3},
                {"index": 5, "name": "ALL_RED_2", "duration_s": 2},
            ],
        }

    with open(plan_path, encoding="utf-8") as f:
        return json.load(f)


class FailSafeManager:
    """State machine managing reliability modes, fault injection, and recovery."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        fallback_plan: dict[str, Any] | None = None,
        initial_mode: FailSafeMode = FailSafeMode.PREDICTIVE,
    ):
        self.config = config or load_reliability_config()
        self.fallback_plan = fallback_plan or load_fallback_plan()
        self.current_mode = initial_mode
        self.last_transition_time = 0.0
        self.shadow_start_time: float | None = None
        self.transition_history: list[dict[str, Any]] = []

    def get_fallback_target_phase(self, sim_time: float) -> int:
        """Compute authoritative fixed-time phase for LOCAL_SAFE mode from fallback_plan.json."""
        cycle_len = self.fallback_plan.get("cycle_length_s", 60)
        cycle_time = sim_time % cycle_len

        # Phases sequence:
        # Phase 0 (Main Green): 0 to 30s
        # Phase 1 (Main Yellow): 30 to 33s
        # Phase 2 (All Red 1): 33 to 35s
        # Phase 3 (Cross Green): 35 to 55s
        # Phase 4 (Cross Yellow): 55 to 58s
        # Phase 5 (All Red 2): 58 to 60s
        accumulated = 0
        for p in self.fallback_plan.get("phases", []):
            dur = p.get("duration_s", 0)
            if cycle_time < (accumulated + dur):
                return p.get("index", 0)
            accumulated += dur

        return 0

    def validate_transition(
        self,
        target_mode: FailSafeMode,
    ) -> bool:
        """Check if target mode transition is permitted by safety state machine."""
        if target_mode == self.current_mode:
            return True
        return (self.current_mode, target_mode) in PERMITTED_TRANSITIONS

    def execute_transition(
        self,
        new_mode: FailSafeMode,
        reason: str,
        sim_time: float,
        trust_score: float = 1.0,
    ) -> dict[str, Any]:
        """Perform mode transition, update timestamps, and record audit event."""
        if not self.validate_transition(new_mode):
            raise ValueError(
                f"Illegal state transition rejected: {self.current_mode.value} -> {new_mode.value}"
            )

        old_mode = self.current_mode
        self.current_mode = new_mode
        self.last_transition_time = sim_time

        if new_mode == FailSafeMode.SHADOW_RECOVERY:
            self.shadow_start_time = sim_time
        elif new_mode != FailSafeMode.SHADOW_RECOVERY:
            self.shadow_start_time = None

        fallback_used = (
            "fixed_fallback_plan_m1"
            if new_mode == FailSafeMode.LOCAL_SAFE
            else ("queue_spillback_fairness_m7" if new_mode == FailSafeMode.SAFE_ADAPTIVE else "predictive_plan_abc")
        )

        event = {
            "timestamp": sim_time,
            "from_mode": old_mode.value,
            "to_mode": new_mode.value,
            "reason": reason,
            "fallback_mechanism": fallback_used,
            "trust_score": round(trust_score, 2),
        }
        self.transition_history.append(event)
        return event

    def evaluate_state(
        self,
        sim_time: float,
        telemetry_healthy: bool,
        planner_healthy: bool,
        controller_healthy: bool,
        trust_score: float,
        gps_age_s: float = 0.0,
    ) -> dict[str, Any]:
        """Evaluate system health inputs and execute state machine mode transitions."""
        trust_pred_th = self.config["trust_predictive_threshold"]
        trust_local_th = self.config["trust_local_threshold"]
        trust_resume_th = self.config["trust_resume_threshold"]
        gps_stale_th = self.config["gps_stale_threshold_s"]
        shadow_window = self.config["shadow_recovery_stable_window_s"]

        transition_event = None

        # 1. State: PREDICTIVE
        if self.current_mode == FailSafeMode.PREDICTIVE:
            if not controller_healthy or trust_score < trust_local_th:
                transition_event = self.execute_transition(
                    FailSafeMode.LOCAL_SAFE,
                    reason="controller_failure_or_critical_trust_drop",
                    sim_time=sim_time,
                    trust_score=trust_score,
                )
            elif (
                not planner_healthy
                or not telemetry_healthy
                or gps_age_s > gps_stale_th
                or trust_score < trust_pred_th
            ):
                transition_event = self.execute_transition(
                    FailSafeMode.SAFE_ADAPTIVE,
                    reason="planner_unavailable_or_telematics_degradation",
                    sim_time=sim_time,
                    trust_score=trust_score,
                )

        # 2. State: SAFE_ADAPTIVE
        elif self.current_mode == FailSafeMode.SAFE_ADAPTIVE:
            if not controller_healthy or trust_score < trust_local_th:
                transition_event = self.execute_transition(
                    FailSafeMode.LOCAL_SAFE,
                    reason="controller_failure_under_adaptive_mode",
                    sim_time=sim_time,
                    trust_score=trust_score,
                )
            elif (
                planner_healthy
                and telemetry_healthy
                and gps_age_s <= gps_stale_th
                and trust_score >= trust_resume_th
            ):
                transition_event = self.execute_transition(
                    FailSafeMode.SHADOW_RECOVERY,
                    reason="services_restored_initiating_shadow_validation",
                    sim_time=sim_time,
                    trust_score=trust_score,
                )

        # 3. State: LOCAL_SAFE
        elif self.current_mode == FailSafeMode.LOCAL_SAFE:
            if (
                controller_healthy
                and planner_healthy
                and telemetry_healthy
                and gps_age_s <= gps_stale_th
                and trust_score >= trust_resume_th
            ):
                transition_event = self.execute_transition(
                    FailSafeMode.SHADOW_RECOVERY,
                    reason="full_system_health_restored_initiating_shadow_validation",
                    sim_time=sim_time,
                    trust_score=trust_score,
                )

        # 4. State: SHADOW_RECOVERY
        elif self.current_mode == FailSafeMode.SHADOW_RECOVERY:
            if not controller_healthy or trust_score < trust_local_th:
                transition_event = self.execute_transition(
                    FailSafeMode.LOCAL_SAFE,
                    reason="instability_detected_during_shadow_recovery",
                    sim_time=sim_time,
                    trust_score=trust_score,
                )
            elif not planner_healthy or not telemetry_healthy or trust_score < trust_pred_th:
                transition_event = self.execute_transition(
                    FailSafeMode.SAFE_ADAPTIVE,
                    reason="partial_loss_during_shadow_recovery",
                    sim_time=sim_time,
                    trust_score=trust_score,
                )
            else:
                # Check validation stability window
                if self.shadow_start_time is not None:
                    stable_duration = sim_time - self.shadow_start_time
                    if stable_duration >= shadow_window:
                        transition_event = self.execute_transition(
                            FailSafeMode.PREDICTIVE,
                            reason=f"shadow_validation_passed_stable_{stable_duration:.0f}s",
                            sim_time=sim_time,
                            trust_score=trust_score,
                        )

        return {
            "current_mode": self.current_mode.value,
            "transition_event": transition_event,
            "shadow_start_time": self.shadow_start_time,
            "last_transition_time": self.last_transition_time,
        }

    def log_transitions_to_csv(self, output_path: Path | str | None = None) -> None:
        """Write all logged mode transition audit records to CSV."""
        if output_path is None:
            output_path = Path("data/output/reliability/mode_transitions.csv")
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        columns = [
            "timestamp",
            "from_mode",
            "to_mode",
            "reason",
            "fallback_mechanism",
            "trust_score",
        ]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(self.transition_history)
