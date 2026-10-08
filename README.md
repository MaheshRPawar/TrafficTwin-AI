# TrafficTwin AI

> **Aarambh WCE Hackathon 2026 — Core Decision-Support Platform**  
> **Simulation-Based, Local-First Traffic Optimization & Corridor Safety Platform**

---

## 1. Overview

TrafficTwin AI is an authority-facing traffic control decision-support platform that couples a deterministic **Eclipse SUMO Digital Twin** with a **multi-layer safety and optimization pipeline**.

Before any signal action is recommended or executed, candidate strategies are evaluated counterfactually against physical link storage, downstream capacity, cross-street starvation thresholds, emergency priority directives, and an immutable Signal Safety Firewall.

The platform provides two distinct dashboards:
1. **Operator Control Room (`/`)**: For traffic engineers and operators with counterfactual Plan A/B/C evaluation, downstream spillback protection, emergency preemption tracking, fail-safe reliability modes, and verified authorization.
2. **Public Simulation Dashboard (`/public`)**: For citizens and observers with clear corridor status, active traffic alerts, queue sizes, and current/next signal countdown timings without exposure of internal control mechanics.

```
Traffic State (J1–J4)
       │
       ▼
[M3] Queue-Reactive Controller
       │
       ▼
[M7] Fairness & Emergency Directives
       │
       ▼
[M6] Spillback Capacity Guard (85% link occupancy lock)
       │
       ▼
[M9] Digital Twin Plan Evaluator (Plan A vs B vs C scoring)
       │
       ▼
[M5] Signal Safety Firewall (10s min green, clearance, conflicts)
       │
       ▼
SUMO / TraCI Simulation Execution
```

---

## 2. Key Modules & Capabilities

- **Corridor Modeling (M1–M2):** Four synchronized arterial junctions (**J1 $\rightarrow$ J2 $\rightarrow$ J3 $\rightarrow$ J4**) benchmarked against a calibrated fixed-time baseline.
- **Adaptive & Spillback Protection (M3, M6):** Bounded green extensions ($10\,\text{s} \le \text{green} \le 40\,\text{s}$) with active downstream link protection that blocks upstream extensions when downstream storage reaches $\ge 85\%$ occupancy.
- **Fairness & Emergency Preemption (M7):** Cross-street fairness debt accumulation prevents starvation; staged emergency preemption flushes downstream queues for approaching emergency vehicles and executes post-emergency recovery.
- **Reliability & Fail-Safe State Machine (M8):**
  $$\text{PREDICTIVE} \longleftrightarrow \text{SAFE\_ADAPTIVE} \longleftrightarrow \text{LOCAL\_SAFE} \longleftrightarrow \text{SHADOW\_RECOVERY}$$
- **Digital Twin Plan Evaluator (M9):**
  - **Plan A:** Current safe schedule.
  - **Plan B:** Bounded green extension (+5s).
  - **Plan C:** Downstream link clearing and coordinated arterial clearance.
  - Transparent deterministic scoring:
    $$\text{PlanScore} = 1.0 \cdot \text{delay} + 2.0 \cdot \text{queue} + 3.0 \cdot \text{spillback} + 1.5 \cdot \text{fairness} + 5.0 \cdot \text{emergency}$$
- **Operator Dashboard & REST API (M10):** Role-gated recommendations (`VIEWER` read-only, `OPERATOR` / `ADMIN` approval), immutable audit logging, and replay. Raw TraCI injection is strictly rejected.
- **Public Simulation Dashboard (M10 Extension):** Accessible at `/public`, displays corridor progression, active traffic alerts, queues, and signal countdowns.

---

## 3. System Boundaries & Operational Context

- **Simulation Testbed:** Built on Eclipse SUMO 1.27+ and TraCI.
- **Local-First & Offline:** Runs entirely without cloud or external network dependencies.
- **Authority-Facing:** Decision support for traffic operations centers, not public GPS routing.
- **Not Live Municipal Hardware Control:** Proves deterministic safety constraints prior to physical deployment.

---

## 4. Quick Start Guide

### Prerequisites
- Python 3.10+ (with Eclipse SUMO installed and `SUMO_HOME` configured)
- Node.js 18+ and npm

### 1. Backend Setup & Automated Verification
```bash
# Clone repository
git clone https://github.com/MaheshRPawar/TrafficTwin-AI.git
cd TrafficTwin-AI

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Linux/macOS: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run full test suite (142 tests)
pytest -v

# Run linters and security analysis
ruff check .
bandit -r backend experiments
pip-audit
```

### 2. Launch Backend API
```bash
python -m uvicorn backend.app.main:app --reload --port 8000
```

### 3. Launch Frontend Dashboards
```bash
cd frontend
npm install
npm run dev
```

- **Operator Dashboard:** Open `http://localhost:5173/`
- **Public Simulation Dashboard:** Open `http://localhost:5173/public`
*(You can also toggle between views via the navigation button in either header).*

### 4. Run Offline Simulations & Benchmarks
```bash
# Run Digital Twin counterfactual evaluation across all scenarios:
python experiments/run_planner.py --scenario normal
python experiments/run_planner.py --scenario rush_hour
python experiments/run_planner.py --scenario blocked_downstream
python experiments/run_planner.py --scenario ambulance
```

---

## 5. Dashboard Descriptions

### Operator Control Room (`/`)
- **Corridor Digital Twin:** Synchronized 4-junction schematic with per-junction queues, phases, and downstream occupancy bars.
- **M9 Plans Tab:** Compares Plan A, B, and C with component score breakdowns and validation/rejection reasons.
- **Flow Tab:** React Flow decision sequence from Traffic State through Safety Firewall to Signal Action.
- **Audit Tab:** Timestamped immutable audit log of system transitions and decisions.
- **Approval Panel:** Role-gated recommendation approval (`VIEWER` is read-only; `OPERATOR` / `ADMIN` can authorize).

### Public Simulation Dashboard (`/public`)
- **Corridor Overview:** Linear West Entry $\rightarrow$ J1 $\rightarrow$ J2 $\rightarrow$ J3 $\rightarrow$ J4 $\rightarrow$ East Exit view with traffic status badges.
- **Signal & Timing Display:** Current signal lamp (Green / Yellow / Red), seconds remaining countdown, and next signal indication.
- **Traffic Alerts:** Clean public advisory banner for incidents, high traffic volumes, or emergency vehicles.
- **Intersection Status Table:** Tabular overview of queues, signal phases, and traffic levels across all corridor junctions.

---

## 6. Judge & Viva Demonstration Flow

1. **Corridor Overview:** View J1–J4 synchronized corridor with real-time queue lengths and phase indicators.
2. **Scenario Selection — Blocked Downstream:** Select `BLOCKED DOWNSTREAM` scenario and inspect Junction J3:
   - Queue: $12\,\text{veh}$
   - Downstream Link (`J3_J4`): $47 / 53\,\text{veh}$ ($88.7\%$ occupancy $\rightarrow$ **CRITICAL**)
3. **Inspect Decision Pipeline:**
   - **M3:** Proposes `EXTEND_GREEN` to serve queue.
   - **M6:** Overrides with `SPILLBACK_BLOCK` to prevent intersection gridlock.
   - **M9:** Evaluates Plan A, B, and C. Plan B is rejected (`m6_spillback_violation`); Plan C is selected for downstream clearance coordination.
   - **M5:** Validates safe phase transition to yellow clearance ($3\,\text{s}$).
4. **Public Dashboard View:** Switch to `/public` to observe citizen-facing traffic alerts, signal countdowns, and congestion notices without technical internals.
5. **Emergency & Recovery:** Select `AMBULANCE` scenario:
   - Staged preemption clears downstream queues, grants priority green, and initiates post-emergency fairness debt service.
6. **Fail-Safe Mode Degradation:** Observe automated degradation from `PREDICTIVE` to `SAFE_ADAPTIVE` / `LOCAL_SAFE` upon telemetry loss, followed by `SHADOW_RECOVERY`.
7. **Role Authorization:** Switch role from `VIEWER` (read-only) to `OPERATOR` to demonstrate access control and audit logging.

---

## 7. Repository Structure

```
TrafficTwin-AI/
├── backend/
│   ├── app/
│   │   ├── controllers/      # Controller adapters
│   │   ├── guards/           # M5 Safety Firewall & clearance rules
│   │   ├── planner/          # M9 Digital Twin Plan Evaluator
│   │   ├── reliability/      # M8 Multi-mode Fail-Safe Manager
│   │   ├── stream/           # M4 Telematics stream model
│   │   └── main.py           # FastAPI service, RBAC & endpoints
│   └── config/params.yaml    # Central operational parameters
├── experiments/              # Offline simulation controllers & runners
│   ├── baseline_fixed.py     # M2 Fixed-time baseline
│   ├── reactive_controller.py# M3 Queue-reactive controller
│   ├── spillback_controller.py# M6 Spillback capacity guard
│   ├── emergency_controller.py# M7 Fairness & emergency controller
│   ├── stream_replay.py      # M4 GPS stream & replay engine
│   └── run_planner.py        # M9 Experiment runner
├── frontend/                 # React + Vite application
│   ├── src/
│   │   ├── pages/            # OperatorDashboard.jsx & PublicDashboard.jsx
│   │   ├── components/       # Corridor, charts, React Flow
│   │   ├── hooks/            # useTrafficData.js
│   │   ├── services/         # trafficService.js
│   │   ├── App.jsx           # Clean view routing
│   │   └── App.css           # Control room & public design system
│   └── package.json
├── data/                     # Scenario outputs & README catalog
│   ├── output/metrics/       # SUMO travel time and queue CSVs
│   ├── output/safety/        # Firewall decision CSVs
│   └── README.md
├── sumo/                     # Eclipse SUMO network & scenario configs
│   ├── scenarios/            # .sumocfg for normal, rush, blocked, ambulance
│   ├── net/                  # 4-junction corridor road network (.net.xml)
│   └── routes/               # Calibrated traffic demand flows (.rou.xml)
├── tests/                    # Automated Test Suite (142 tests passing)
└── CHANGELOG.md
```

---

## 8. License

This project is licensed under the MIT License — see the LICENSE file for details.
