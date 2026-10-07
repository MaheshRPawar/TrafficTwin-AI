# TrafficTwin AI — Software Requirements Specification (SRS)
Version 1.0 · Conforms in spirit to IEEE 29148 (lean form)

## 1. Scope
Software system that connects to a SUMO simulation via TraCI, estimates traffic state, forecasts congestion, selects safe signal actions for 4 junctions (J1–J4), exposes live state to a web dashboard, and records metrics. Out of scope: hardware, real controllers, pedestrians (not modeled).

## 2. Definitions
Link = directed road segment between junctions. Spillback = queue on a link reaching its upstream junction box or ≥ SPILLBACK_OCC occupancy. Firewall = validator between any controller and TraCI. Trust = GPS data quality score 0–1.

## 3. Functional requirements
IDs: FR-<module>-<n>. Priority P0/P1/P2.

### 3.1 Simulation & data stream (SIM)
- FR-SIM-1 (P0) Run named scenario with fixed seed and fixed route file via TraCI at 1 s step.
- FR-SIM-2 (P0) Emit GPS-like events per vehicle every 2 s: vehicle_id, vehicle_type(car|taxi|bus|ambulance), ts, edge, lane_pos, x, y, speed, heading, route_id.
- FR-SIM-3 (P0) Event source behind an adapter interface so a real feed can replace SUMO.
- FR-SIM-4 (P1) Inject faults: gps_outage, ml_fail, network_loss, with duration.

### 3.2 State estimator (EST)
- FR-EST-1 (P0) Per link every 1 s: vehicles, capacity, free_capacity, queue_len, avg_speed, density, avg_wait, arrival_rate.
- FR-EST-2 (P0) Per junction: phase, phase_age, signal state (green|yellow|all_red), per-approach wait.
- FR-EST-3 (P0) Track bus and ambulance positions.
- FR-EST-4 (P1) Compute Trust per link from freshness, missing rate, coverage, speed consistency, duplicates, latency.

### 3.3 Forecast (PRD)
- FR-PRD-1 (P0) Per link risk in [0,1] for horizon H (default 180 s) using rule-based wave propagation: inflow = released vehicles delayed by link travel time; risk = (vehicles + inflow − expected outflow) / capacity.
- FR-PRD-2 (P0) Label each link Low/Moderate/High (thresholds in params.yaml).
- FR-PRD-3 (P1) Report forecast error vs actual for past decisions.

### 3.4 Controllers (CTL)
- FR-CTL-1 (P0) Fixed-time controller with stored safe cycle.
- FR-CTL-2 (P0) Queue-reactive controller (baseline, no prediction).
- FR-CTL-3 (P0) TrafficTwin controller = reactive candidate + downstream guard + fairness debt + firewall.
- FR-CTL-4 (P0) Downstream guard: permit release only if free_capacity ≥ expected_released + BUFFER; else block and log.
- FR-CTL-5 (P0) Fairness: D_i = α·avg_wait + β·max_wait + γ·missed_cycles; force service when max_wait > MAX_WAIT (except emergency).
- FR-CTL-6 (P1) Bus priority only if bus late > threshold AND downstream safe AND fairness within limit; bounded to BUS_MAX_EXT seconds.
- FR-CTL-7 (P0) Ambulance staged preemption: ETA per junction; if downstream not clear, clear it first; green staged by ETA window, not all junctions green.
- FR-CTL-8 (P0) Recovery: after ambulance passes, allocate bounded recovery green to delayed cross approaches; log duration and effect.

### 3.5 Safety firewall (FW)
Every action must pass; any failure rejects action and falls back to the stored plan step.
- FR-FW-1 min green · FR-FW-2 max green · FR-FW-3 yellow + all-red clearance · FR-FW-4 no conflicting greens · FR-FW-5 valid phase transition graph · FR-FW-6 downstream capacity · FR-FW-7 fairness limit · FR-FW-8 emergency policy · FR-FW-9 log every verdict (all P0).

### 3.6 Digital Twin (TWN) — P1
- FR-TWN-1 Snapshot link/junction state from the live sim.
- FR-TWN-2 Generate up to 3 valid candidates (A continue, B extend busiest safe phase, C clear downstream first / transit / recovery as applicable).
- FR-TWN-3 Evaluate each over short horizon (default 60–120 s) with the lightweight queue-propagation model.
- FR-TWN-4 PlanScore = w1·delay + w2·max_queue + w3·spillback_risk + w4·emergency_delay + w5·bus_delay + w6·fairness_penalty + w7·idle_emission; lowest wins. Weights in params.yaml.
- FR-TWN-5 Return all scores and the chosen plan with explanation.

### 3.7 Reliability (REL)
- FR-REL-1 (P0) Modes: Predictive, Safe Adaptive, Local Safe; plus Shadow Recovery transition.
- FR-REL-2 (P0) Local Safe when no GPS ≥ GPS_STALE_S, ML failure, unsafe command, or comms lost; use stored plan in `fallback_plan.json`.
- FR-REL-3 (P1) Safe Adaptive when Trust < T_PRED and ≥ T_LOCAL: deterministic queue+guard+fairness, no forecast.
- FR-REL-4 (P1) Shadow Recovery: AI computes silently; resume Predictive after STABLE_S seconds of Trust ≥ T_RESUME and zero firewall rejects.
- FR-REL-5 (P0) Emit mode event with reason on every transition.

### 3.8 Explainability (EXP)
- FR-EXP-1 (P0) Each decision produces a card: action, reasons[], checks{}, predicted effect, measured effect after 60 s (filled later).

### 3.9 Metrics (MET)
- FR-MET-1 (P0) Log per run to CSV: all metrics in PRD §8, with scenario, controller, seed.
- FR-MET-2 (P0) Experiment runner executes controller × scenario × seed matrix with identical route files.
- FR-MET-3 (P0) Summary table generated from CSV only.

### 3.10 API & dashboard (API/UI)
- FR-API-1 (P0) WebSocket `/ws/live` streaming gps, link, junction, decision, mode events.
- FR-API-2 (P0) REST: start scenario, inject fault, approve decision, get metrics, list decisions, health.
- FR-UI-1 (P0) Live Control Room · FR-UI-2 (P0) Decision Log · FR-UI-3 (P0) Controller Comparison · FR-UI-4 (P1) What-If Lab · FR-UI-5 (P1) reliability and trust panels.

### 3.11 Security, roles and audit (SEC)
- FR-SEC-1 (P0) Approval endpoint requires an authenticated Operator/Admin; Viewer or no credential ⇒ HTTP 403; unknown recommendation ⇒ 404.
- FR-SEC-2 (P0) Approval mode config `approval_mode = auto | manual`; demo shows one manual approval; the approved action still passes the firewall.
- FR-SEC-3 (P0) All API input validated (pydantic); invalid ⇒ 422, never reaches TraCI.
- FR-AUD-1 (P0) Every recommendation, approval, rejection, action, mode change and fault is written to an append-only audit JSONL (SQLite optional) before and after application.
- FR-SEC-4 (P1) Local demo accounts with hashed passwords and signed token; Admin role P2.

## 4. Non-functional requirements
- NFR-1 Control decision latency ≤ 200 ms per junction per step (measured, reported).
- NFR-2 Dashboard update ≤ 1 s behind sim; throttle to 1 Hz state, 0.5 Hz GPS.
- NFR-3 Determinism: same seed + scenario + controller ⇒ same metrics (± float tolerance).
- NFR-4 Safety: zero firewall-invalid commands reach TraCI (tested).
- NFR-5 Resilience: killing the feed or the ML module never halts signals.
- NFR-6 Portability: runs on Windows/Linux/macOS with native SUMO, Python 3.11+, Node LTS.
- NFR-8 Security: no secrets in git; ruff, pytest, bandit, pip-audit run and results saved; dashboard never calls TraCI.
- NFR-9 Testability: decision and safety logic unit-testable without launching UI or SUMO GUI.
- NFR-7 Honesty: UI labels data "simulated GPS"; no hard-coded result numbers anywhere.

## 5. Interfaces
Schemas live in `shared/schemas/*.json`; see ARCHITECTURE §6 for event shapes. TraCI used for vehicle/edge/lane/trafficlight reads and phase/duration writes.

## 6. Constraints
Software only; open-source tools; SUMO + TraCI; no proprietary data; licence-respecting reuse recorded in THIRD_PARTY_NOTICES.md.

## 7. Acceptance criteria (system level)
- AC-1 All three controllers run on every scenario with identical demand.
- AC-2 Blocked-downstream scenario: TrafficTwin logs ≥1 "downstream full" block and spillback count is reported against baselines.
- AC-3 Ambulance run: staged greens visible, downstream cleared first when blocked, recovery logged.
- AC-4 Fault injection switches to Local Safe within GPS_STALE_S + 1 s and traffic keeps moving.
- AC-5 Shadow Recovery returns to Predictive only after the stability window.
- AC-6 Firewall unit tests pass; replay of a full run shows 0 invalid commands.

## 7a. Release mapping
R1 (online, Block A): FR-SIM-1,2 · FR-EST-1,2 · FR-CTL-1,2 · FR-MET-1,2,3 · FR-API-3 (replay) · FR-UI-1 (replay). Optional: FR-CTL-4, FR-PRD-1.
Event (Block B): all other P0, then P1 in the order given in TASKS.md. Under time pressure, P1 may be reduced: Safe Adaptive = reactive + guard + fairness; Shadow Recovery = timer-based; trust = freshness + coverage only; Twin = Plan A/B/C lite.
Added: FR-API-3 (P0, R1) Dashboard replay mode reads recorded events from `data/recorded/` using the same schemas as the live stream, with no SUMO required.

## 8. Traceability
| Official requirement | FRs | Tests |
|---|---|---|
| GPS ingestion | SIM-2,3 | T-SIM |
| Congestion prediction | PRD-1,2 | T-PRD |
| Dynamic signals | CTL-3, FW-* | T-FW |
| Multi-junction | CTL-4, CTL-7 | T-GUARD, T-AMB |
| Measurable comparison | MET-* | T-MET |
| Safe fallback | REL-* | T-REL |
