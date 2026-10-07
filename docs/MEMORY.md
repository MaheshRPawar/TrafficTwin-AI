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
Docs: updated for the 24-hour module-by-module plan. Code: M2 completed and verified (fixed-time baseline runner, tripinfo/queue/summary parsers, 6 metrics, 4 scenario CSVs, one chart).
Results: none yet. Do not quote any numbers until runs exist.

## Open questions
- Date gap between R1 and the event start; R1 slot length and whether demo is live or recorded.
- Whether pre-built R1 code is allowed in the 48-hour round (must ask; disclose either way).
- Team is 5 people (Spirit): roles A–E in ROLES.md; names to be assigned.
- Team role split (fill owners in TASKS.md).
- Demo hardware and display setup.

## Corrections log
- (add user corrections here, e.g. "too verbose", "off-format") 

## Session log
- 2026-10-08: M0 completed (scaffolding, requirements.txt, .venv, verify_environment.py, smoke tests, ruff, bandit, pip-audit passed).
- 2026-10-08: M1 completed (corridor.net.xml with J1-J4 at 200m spacing, 6-phase safe cycles with all-red, 4 vehicle types, 4 scenarios with seed=42, headless & GUI verified, fallback_plan.json).
- 2026-10-08: M2 completed (run_fixed.py, tripinfo/queue/summary parsers, calc_metrics with 6 metrics+p95+emergency_delay, CSV exports, baseline chart, 24 tests pass). Normal: thru=194 avg_wait=20.0s. Rush: thru=338 avg_wait=26.2s. Next: M3 GPS stream.
