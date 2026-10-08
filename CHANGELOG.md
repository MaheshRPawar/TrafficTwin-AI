# Changelog

All notable changes to TrafficTwin AI are documented in this file.

The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-10-08

### Core MVP Release — Complete Local Decision-Support Platform (Modules M0–M11)

#### Module M9 — Digital Twin Plan A/B/C Evaluator
- **Deterministic Counterfactual Evaluator:** Evaluates candidate signal strategies in the local Digital Twin prior to recommendation.
  - **Plan A (Current Timing):** Continues current safe timing schedule.
  - **Plan B (Bounded Extension):** Proposes a bounded $+5\,\text{s}$ green extension, strictly constrained by $\text{max\_green} = 40\,\text{s}$, yellow $= 3\,\text{s}$, all-red $= 2\,\text{s}$, and downstream capacity.
  - **Plan C (Downstream Clearing & Coordination):** Proactively prioritizes downstream arterial clearance, coordinates corridor offsets, and clears spillback-prone links.
- **Explicit Scoring Engine:**
  $$\text{PlanScore} = 1.0 \cdot \text{delay} + 2.0 \cdot \text{queue} + 3.0 \cdot \text{spillback} + 1.5 \cdot \text{fairness} + 5.0 \cdot \text{emergency}$$
- **Fail-Safe Fallback:** If all candidate plans violate safety or capacity constraints, the evaluator safely falls back to `SAFE_ADAPTIVE` without crashing.
- **CLI Runner & Experiments:** Added `experiments/run_planner.py` with reproducible evaluation runs across `normal`, `rush_hour`, `blocked_downstream`, and `ambulance` scenarios.

#### Module M10 — FastAPI Backend + Operator Dashboard Integration
- **REST Endpoints:**
  - `GET /health` & `GET /api/health` — System status, controller mode, active scenario, and subsystem health.
  - `GET /api/corridor/state` — Live 4-junction telemetry (J1–J4 queue lengths, phase states, downstream occupancies, spillback risks, fairness debt, emergency status, active recommendation).
  - `GET /api/recommendations/current` — Detailed decision payload with proposed action, M3 reactive intent, M6 downstream guard result, M5 firewall validation, M7 emergency state, and M9 selected plan.
  - `GET /api/audit-events` — Immutable audit log of all system decisions, safety firewall checks, fail-safe transitions, and operator actions.
  - `GET /api/replay` — Recorded simulation traces across all 4 scenarios for deterministic playback.
  - `POST /api/recommendations/{id}/approve-simulation` — Role-gated recommendation approval endpoint.
- **Local Role-Based Access Control (RBAC):**
  - `VIEWER` (Read-only, 403 Forbidden on approval).
  - `OPERATOR` (Authorized to approve pre-validated recommendations).
  - `ADMIN` (Authorized to approve and manage system configuration).
- **Security & Integrity:**
  - Raw TraCI commands and arbitrary user-generated phase injections are strictly rejected.
  - Only recommendations that have already cleared M5, M6, and M7 can be approved.
- **Industrial Control Room UI:**
  - Integrated with React + Vite frontend maintaining the clean light aesthetic.
  - Plan A/B/C scorecard with component breakdown.
  - React Flow decision pipeline diagram (Traffic State $\rightarrow$ M3 $\rightarrow$ M7 $\rightarrow$ M6 $\rightarrow$ M9 $\rightarrow$ M5 $\rightarrow$ Signal).
  - Recharts for queue lengths, downstream occupancy, plan score comparisons, and recovery timelines.

#### Module M11 — Verification, Security Hardening & Evidence Pack
- **Integration Test Suite:** 142 automated tests passing (`pytest` with 100% pass rate).
- **Security Audit:** `bandit` scan clean (0 vulnerabilities), `pip-audit` clean (0 known CVEs).
- **Code Hygiene:** Full compliance with `ruff` linting and formatting.
- **Offline & Local-First:** Complete decision engine and dashboard operate locally without cloud dependencies.

---

### Previous Modules (M0–M8 Foundation)
- **M0–M1:** Four-junction synchronized arterial SUMO corridor (J1–J4) with calibrated demand flows.
- **M2:** Fixed-time baseline controller with comprehensive queue and travel-time metrics.
- **M3:** Queue-reactive controller with bounded green extensions ($10\,\text{s} \le g \le 40\,\text{s}$).
- **M4:** Deterministic GPS/telematics stream pipeline with replay engine.
- **M5:** Signal Safety Firewall enforcing phase sequencing, clearance intervals, and conflicting movement isolation.
- **M6:** Spillback-aware controller guarding downstream link capacity ($\ge 85\%$ occupancy lock).
- **M7:** Cross-street fairness debt tracking, staged ambulance preemption, and post-emergency recovery.
- **M8:** Multi-mode fail-safe reliability manager (`PREDICTIVE` $\leftrightarrow$ `SAFE_ADAPTIVE` $\leftrightarrow$ `LOCAL_SAFE` $\leftrightarrow$ `SHADOW_RECOVERY`).
