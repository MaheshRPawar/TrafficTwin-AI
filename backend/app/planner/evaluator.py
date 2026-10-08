"""TrafficTwin AI — Digital Twin Plan A/B/C Evaluator (Module M9).

Deterministic multi-plan generator and evaluator:
- Plan A: Current safe timing progression.
- Plan B: Bounded green extension (+5s) for heavy queues.
- Plan C: Downstream clearing & coordinated corridor progression (strongest spillback guard).

All plans are validated against M5 Safety Firewall and M6 Spillback Guard.
The lowest valid score is selected and explainable decision logs are generated.
"""

from pathlib import Path
from typing import Any

import yaml

from backend.app.guards.safety_firewall import validate_action
from backend.app.planner.models import CorridorSnapshot, EvaluationResult, PlanOption

DEFAULT_PLANNER_CONFIG = {
    "weight_delay": 1.0,
    "weight_queue": 2.0,
    "weight_spillback": 3.0,
    "weight_fairness": 1.5,
    "weight_emergency": 5.0,
    "min_green_s": 10.0,
    "max_green_s": 40.0,
    "extension_step_s": 5.0,
    "warning_threshold": 0.75,
    "critical_threshold": 0.85,
}


def load_planner_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """Load planner scoring weights and safety limits from params.yaml."""
    if config_path is None:
        config_path = Path("backend/config/params.yaml")
    else:
        config_path = Path(config_path)

    cfg = dict(DEFAULT_PLANNER_CONFIG)
    if not config_path.exists():
        return cfg

    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data:
            if "planner" in data:
                pc = data["planner"]
                cfg["weight_delay"] = float(pc.get("weight_delay", cfg["weight_delay"]))
                cfg["weight_queue"] = float(pc.get("weight_queue", cfg["weight_queue"]))
                cfg["weight_spillback"] = float(
                    pc.get("weight_spillback", cfg["weight_spillback"])
                )
                cfg["weight_fairness"] = float(
                    pc.get("weight_fairness", cfg["weight_fairness"])
                )
                cfg["weight_emergency"] = float(
                    pc.get("weight_emergency", cfg["weight_emergency"])
                )

            if "safety_firewall" in data:
                sf = data["safety_firewall"]
                cfg["min_green_s"] = float(sf.get("min_green_s", cfg["min_green_s"]))
                cfg["max_green_s"] = float(sf.get("max_green_s", cfg["max_green_s"]))

            if "reactive_controller" in data:
                rc = data["reactive_controller"]
                cfg["extension_step_s"] = float(
                    rc.get("extension_step_s", cfg["extension_step_s"])
                )

            if "spillback" in data:
                sc = data["spillback"]
                cfg["warning_threshold"] = float(
                    sc.get("warning_threshold", cfg["warning_threshold"])
                )
                cfg["critical_threshold"] = float(
                    sc.get("critical_threshold", cfg["critical_threshold"])
                )
    except (OSError, yaml.YAMLError, ValueError, KeyError):
        return cfg

    return cfg


class DigitalTwinPlanner:
    """Evaluates candidate control strategies (Plan A, B, C) in the digital twin."""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or load_planner_config()

    def generate_plan_a(self, snapshot: CorridorSnapshot) -> PlanOption:
        """Plan A: Current safe timing progression."""
        actions: dict[str, str] = {}
        is_valid = True
        reasons: list[str] = []

        for jid, js in snapshot.junctions.items():
            if js.current_phase in (0, 3):
                actions[jid] = "KEEP_GREEN"
            else:
                actions[jid] = "HOLD"

            # Validate against safety firewall
            fw_act = {
                "junction_id": jid,
                "current_phase": js.current_phase,
                "requested_phase": js.current_phase,
                "action": actions[jid],
                "elapsed_green_s": js.elapsed_green_s,
                "extension_s": 0.0,
            }
            fw_res = validate_action(fw_act)
            if not fw_res["allowed"]:
                is_valid = False
                reasons.append(f"{jid}:{fw_res['reason']}")

        return PlanOption(
            plan_id="PLAN_A",
            name="Current Safe Timing",
            description="Maintain current phase timing and standard cycle progression.",
            proposed_actions=actions,
            is_valid=is_valid,
            validation_reason="; ".join(reasons) if reasons else "All safety rules satisfied",
            delay_score=0.0,
            queue_score=0.0,
            spillback_score=0.0,
            fairness_score=0.0,
            emergency_score=0.0,
            total_score=0.0,
        )

    def generate_plan_b(self, snapshot: CorridorSnapshot) -> PlanOption:
        """Plan B: Bounded green extension (+5s) for heavy queues."""
        actions: dict[str, str] = {}
        is_valid = True
        reasons: list[str] = []
        ext_step = self.config["extension_step_s"]
        max_green = self.config["max_green_s"]

        for jid, js in snapshot.junctions.items():
            # If critical downstream spillback risk on Phase 0, extension is strictly illegal
            if js.current_phase == 0 and js.downstream_occupancy >= self.config["critical_threshold"]:
                actions[jid] = "EXTEND_GREEN"  # Proposed
                is_valid = False
                reasons.append(f"{jid}:m6_spillback_violation_occupancy_{js.downstream_occupancy:.2f}")
                continue

            # If green and queues present
            if js.current_phase in (0, 3):
                cur_q = js.queue_main if js.current_phase == 0 else js.queue_cross
                if cur_q >= 3 and (js.elapsed_green_s + ext_step) <= max_green:
                    actions[jid] = "EXTEND_GREEN"
                else:
                    actions[jid] = "KEEP_GREEN"
            else:
                actions[jid] = "HOLD"

            # Validate against safety firewall
            fw_act = {
                "junction_id": jid,
                "current_phase": js.current_phase,
                "requested_phase": js.current_phase,
                "action": actions[jid],
                "elapsed_green_s": js.elapsed_green_s,
                "extension_s": ext_step if actions[jid] == "EXTEND_GREEN" else 0.0,
            }
            fw_res = validate_action(fw_act)
            if not fw_res["allowed"]:
                is_valid = False
                reasons.append(f"{jid}:{fw_res['reason']}")

        return PlanOption(
            plan_id="PLAN_B",
            name="Bounded Green Extension",
            description="Extend green by 5s for heavy queues up to the 40s safety ceiling.",
            proposed_actions=actions,
            is_valid=is_valid,
            validation_reason="; ".join(reasons) if reasons else "All safety & spillback rules satisfied",
            delay_score=0.0,
            queue_score=0.0,
            spillback_score=0.0,
            fairness_score=0.0,
            emergency_score=0.0,
            total_score=0.0,
        )

    def generate_plan_c(self, snapshot: CorridorSnapshot) -> PlanOption:
        """Plan C: Downstream clearing & coordinated corridor progression."""
        actions: dict[str, str] = {}
        is_valid = True
        reasons: list[str] = []
        min_green = self.config["min_green_s"]

        for jid, js in snapshot.junctions.items():
            # 1. Emergency Preemption has highest coordination priority
            if js.emergency_status == "PRIORITY_STAGED":
                if js.current_phase == 0:
                    actions[jid] = "KEEP_GREEN"
                elif js.current_phase == 3:
                    actions[jid] = "START_TRANSITION" if js.elapsed_green_s >= min_green else "HOLD"
                else:
                    actions[jid] = "HOLD"

            # 2. Critical Downstream Spillback clearing
            elif js.current_phase == 0 and js.downstream_occupancy >= self.config["critical_threshold"]:
                # Upstream bottleneck gate: transition away from saturated downstream link
                actions[jid] = "START_TRANSITION" if js.elapsed_green_s >= min_green else "HOLD"

            # 3. Downstream exit junction (J4): flush queue to sink edge
            elif jid == "J4" and js.current_phase == 0:
                actions[jid] = "KEEP_GREEN"

            # 4. Side-street starvation mitigation
            elif js.starvation_risk and js.current_phase == 0:
                actions[jid] = "START_TRANSITION" if js.elapsed_green_s >= min_green else "HOLD"

            # 5. Default coordinated progression
            elif js.current_phase in (0, 3):
                actions[jid] = "KEEP_GREEN"
            else:
                actions[jid] = "HOLD"

            # Validate against safety firewall
            fw_act = {
                "junction_id": jid,
                "current_phase": js.current_phase,
                "requested_phase": js.current_phase if actions[jid] != "START_TRANSITION" else None,
                "action": actions[jid],
                "elapsed_green_s": js.elapsed_green_s,
                "extension_s": 0.0,
            }
            fw_res = validate_action(fw_act)
            if not fw_res["allowed"]:
                is_valid = False
                reasons.append(f"{jid}:{fw_res['reason']}")

        return PlanOption(
            plan_id="PLAN_C",
            name="Downstream Clearing & Corridor Coordination",
            description="Clear downstream bottlenecks and coordinate signal timings across the corridor.",
            proposed_actions=actions,
            is_valid=is_valid,
            validation_reason="; ".join(reasons) if reasons else "All safety, spillback, and coordination rules satisfied",
            delay_score=0.0,
            queue_score=0.0,
            spillback_score=0.0,
            fairness_score=0.0,
            emergency_score=0.0,
            total_score=0.0,
        )

    def score_plan(self, plan: PlanOption, snapshot: CorridorSnapshot) -> None:
        """Deterministic transparent scoring of a candidate plan."""
        w_delay = self.config["weight_delay"]
        w_queue = self.config["weight_queue"]
        w_spill = self.config["weight_spillback"]
        w_fair = self.config["weight_fairness"]
        w_emerg = self.config["weight_emergency"]

        raw_delay = 0.0
        raw_queue = 0.0
        raw_spill = 0.0
        raw_fair = 0.0
        raw_emerg = 0.0

        for jid, js in snapshot.junctions.items():
            act = plan.proposed_actions.get(jid, "HOLD")

            # Queue & delay estimation
            tot_q = js.queue_main + js.queue_cross
            raw_queue += tot_q

            if act == "EXTEND_GREEN":
                if js.current_phase == 0:
                    raw_delay += max(0, js.queue_cross * 2.0)
                else:
                    raw_delay += max(0, js.queue_main * 2.0)
            elif act == "START_TRANSITION":
                raw_delay += 5.0  # Clearance penalty
            else:
                raw_delay += tot_q * 1.0

            # Spillback penalty: heavily penalize feeding into high occupancy
            occ = js.downstream_occupancy
            if js.current_phase == 0 and act in ("KEEP_GREEN", "EXTEND_GREEN"):
                if occ >= self.config["critical_threshold"]:
                    raw_spill += 50.0  # Severe penalty
                elif occ >= self.config["warning_threshold"]:
                    raw_spill += 20.0
                else:
                    raw_spill += occ * 5.0
            elif js.current_phase == 0 and act == "START_TRANSITION":
                # Mitigating spillback gives lower spillback penalty
                raw_spill += 2.0

            # Fairness debt penalty
            raw_fair += js.cross_fairness_debt
            if js.starvation_risk and act != "START_TRANSITION" and js.current_phase == 0:
                raw_fair += 25.0

            # Emergency priority penalty
            if js.emergency_status == "PRIORITY_STAGED":
                if js.current_phase == 0 and act in ("KEEP_GREEN", "EXTEND_GREEN"):
                    raw_emerg += 0.0  # Optimal for emergency
                elif js.current_phase == 3 and act == "START_TRANSITION":
                    raw_emerg += 1.0  # Transitioning towards main green
                else:
                    raw_emerg += 40.0  # Blocking emergency corridor

        plan.delay_score = round(raw_delay, 2)
        plan.queue_score = round(raw_queue, 2)
        plan.spillback_score = round(raw_spill, 2)
        plan.fairness_score = round(raw_fair, 2)
        plan.emergency_score = round(raw_emerg, 2)

        total = (
            w_delay * plan.delay_score
            + w_queue * plan.queue_score
            + w_spill * plan.spillback_score
            + w_fair * plan.fairness_score
            + w_emerg * plan.emergency_score
        )
        plan.total_score = round(total, 2)

    def evaluate(self, snapshot: CorridorSnapshot) -> EvaluationResult:
        """Evaluate Plan A, B, and C against the corridor state snapshot."""
        try:
            plan_a = self.generate_plan_a(snapshot)
            plan_b = self.generate_plan_b(snapshot)
            plan_c = self.generate_plan_c(snapshot)

            candidates = [plan_a, plan_b, plan_c]
            for p in candidates:
                self.score_plan(p, snapshot)

            valid_candidates = [p for p in candidates if p.is_valid]

            if not valid_candidates:
                # Safe Adaptive Fallback if all plans fail validation
                fallback_plan = plan_a
                return EvaluationResult(
                    selected_plan_id="SAFE_ADAPTIVE",
                    selected_plan=fallback_plan,
                    candidate_plans=candidates,
                    selection_reason="All candidate plans rejected by Safety Firewall / Downstream Guard. Engaged SAFE_ADAPTIVE fallback.",
                    fallback_engaged=True,
                    timestamp=snapshot.timestamp,
                )

            # Select candidate with lowest valid total score
            selected = min(valid_candidates, key=lambda p: p.total_score)

            reason = (
                f"Selected {selected.name} ({selected.plan_id}): Lowest valid score ({selected.total_score:.1f}). "
                f"Spillback penalty: {selected.spillback_score:.1f}, Delay: {selected.delay_score:.1f}, "
                f"Queue: {selected.queue_score:.1f}, Fairness: {selected.fairness_score:.1f}."
            )

            return EvaluationResult(
                selected_plan_id=selected.plan_id,
                selected_plan=selected,
                candidate_plans=candidates,
                selection_reason=reason,
                fallback_engaged=False,
                timestamp=snapshot.timestamp,
            )

        except Exception as exc:
            # Planner failure guard: fail-safe to safe adaptive without crashing
            fallback_plan = PlanOption(
                plan_id="SAFE_ADAPTIVE",
                name="Safe Adaptive Fallback",
                description="Controller fallback under planner exception.",
                proposed_actions={jid: "HOLD" for jid in snapshot.junctions},
                is_valid=True,
                validation_reason="Planner fault handler",
                delay_score=0.0,
                queue_score=0.0,
                spillback_score=0.0,
                fairness_score=0.0,
                emergency_score=0.0,
                total_score=999.0,
            )
            return EvaluationResult(
                selected_plan_id="SAFE_ADAPTIVE",
                selected_plan=fallback_plan,
                candidate_plans=[fallback_plan],
                selection_reason=f"Planner exception: {exc}. Engaged SAFE_ADAPTIVE fallback.",
                fallback_engaged=True,
                timestamp=snapshot.timestamp,
            )

    evaluate_corridor = evaluate
