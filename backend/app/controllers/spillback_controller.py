"""TrafficTwin AI — Spillback-Aware Signal Controller (Module M6).

Module exposing core spillback controller components for backend applications.
"""

from experiments.spillback_controller import (
    DEFAULT_CONFIG,
    DOWNSTREAM_EDGES,
    apply_spillback_guard,
    calculate_spillback_risk,
    get_downstream_state,
    load_spillback_config,
    step_spillback_junction,
)

__all__ = [
    "DEFAULT_CONFIG",
    "DOWNSTREAM_EDGES",
    "apply_spillback_guard",
    "calculate_spillback_risk",
    "get_downstream_state",
    "load_spillback_config",
    "step_spillback_junction",
]
