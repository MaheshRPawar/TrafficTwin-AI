# Module M5 — Signal Safety Firewall

## 1. Purpose

The Signal Safety Firewall is an independent safety validation layer in TrafficTwin AI. It acts as an authoritative gateway: every proposed signal-control action must pass validation before it can be applied to any junction in the corridor.

```
Proposed Signal Action
         ↓
  Safety Firewall (M5)
    ├── Valid Junction?
    ├── Valid Phase (0-5)?
    ├── Valid Action?
    ├── Clearance Phase Restriction?
    ├── Minimum Green Elapsed?
    ├── Maximum Green Bounded?
    ├── Yellow Clearance Respected?
    ├── All-Red Clearance Respected?
    └── Conflicting Movements Protected?
         ↓
   PASS (allowed: true)  → Action executed
   FAIL (allowed: false) → Action rejected + specific reason logged
```

The firewall adheres to the **FAIL-CLOSED** principle: if an action cannot be proven safe, it is rejected immediately.

---

## 2. Proposed Action & Result Interface

### Input Schema

```python
{
    "junction_id": "J1",            # Required: "J1", "J2", "J3", or "J4"
    "current_phase": 0,             # Required: int (0 to 5)
    "requested_phase": 1,           # Optional: int (0 to 5) or None
    "action": "START_TRANSITION",   # Required: "KEEP_GREEN", "EXTEND_GREEN", "START_TRANSITION", "HOLD"
    "timestamp": 120.0,             # Optional: float simulation time
    "elapsed_green_s": 25.0,        # Optional: time spent in active green phase
    "extension_s": 5.0,             # Optional: extension duration for EXTEND_GREEN
    "reason": "cross_queue_demand", # Optional: motivation from upstream controller
}
```

### Validation Result

```python
# On Approval:
{
    "allowed": True,
    "reason": "valid_transition",   # or "valid_action"
    "junction_id": "J1",
    "current_phase": 0,
    "requested_phase": 1,
}

# On Rejection:
{
    "allowed": False,
    "reason": "minimum_green_not_reached",
    "junction_id": "J1",
    "current_phase": 0,
    "requested_phase": 1,
}
```

---

## 3. Actual Signal Phases (4-Junction Corridor)

Inspected directly from `sumo/net/corridor.tll.xml`:

| Phase ID | Name | Duration | Signal State (`rrrrGGGggrrrrGGGgg` style) | Movement |
|---|---|---|---|---|
| **0** | `MAIN_GREEN` | 30s (default) | `rrrrGGGggrrrrGGGgg` | East-West Arterial Green |
| **1** | `MAIN_YELLOW` | 3s (clearance) | `rrrryyyyyrrrryyyyy` | Arterial Yellow Change |
| **2** | `ALL_RED_1` | 2s (clearance) | `rrrrrrrrrrrrrrrrrr` | Intersection Clearance All-Red |
| **3** | `CROSS_GREEN` | 20s (default) | `GGggrrrrrGGggrrrrr` | North-South Cross Street Green |
| **4** | `CROSS_YELLOW` | 3s (clearance) | `yyyyrrrrryyyyrrrrr` | Cross Street Yellow Change |
| **5** | `ALL_RED_2` | 2s (clearance) | `rrrrrrrrrrrrrrrrrr` | Intersection Clearance All-Red |

---

## 4. Legal Phase Progression

Transitions must strictly follow the cyclic progression:

$$0 \longrightarrow 1 \longrightarrow 2 \longrightarrow 3 \longrightarrow 4 \longrightarrow 5 \longrightarrow 0$$

- Green phases are **0** and **3**.
- Clearance intervals are **1**, **2**, **4**, and **5**.
- Conflicting green pair: **(0, 3)** (Main Arterial vs Cross Street).

---

## 5. Safety Checks & Specific Rejection Reasons

| Check | Condition | Rejection Reason |
|---|---|---|
| **Junction Check** | `junction_id` not in `["J1", "J2", "J3", "J4"]` | `invalid_junction` |
| **Phase Number Check** | `current_phase` or `requested_phase` not in `0..5` | `invalid_phase` |
| **Action Check** | `action` not in `["KEEP_GREEN", "EXTEND_GREEN", "START_TRANSITION", "HOLD"]` | `invalid_action` |
| **Clearance Restriction** | Requesting `EXTEND_GREEN` or `KEEP_GREEN` during clearance phases (`1, 2, 4, 5`) | `action_not_valid_for_clearance_phase` |
| **Conflict Protection** | Direct jump between conflicting greens (`0 ↔ 3`) without clearance | `conflicting_phase` |
| **Yellow Clearance** | Direct jump from green to all-red (`0 → 2` or `3 → 5`) skipping yellow | `yellow_clearance_required` |
| **All-Red Clearance** | Direct jump from yellow to green (`1 → 3` or `4 → 0`) skipping all-red | `all_red_clearance_required` |
| **Legal Progression** | Any non-consecutive phase jump (e.g. `0 → 4`, `2 → 5`) | `illegal_phase_transition` |
| **Minimum Green** | Attempting to terminate green before `min_green_s` (10s) elapses | `minimum_green_not_reached` |
| **Maximum Green** | Green extension exceeding `max_green_s` (40s project cap) | `maximum_green_exceeded` |

---

## 6. Audit Logging

Every decision validated by the firewall is loggable to CSV:

```csv
timestamp,junction_id,current_phase,requested_phase,action,allowed,reason
15.0,J1,0,0,KEEP_GREEN,True,valid_action
6.0,J2,0,1,START_TRANSITION,False,minimum_green_not_reached
25.0,J3,0,3,START_TRANSITION,False,conflicting_phase
43.0,J4,0,0,EXTEND_GREEN,False,maximum_green_exceeded
20.0,J2,0,1,START_TRANSITION,True,valid_transition
```

Logging helper:
```python
from backend.app.guards.safety_firewall import log_firewall_decision

log_firewall_decision(result_record, output_path="data/output/safety/firewall_decisions.csv")
```

---

## 7. How Downstream Modules Will Use M5

1. Upstream controllers (M6 Spillback, M7 Preemption/Fairness, M9 Digital Twin) formulate a candidate action dictionary.
2. Before calling TraCI or actuating signals, they pass the action to `validate_action(action)`.
3. If `allowed == True`: the action is applied.
4. If `allowed == False`: the controller discards the proposal and retains the safe default (e.g., maintaining clearance or holding green until min green expires).

---

## 8. Scope Boundary & Important Limitations

> **M5 validates signal safety only.**  
> - Downstream link capacity and spillback queue prediction belong to **M6**.  
> - Fairness tracking, emergency vehicle preemption, and cycle recovery belong to **M7**.  
> - Fail-safe fallback controllers and watchdog heartbeats belong to **M8**.
