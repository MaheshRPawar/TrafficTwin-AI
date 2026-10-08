# Module M8: Fail-Safe Modes and System Reliability

## Executive Summary
Module M8 implements an explicit, deterministic fault-tolerant state machine to guarantee that TrafficTwin AI never becomes a single point of failure for the urban corridor. Under degraded sensor conditions, telematics failure, planner disruption, or controller errors, the corridor automatically cascades into hardened fallback programs without human intervention.

---

## Operational Mode Definitions

| Mode | Name | Activation Conditions | Fallback / Control Mechanism | Actuation Status |
| :--- | :--- | :--- | :--- | :--- |
| **1** | `PREDICTIVE` | Full telematics stream, trust score $\ge 0.70$, planner active, wave forecast healthy | Complete multi-step Plan A/B/C optimization | Active Actuation |
| **2** | `SAFE_ADAPTIVE` | Planner/forecast down, stale GPS stream ($> 5\text{s}$), or trust score $\in [0.40, 0.70)$ | Local TraCI Queue + Spillback + Fairness engine (M3+M6+M7) | Active Actuation |
| **3** | `LOCAL_SAFE` | Controller failure, sensor crash, TraCI disruption, or trust score $< 0.40$ | Authoritative fixed-time signal cycle from `fallback_plan.json` | Active Safe Fallback |
| **4** | `SHADOW_RECOVERY` | Service restored, trust score $\ge 0.80$, verifying stability for $\ge 30\text{s}$ | Silent recommendation generation with local execution | Validation Only |

---

## State Transition Machine
```
                             ┌─────────────────┐
                             │   PREDICTIVE    │
                             └────────┬────────┘
                                      │
                   ┌──────────────────┴──────────────────┐
                   │ Planner Down / Stale GPS Stream      │ Controller Crash /
                   │ (Trust < 0.70)                      │ Critical Fault
                   ▼                                     │ (Trust < 0.40)
        ┌─────────────────────┐                          │
        │    SAFE_ADAPTIVE    │                          │
        └──────────┬──────────┘                          │
                   │                                     │
                   │ Controller Failure / Sensor Loss    │
                   │ (Trust < 0.40)                      │
                   ▼                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │                       LOCAL_SAFE                       │
        │   (Authoritative 60s Fixed Fallback: 30s Green, 20s)   │
        └──────────────────────────┬─────────────────────────────┘
                                   │
                                   │ System Restored & Healthy
                                   │ (Trust >= 0.80)
                                   ▼
        ┌────────────────────────────────────────────────────────┐
        │                    SHADOW_RECOVERY                     │
        │   - Silent recommendation generation (no overrides)    │
        │   - Stable validation window >= 30 seconds             │
        └──────────────────────────┬─────────────────────────────┘
                                   │
                                   │ Stable Window Passed
                                   ▼
                             ┌─────────────────┐
                             │   PREDICTIVE    │
                             └─────────────────┘
```

---

## Authoritative Local Safe Fallback Plan (`fallback_plan.json`)
The `LOCAL_SAFE` mode utilizes the approved fixed-time cycle program verified in Module M1. It does not perform experimental adaptive overrides or direct unvalidated TraCI commands.

```json
{
  "cycle_length_s": 60,
  "phases": [
    {"index": 0, "name": "MAIN_GREEN",   "duration_s": 30, "state": "rrrrGGGggrrrrGGGgg"},
    {"index": 1, "name": "MAIN_YELLOW",  "duration_s": 3,  "state": "rrrryyyyyrrrryyyyy"},
    {"index": 2, "name": "ALL_RED_1",    "duration_s": 2,  "state": "rrrrrrrrrrrrrrrrrr"},
    {"index": 3, "name": "CROSS_GREEN",  "duration_s": 20, "state": "GGggrrrrrGGggrrrrr"},
    {"index": 4, "name": "CROSS_YELLOW", "duration_s": 3,  "state": "yyyyrrrrryyyyrrrrr"},
    {"index": 5, "name": "ALL_RED_2",    "duration_s": 2,  "state": "rrrrrrrrrrrrrrrrrr"}
  ]
}
```

---

## Fault Injection Testing & Verification
The state machine was verified via `tests/test_fail_safe_manager.py` across 6 failure scenarios:
1. **Planner Failure Injection**: `PREDICTIVE -> SAFE_ADAPTIVE` with audit log `planner_unavailable_or_telematics_degradation`.
2. **Stale Telematics Injection**: Telematics age $> 5.0\text{s}$ triggers instantaneous fallback to `SAFE_ADAPTIVE`.
3. **Controller Fault Injection**: Controller failure immediately engages `LOCAL_SAFE` mode.
4. **Critical Trust Drop**: Trust score $< 0.40$ cascades directly to `LOCAL_SAFE`.
5. **Illegal Transition Block**: Prohibits direct jumps from `LOCAL_SAFE` to `PREDICTIVE` without undergoing `SHADOW_RECOVERY`.
6. **Shadow Validation Protocol**: Holds recovery state for 30 consecutive healthy seconds before promoting back to `PREDICTIVE`.

All transitions write structured records to `data/output/reliability/mode_transitions.csv`.
