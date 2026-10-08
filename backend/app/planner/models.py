"""TrafficTwin AI — Digital Twin Plan Evaluator Models (Module M9).

Defines snapshot structures, plan options (Plan A, Plan B, Plan C), and evaluation results.
"""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class JunctionSnapshot:
    """Snapshot of a single junction state at a specific simulation timestep."""

    junction_id: str
    current_phase: int
    elapsed_green_s: float
    queue_main: int
    queue_cross: int
    downstream_edge: str
    downstream_occupancy: float
    spillback_risk: str
    cross_fairness_debt: float
    starvation_risk: bool
    emergency_status: str


@dataclass
class CorridorSnapshot:
    """Complete snapshot of the 4-junction corridor state."""

    timestamp: float
    scenario: str
    controller_mode: str
    junctions: dict[str, JunctionSnapshot] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "scenario": self.scenario,
            "controller_mode": self.controller_mode,
            "junctions": {k: asdict(v) for k, v in self.junctions.items()},
        }


@dataclass
class PlanOption:
    """A traffic control alternative evaluated by the Digital Twin."""

    plan_id: str  # PLAN_A, PLAN_B, PLAN_C
    name: str
    description: str
    proposed_actions: dict[str, str]  # junction_id -> action
    is_valid: bool
    validation_reason: str
    delay_score: float
    queue_score: float
    spillback_score: float
    fairness_score: float
    emergency_score: float
    total_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class EvaluationResult:
    """Outcome of Digital Twin Plan A/B/C deterministic evaluation."""

    selected_plan_id: str
    selected_plan: PlanOption
    candidate_plans: list[PlanOption]
    selection_reason: str
    fallback_engaged: bool
    timestamp: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_plan_id": self.selected_plan_id,
            "selected_plan": self.selected_plan.to_dict(),
            "candidate_plans": [p.to_dict() for p in self.candidate_plans],
            "selection_reason": self.selection_reason,
            "fallback_engaged": self.fallback_engaged,
            "timestamp": self.timestamp,
        }
