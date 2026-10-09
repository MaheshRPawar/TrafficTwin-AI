# Document 07 — Feature-by-Feature Engineering Guide

## 1. Feature Breakdown Matrix

This guide provides deep technical details for all 12 core capabilities implemented and verified in TrafficTwin AI.

---

### Feature 1: Four-Junction Corridor Monitoring
- **What It Does**: Continuously monitors the four signalized intersections ($J_1 \rightarrow J_2 \rightarrow J_3 \rightarrow J_4$) along the East-West arterial corridor.
- **Why It Is Needed**: Urban traffic operates as a coupled network; isolated intersection monitoring misses upstream-downstream shockwaves.
- **Implementation**: [`frontend/src/pages/OperatorDashboard.jsx`](file:///frontend/src/pages/OperatorDashboard.jsx), [`backend/app/main.py`](file:///backend/app/main.py)
- **API Endpoint**: `GET /api/corridor/state`, `GET /api/scenarios/{id}/junctions`
- **How to Demonstrate**: Switch between scenarios in the top bar. Observe live queue lengths, signal phase indicators, and downstream occupancy percentages updating for $J_1$ through $J_4$.

---

### Feature 2: Controller Comparison (Fixed vs. Reactive vs. Spillback vs. M9)
- **What It Does**: Provides side-by-side benchmark performance comparisons between 4 distinct control paradigms.
- **Why It Is Needed**: Proves to judges that TrafficTwin's multi-plan evaluation outperforms naive fixed-time and queue-actuated baselines.
- **Implementation**: [`experiments/run_fixed.py`](file:///experiments/run_fixed.py), [`experiments/run_reactive.py`](file:///experiments/run_reactive.py), [`experiments/run_spillback.py`](file:///experiments/run_spillback.py), [`experiments/run_planner.py`](file:///experiments/run_planner.py)
- **API Endpoint**: `GET /api/scenarios/{scenario_id}/summary`
- **What Judge Observes**: Under blocked downstream conditions, Fixed-Time suffers 78s average delay; Reactive suffers 82s delay; TrafficTwin M9 limits delay to 48s and reduces maximum queue from 38 down to 14 vehicles.

---

### Feature 3: Queue & Downstream Occupancy Monitoring
- **What It Does**: Measures both queue build-up on approach lanes and physical vehicular storage buffer on downstream egress links.
- **Why It Is Needed**: Approach queues show local demand; downstream occupancy reveals whether vehicles can physically exit the intersection.
- **Implementation**: [`experiments/reactive_controller.py`](file:///experiments/reactive_controller.py), [`experiments/spillback_controller.py`](file:///experiments/spillback_controller.py)
- **API Endpoint**: `GET /api/corridor/state` (fields `queue` and `downstream_occupancy`)
- **What Judge Observes**: In the Operator Dashboard, link $J_3\_J_4$ turns red with 88.7% occupancy when blocked downstream occurs.

---

### Feature 4: Spillback Detection & Protection (Module M6)
- **What It Does**: Intercepts and blocks upstream green extensions when the downstream link exceeds 85% storage capacity.
- **Why It Is Needed**: Prevents cross-street gridlock by refusing to dump more cars into an already saturated block.
- **Implementation**: [`backend/app/guards/spillback_guard.py`](file:///backend/app/guards/spillback_guard.py), [`experiments/demo_spillback.py`](file:///experiments/demo_spillback.py)
- **API Endpoint**: `GET /api/corridor/state` (`spillback_risk: "CRITICAL"`)
- **How to Demonstrate**: Run `python experiments/demo_spillback.py`. The console demonstrates how an upstream green request of $+5\text{s}$ is intercepted and cancelled by M6.

---

### Feature 5: Safety Firewall & Legal Phase Transitions (Module M5)
- **What It Does**: Enforces strict transportation safety invariants: minimum green (10s), maximum green (40s), yellow clearance (3s), and all-red clearance (2s).
- **Why It Is Needed**: Autonomous controllers must never cause vehicle collisions or violate legal yellow clearance timings.
- **Implementation**: [`backend/app/guards/safety_firewall.py`](file:///backend/app/guards/safety_firewall.py), [`experiments/demo_safety_firewall.py`](file:///experiments/demo_safety_firewall.py)
- **How to Demonstrate**: Run `python experiments/demo_safety_firewall.py`. Observe 4 test cases: early transition rejection ($<10\text{s}$), max green enforcement ($40\text{s}$), direct phase skip rejection, and legal yellow transition approval.

---

### Feature 6: Ambulance Priority, Downstream Gating & Staged Recovery (Module M7)
- **What It Does**: Senses approaching emergency vehicles, verifies downstream capacity before granting green, and coordinates recovery afterward.
- **Why It Is Needed**: Giving an ambulance green into a gridlocked downstream link traps the ambulance. Downstream gating flushes the link first.
- **Implementation**: [`experiments/emergency_controller.py`](file:///experiments/emergency_controller.py), [`experiments/run_ambulance.py`](file:///experiments/run_ambulance.py)
- **What Judge Observes**: In Scenario `ambulance`, the system detects `amb_1` (ETA 12.4s), triggers `DOWNSTREAM_CLEARANCE` at $J_2$, and clears link $J_2\_J_3$ so the ambulance maintains free-flow speed.

---

### Feature 7: Fairness Debt & Starvation-Risk Handling (Module M7)
- **What It Does**: Accumulates waiting debt for cross-street traffic and forces green service if debt exceeds 30.0 seconds.
- **Why It Is Needed**: Arterial green extensions must not starve pedestrians or minor cross-street drivers indefinitely.
- **Implementation**: [`experiments/emergency_controller.py`](file:///experiments/emergency_controller.py)
- **What Judge Observes**: Audit events log cross-street debt accumulation. When starvation threshold is approached, Plan A/B penalties spike, forcing transition to cross-street service.

---

### Feature 8: Fail-Safe State Transitions & Recovery (Module M8)
- **What It Does**: Implements a 3-state Finite State Machine: `PREDICTIVE` $\rightarrow$ `DEGRADED` $\rightarrow$ `FAIL_SAFE`.
- **Why It Is Needed**: If sensor telemetry drops or the digital twin solver crashes, the hardware must fall back to fail-safe fixed coordination.
- **Implementation**: [`backend/app/reliability/fail_safe.py`](file:///backend/app/reliability/fail_safe.py)
- **What Judge Observes**: If stream heartbeat is lost for $>5.0\text{s}$, status shifts to `DEGRADED`. After 3 consecutive timeouts, the system falls back to `FAIL_SAFE` (flashing yellow / fixed-time default).

---

### Feature 9: Digital Twin Plan A/B/C Evaluator (Module M9)
- **What It Does**: Simultaneously evaluates 3 candidate plans (Plan A Progression, Plan B Queue Extension, Plan C Downstream Clearing) using weighted multi-objective scoring.
- **Why It Is Needed**: Explains exactly *why* an alternative was chosen and *why* other options were rejected.
- **Implementation**: [`backend/app/planner/evaluator.py`](file:///backend/app/planner/evaluator.py)
- **API Endpoint**: `GET /api/corridor/state` (`selected_plan` object)
- **What Judge Observes**: In the Operator Dashboard, the Plan Scorecard shows Plan C winning with score 28.5, while Plan B is explicitly marked `REJECTED (M6 Spillback Violation)`.

---

### Feature 10: Simulation Metrics & Audit Trail
- **What It Does**: Records an immutable, chronologically-ordered ledger of all operational decisions, firewall approvals, and operator authorizations.
- **Why It Is Needed**: Traffic operations require 100% auditability for insurance, legal compliance, and incident investigations.
- **Implementation**: [`backend/app/main.py`](file:///backend/app/main.py)
- **API Endpoint**: `GET /api/audit-events`
- **What Judge Observes**: A timestamped table in the Operator Dashboard showing events like `AUD-004: M6 Spillback Intercept`, `AUD-005: Plan C Selection`, `AUD-006: M5 Firewall Validation`.

---

### Feature 11: Operator & Public View Separation
- **What It Does**: Enforces strict privilege boundaries between traffic engineers (`/`) and commuting citizens (`/public`).
- **Why It Is Needed**: Protects critical signal infrastructure from unauthorized actuation while keeping the public informed.
- **Implementation**: [`frontend/src/pages/PublicDashboard.jsx`](file:///frontend/src/pages/PublicDashboard.jsx), [`backend/app/main.py`](file:///backend/app/main.py)
- **API Security**: `POST /api/recommendations/{id}/approve-simulation` rejects `VIEWER` with HTTP 403 Forbidden.

---

### Feature 12: Repeatable Multi-Scenario Demo Workflow
- **What It Does**: Provides one-click repeatable execution of Normal, Rush, Blocked Downstream, and Ambulance simulations with zero state corruption.
- **Why It Is Needed**: Ensures the demo runs reliably under live hackathon judging pressure.
- **Implementation**: [`run.bat`](file:///run.bat), [`launch_sumo_gui.bat`](file:///launch_sumo_gui.bat), [`experiments/run_planner.py`](file:///experiments/run_planner.py)
