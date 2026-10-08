# Module M9: Digital Twin Plan A/B/C Evaluator

## Executive Summary
Module M9 introduces the **Digital Twin Decision Support Evaluator** for the TrafficTwin AI platform. Before actuating any signal control recommendation, the system formulates and deterministically evaluates three discrete candidate control strategies (Plan A, Plan B, and Plan C) against live corridor snapshots. 

Every candidate plan is strictly verified through the **M5 Signal Safety Firewall** and **M6 Downstream Capacity Guard**. Invalid alternatives are discarded, and the lowest valid scoring alternative is selected with a full transparent decision trace.

---

## Candidate Plan Definitions

| Plan | Strategy Name | Operational Logic | Key Constraints |
| :--- | :--- | :--- | :--- |
| **Plan A** | *Current Safe Timing* | Maintains standard cycle progression and current phase timing without modification. | Validated against clearance intervals and minimum green. |
| **Plan B** | *Bounded Green Extension* | Injects $+5.0\text{s}$ green extension on heavily queued approaches ($\ge 3\text{ veh}$). | Bounded by $40.0\text{s}$ maximum green ceiling. **Strictly rejected by M6 if downstream occupancy $\ge 85\%$**. |
| **Plan C** | *Downstream Clearing & Corridor Coordination* | Proactively transitions upstream approaches to yellow/red and coordinates green waves to clear downstream bottlenecks. | Highest spillback mitigation. Coordinates Eastbound progression for emergency and heavy bottleneck relief. |

---

## Mathematical Scoring Formula
All plans are evaluated using a deterministic, transparent composite cost function:

$$\text{PlanScore} = w_{\text{delay}} \cdot \text{DelayScore} + w_{\text{queue}} \cdot \text{QueueScore} + w_{\text{spillback}} \cdot \text{SpillbackPenalty} + w_{\text{fairness}} \cdot \text{FairnessPenalty} + w_{\text{emergency}} \cdot \text{EmergencyPenalty}$$

### Authoritative Scoring Weights
Configured in `backend/config/params.yaml`:
- $w_{\text{delay}} = 1.0$: Aggregate waiting vehicle delay.
- $w_{\text{queue}} = 2.0$: Penalty for unserved approach queues.
- $w_{\text{spillback}} = 3.0$: Heavy penalty for releasing flow into saturated downstream links ($\ge 75\%$ warning, $\ge 85\%$ critical).
- $w_{\text{fairness}} = 1.5$: Penalty for neglected side-street debt.
- $w_{\text{emergency}} = 5.0$: Severe penalty for blocking active emergency preemption.

Lower score indicates a superior operational decision.

---

## Safety & Fallback Guarantees
1. **Safety Firewall Verification**: Plans proposing transitions before $10.0\text{s}$ minimum green or exceeding $40.0\text{s}$ maximum green are marked `is_valid = False` and rejected.
2. **Spillback Protection (M6)**: Plan B (Green Extension) is automatically invalidated on Phase 0 if downstream occupancy exceeds $85\%$.
3. **Planner Exception Fail-Safe**: In the event of planner failure, data corruption, or if all candidates are invalid, the evaluator automatically returns a `SAFE_ADAPTIVE` recommendation without throwing exceptions or stalling corridor actuation.

---

## Empirical Verification
Executed via `experiments/run_planner.py --all`:
- **Rush Hour**: Plan C was selected during bottleneck peaks to prevent gridlock propagation; Plan B was selected during isolated queue bursts.
- **Blocked Downstream**: Plan C successfully cleared upstream inflows at J3 while downstream link J3_J4 was saturated.
- **Ambulance**: Emergency preemption automatically coordinated corridor progression with zero clearance violations.
- **Artifacts Saved**: `data/output/metrics/planner_*_summary.csv` and `data/output/safety/planner_*_decisions.csv`.
