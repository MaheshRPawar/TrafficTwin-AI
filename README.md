# TrafficTwin AI

> **Aarambh WCE Hackathon 2026 — Complete Core MVP (Modules M0–M11)**  
> **A Local-First, Simulation-Based Decision Support Platform for Arterial Corridor Control**

---

## Overview

TrafficTwin AI is an authority-facing traffic control decision-support platform that couples a deterministic **Eclipse SUMO Digital Twin** with a **multi-layer safety and optimization pipeline**.

Before any signal action is recommended or simulated, candidate strategies are evaluated counterfactually against physical constraints, downstream capacities, cross-street starvation thresholds, emergency priority directives, and an immutable Signal Safety Firewall.

```
Traffic State (J1–J4)
       │
       ▼
[M3] Queue-Reactive Proposer
       │
       ▼
[M7] Fairness & Emergency Directives
       │
       ▼
[M6] Spillback Capacity Guard (85% occupancy threshold)
       │
       ▼
[M9] Digital Twin Plan Evaluator (Plan A vs B vs C scoring)
       │
       ▼
[M5] Signal Safety Firewall (10s min green, clearance, conflicts)
       │
       ▼
SUMO Actuation / Operator Approval / TraCI
```

---

## Key Features

### 1. Four-Junction Synchronized Corridor (M1–M2)
- Models arterial intersections **J1 $\rightarrow$ J2 $\rightarrow$ J3 $\rightarrow$ J4** with calibrated main arterial and cross-street flows.
- Baseline fixed-time benchmarked against adaptive strategies.

### 2. Queue-Reactive & Spillback-Aware Control (M3, M6)
- Bounded green extension ($10\,\text{s} \le \text{green} \le 40\,\text{s}$).
- Real-time downstream link capacity tracking. Proactively suppresses upstream green extensions when downstream occupancy reaches $\ge 85\%$ to prevent gridlock.

### 3. Cross-Street Fairness & Ambulance Preemption (M7)
- **Fairness Debt Tracking:** Prevents cross-street starvation by enforcing priority when debt exceeds threshold.
- **Staged Emergency Preemption:** Detects emergency vehicles, clears downstream queues, grants priority green, and enters a graceful post-emergency recovery cycle.

### 4. Reliability & Fail-Safe Architecture (M8)
- Four-stage operational state machine:
  $$\text{PREDICTIVE} \longleftrightarrow \text{SAFE\_ADAPTIVE} \longleftrightarrow \text{LOCAL\_SAFE} \longleftrightarrow \text{SHADOW\_RECOVERY}$$
- Automated graceful degradation upon telemetry lag, sensor loss, or controller timeouts.

### 5. Digital Twin Counterfactual Planner (M9)
- Real-time deterministic evaluation of candidate plans:
  - **Plan A:** Current safe schedule.
  - **Plan B:** Bounded green extension (+5s).
  - **Plan C:** Downstream link clearing and coordinated arterial clearance.
- Transparent scoring formula:
  $$\text{PlanScore} = 1.0 \cdot \text{delay} + 2.0 \cdot \text{queue} + 3.0 \cdot \text{spillback} + 1.5 \cdot \text{fairness} + 5.0 \cdot \text{emergency}$$
- Selects the lowest-scoring valid candidate; safely defaults to `SAFE_ADAPTIVE` if all plans violate safety rules.

### 6. Operator Control Room & REST API (M10)
- **FastAPI Endpoints:** Real-time corridor telemetry, recommendation details, immutable audit logs, and replay traces.
- **Local RBAC:** `VIEWER` (read-only), `OPERATOR` (authorized approval), and `ADMIN`.
- **Security Guarantee:** Rejects raw TraCI commands or unvalidated phase injections. Only pre-validated recommendations can be approved.
- **Industrial Dashboard:** Clean, light transportation engineering aesthetic with Recharts analytics and React Flow decision visualization.

---

## System Boundaries & Operational Context

- **Simulation-Based:** Built on Eclipse SUMO and TraCI.
- **Local-First & Offline:** Functions entirely without cloud or external network dependencies.
- **Authority-Facing:** Designed as decision-support for traffic engineers and operators, not public end-user routing.
- **Not Live Municipal Control:** Simulation testbed demonstrating deterministic safety constraints prior to physical hardware deployment.

---

## Quick Start Guide

### Prerequisites
- Python 3.10+ (with Eclipse SUMO installed and `SUMO_HOME` configured)
- Node.js 18+ and npm

### 1. Backend Setup & Test Suite
```bash
# Clone repository
git clone https://github.com/MaheshRPawar/TrafficTwin-AI.git
cd TrafficTwin-AI

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Linux/macOS: source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run full test suite (142 tests)
pytest -v

# Run linters and security checks
ruff check .
bandit -r backend experiments
pip-audit
```

### 2. Run Offline Experiments & Benchmarks
```bash
# Run Digital Twin Planner across scenarios
python experiments/run_planner.py --scenario normal
python experiments/run_planner.py --scenario rush_hour
python experiments/run_planner.py --scenario blocked_downstream
python experiments/run_planner.py --scenario ambulance
```

### 3. Launch Backend API
```bash
# Start FastAPI service on port 8000
python -m uvicorn backend.app.main:app --reload --port 8000
```

### 4. Launch Operator Frontend
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## REST API Overview

| Endpoint | Method | Role Required | Description |
| :--- | :---: | :---: | :--- |
| `/health` | `GET` | Any | Subsystem health, controller mode, active scenario |
| `/api/corridor/state` | `GET` | Any | 4-junction live states (queues, phases, occupancy) |
| `/api/recommendations/current` | `GET` | Any | Active recommendation and full pipeline trace |
| `/api/audit-events` | `GET` | Any | Immutable decision audit history |
| `/api/replay` | `GET` | Any | Recorded simulation traces across scenarios |
| `/api/recommendations/{id}/approve-simulation` | `POST` | `OPERATOR`, `ADMIN` | Authorizes an existing pre-validated recommendation (`VIEWER` returns 403) |

---

## Judge Demonstration Flow

1. **Corridor Overview:** View J1–J4 synchronized corridor with real-time queue lengths and phase indicators.
2. **Scenario Selection:** Select **BLOCKED DOWNSTREAM** scenario.
3. **Inspect J3 Critical Link:**
   - Queue: $12\,\text{veh}$
   - Downstream Link (`J3_J4`): $47 / 53\,\text{veh}$ ($88.7\%$ occupancy $\rightarrow$ **CRITICAL**)
4. **Inspect Pipeline Decision:**
   - **M3:** Proposes `EXTEND_GREEN` to serve queue.
   - **M6:** Overrides with `SPILLBACK_BLOCK` due to critical downstream congestion.
   - **M9:** Evaluates Plan A, B, C; rejects Plan B (spillback risk), selects Plan C (downstream clearance).
   - **M5:** Validates safe phase transition to yellow clearance.
5. **Emergency & Recovery:** Switch to **AMBULANCE** scenario to demonstrate staged preemption, downstream queue evacuation, and post-emergency fairness recovery.
6. **Fail-Safe Mode Transition:** Observe automated degradation to `SAFE_ADAPTIVE` / `LOCAL_SAFE` upon telemetry failure, followed by `SHADOW_RECOVERY`.
7. **Operator Authorization:** Switch between `VIEWER` and `OPERATOR` roles to demonstrate access control and audit logging.

---

## Repository Structure

```
TrafficTwin-AI/
├── backend/
│   ├── app/
│   │   ├── guards/safety_firewall.py     # M5 Signal Safety Firewall
│   │   ├── planner/                      # M9 Digital Twin Plan Evaluator
│   │   │   ├── models.py
│   │   │   └── evaluator.py
│   │   ├── reliability/                  # M8 Multi-mode Fail-Safe Manager
│   │   │   └── fail_safe_manager.py
│   │   └── main.py                       # M10 FastAPI backend & RBAC
│   └── config/params.yaml                # Authoritative system parameters
├── experiments/                          # Core simulation controllers & runners
│   ├── baseline_fixed.py                 # M2 Fixed-time baseline
│   ├── reactive_controller.py            # M3 Queue-reactive controller
│   ├── stream_replay.py                  # M4 GPS stream & replay engine
│   ├── spillback_controller.py           # M6 Spillback capacity guard
│   ├── emergency_controller.py           # M7 Fairness & emergency controller
│   └── run_planner.py                    # M9 Experiment runner
├── frontend/                             # M10 Operator Control Room (React+Vite)
│   ├── src/
│   │   ├── components/                   # Corridor, charts, React Flow, logs
│   │   ├── services/trafficService.js    # Live API client with fallback
│   │   └── App.jsx
│   └── package.json
├── tests/                                # M11 Automated Test Suite (142 tests)
│   ├── test_m1_corridor.py
│   ├── test_m2_baseline.py
│   ├── test_m3_reactive.py
│   ├── test_m4_stream.py
│   ├── test_m5_firewall.py
│   ├── test_m6_spillback.py
│   ├── test_m7_ambulance_recovery.py
│   ├── test_m8_failsafe.py
│   ├── test_m9_planner.py
│   ├── test_m10_api_dashboard.py
│   └── test_m11_integration_flows.py
├── docs/                                 # Technical documentation & evidence
│   ├── M9_DIGITAL_TWIN_PLANNER.md
│   └── ...
└── CHANGELOG.md
```

---

## License

This project is licensed under the MIT License — see the LICENSE file for details.
