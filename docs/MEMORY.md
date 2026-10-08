# TrafficTwin AI — Project Memory
Living file. Read first, update at end of every session. Keep under ~150 lines.

## Identity
Project: TrafficTwin AI · Event: AARAMBH WCE-HACKATHON 2026 · Problem: AI-Powered Traffic Flow Optimization.
Pitch: fail-operational traffic Digital Twin: predict congestion waves, test safe plans, prevent spillback, staged ambulance preemption with fairness recovery, confidence-aware fallback.

## Locked decisions
- WORKFLOW: module by module (M0–M13 in TASKS.md); push + tag only when a module's gate passes; one module per Antigravity prompt (template in GSD.md).
- GPS-first confirmed; camera/YOLO is a future optional adapter, not MVP. Perplexity "Product Scope Locked" video-first plan rejected (conflicts with submitted deck and 48-hour limit); its phase discipline and GitHub workflow adopted.
- Project name: TrafficTwin AI (renamed from FlowSync AI). Controller id: `traffictwin`. Tagline: Predict. Simulate. Protect. Recover.
- TIMELINE (current): 24 build-hours total, 5 people in parallel tracks. Block A (H0–H8, M0–M4) for R1 → tag r1-prototype; Block B (H8–H24, M5–M13) at the 48-hour event; rest of the event is buffer. Checkpoint A H18, freeze H22.
- Software only; SUMO + TraCI; 4 junctions (J1–J4); 6 only if stable.
- 3 control modes (Predictive, Safe Adaptive, Local Safe) + Shadow Recovery transition.
- Rule-based forecast; ML is P2; no deep RL.
- Lightweight queue-propagation twin; SUMO fork is stretch.
- Storage: CSV/JSON/SQLite, no PostgreSQL/Redis.
- UI: custom SVG corridor, 4 views (Live Control Room, Decision Log, Comparison, What-If Lab); health and reliability are panels.
- Horizon: 2–5 min rolling (state it honestly).
- Human approval is a toggle; auto-apply in sim by default.
- Pedestrians not modeled; emissions are an idle-time proxy.

## Default parameters (starting values, tune in SUMO)
MIN_GREEN 10 s · MAX_GREEN 45 s · YELLOW 3 s · ALL_RED 2 s · BUFFER 4 veh · MAX_WAIT 90 s · forecast H 180 s · TWIN_PERIOD 15 s · GPS_STALE_S 5 s · T_PRED 0.7 · T_LOCAL 0.4 · T_RESUME 0.8 · STABLE_S 30 s · veh length+gap 7.5 m.
Source of truth: `backend/config/params.yaml`.

## Glossary
Link, Spillback, Firewall, Trust, Fairness debt, Staged preemption, Recovery, Shadow Recovery, Local Safe (see SRS §2).

## Conventions
Event types: gps, link, junction, decision, mode. Controllers: fixed, reactive, traffictwin. Scenarios: normal, rush, blocked_downstream, ambulance, gps_outage.

## Current status
Docs: updated for Module M6 spillback controller. Code: M6 completed and verified (spillback-aware controller in experiments/spillback_controller.py and backend/app/controllers/spillback_controller.py, downstream capacity & occupancy calculation, rule-based NORMAL/WARNING/CRITICAL risk classification, downstream corridor mapping J1->J1_J2, J2->J2_J3, J3->J3_J4, J4->J4_E5, M3->M6->M5->TraCI execution flow, audit CSV decision logging, runner in experiments/run_spillback.py, demo in experiments/demo_spillback.py, docs in docs/M6_SPILLBACK.md, 13 new M6 tests, 95 total tests pass, ruff clean, bandit clean).
Results: Normal thru=197 avg_wait=13.5s; Rush thru=314 avg_wait=19.6s; Blocked Downstream thru=200 avg_wait=12.8s mean_queue=50.67 (1 SPILLBACK_BLOCK, 1 protected transition, peak occupancy=0.917); Ambulance thru=250 avg_wait=11.6s.

## Open questions
- Date gap between R1 and the event start; R1 slot length and whether demo is live or recorded.
- Whether pre-built R1 code is allowed in the 48-hour round (must ask; disclose either way).
- Team is 5 people (Spirit): roles A–E in ROLES.md; names to be assigned.
- Team role split (fill owners in TASKS.md).
- Demo hardware and display setup.

## Corrections log
- 2026-10-08: Aligned M5 firewall max_green_s from 45.0s to 40.0s matching project params.yaml, and inserted runtime validation gateway into M3 step_junction prior to TraCI actuation.
- 2026-10-08: Configured M6 spillback thresholds in params.yaml (warning=0.75, critical=0.85); verified fail-closed M5 firewall boundary for all M6 signal actions.

## Session log
- 2026-10-08: M0 completed (scaffolding, requirements.txt, .venv, verify_environment.py, smoke tests, ruff, bandit, pip-audit passed).
- 2026-10-08: M1 completed (corridor.net.xml with J1-J4 at 200m spacing, 6-phase safe cycles with all-red, 4 vehicle types, 4 scenarios with seed=42, headless & GUI verified, fallback_plan.json).
- 2026-10-08: M2 completed (run_fixed.py, tripinfo/queue/summary parsers, calc_metrics with 6 metrics+p95+emergency_delay, CSV exports, baseline chart, 24 tests pass). Normal: thru=194 avg_wait=20.0s. Rush: thru=338 avg_wait=26.2s.
- 2026-10-08: M3 completed (safe queue-reactive controller in experiments/reactive_controller.py, run_reactive.py with TraCI, bounded green extension, min/max green, yellow/all-red clearance, decision logs, reactive metrics CSVs, fixed vs reactive comparison chart, 45 tests pass). Normal: thru=197 avg_wait=13.5s. Rush: thru=314 avg_wait=19.6s.
- 2026-10-08: M4 completed (backend/app/stream/gps_event.py, shared/schemas/vehicle_position.schema.json, generate_gps_events.py, replay_gps.py, 4 scenario JSONL streams generated with 100% validity, 59 tests pass).
- 2026-10-08: M5 completed & verified (backend/app/guards/safety_firewall.py, backend/app/guards/__init__.py, runtime TraCI validation in experiments/reactive_controller.py, experiments/demo_safety_firewall.py, docs/M5_SAFETY_FIREWALL.md, 23 tests in tests/test_m5_firewall.py, 82 total tests pass, ruff clean, bandit clean).
- 2026-10-08: M6 completed & verified (experiments/spillback_controller.py, backend/app/controllers/spillback_controller.py, experiments/run_spillback.py, experiments/demo_spillback.py, docs/M6_SPILLBACK.md, 13 tests in tests/test_m6_spillback.py, 95 total tests pass, ruff clean, bandit clean, m6-ready tag).

