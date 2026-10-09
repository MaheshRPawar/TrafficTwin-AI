# Document 02 — Complete Annotated Folder Structure

## 1. High-Level Repository Layout

```
TrafficTwin-AI/
├── backend/                  # FastAPI REST & WebSocket server, safety guards, M9 planner
├── frontend/                 # React 19 + Vite desktop application & public dashboard
├── sumo/                     # SUMO network files, routes, and scenario configurations
├── experiments/              # Benchmark scenario runners, controllers, and metric parsers
├── data/                     # Output metrics, synthetic GPS logs, and safety audit traces
├── tests/                    # Pytest test suite (142 comprehensive tests)
├── scripts/                  # Environment verification and diagnostic utilities
├── docs/                     # Architecture specifications and judge-preparation guides
├── run.bat                   # One-click Windows launcher (starts Backend + Frontend + Browser)
├── launch_sumo_gui.bat       # One-click SUMO GUI visualizer launcher
└── stop.bat                  # One-click script to terminate running servers
```

---

## 2. Detailed Directory & File Breakdown

### A. Backend (`backend/`)
Contains the Python FastAPI web service, digital twin evaluator, safety firewall, and reliability managers.

| File Path | Type | Purpose | Calls / Dependencies |
| :--- | :--- | :--- | :--- |
| [`backend/app/main.py`](file:///backend/app/main.py) | Source | FastAPI application entry point. Implements REST endpoints (`/api/corridor/state`, `/api/health`, `/api/recommendations`, `/api/audit-events`) and WebSocket (`/ws/simulation`). | Calls `DigitalTwinPlanner`, reads `data/output/` |
| [`backend/app/guards/safety_firewall.py`](file:///backend/app/guards/safety_firewall.py) | Source | **Module M5**: Enforces deterministic signal constraints (10s min green, 40s max green, 3s yellow, legal phase sequence). | Called by `main.py`, `run_planner.py`, `run_ambulance.py` |
| [`backend/app/guards/spillback_guard.py`](file:///backend/app/guards/spillback_guard.py) | Source | **Module M6**: Computes physical link occupancy and blocks upstream green when occupancy $\ge 85\%$. | Called by `spillback_controller.py`, `evaluator.py` |
| [`backend/app/planner/evaluator.py`](file:///backend/app/planner/evaluator.py) | Source | **Module M9**: Deterministic Digital Twin Evaluator generating and scoring Plan A, Plan B, and Plan C. | Calls `models.py`, `params.yaml` |
| [`backend/app/planner/models.py`](file:///backend/app/planner/models.py) | Source | Pydantic data schemas for `CorridorSnapshot`, `JunctionSnapshot`, `PlanCandidate`, and `EvaluationResult`. | Imported across planner and backend |
| [`backend/app/reliability/fail_safe.py`](file:///backend/app/reliability/fail_safe.py) | Source | **Module M8**: Finite state machine managing transitions between `PREDICTIVE`, `DEGRADED`, and `FAIL_SAFE` modes. | Called by runtime controllers |
| [`backend/config/params.yaml`](file:///backend/config/params.yaml) | Config | Authoritative system parameters (min/max green, yellow clearance, spillback thresholds, penalty weights). | Read by all controllers and guards |

---

### B. Frontend (`frontend/`)
Vite + React single-page desktop application featuring dual dashboards (Operator Control Room and Public Commuter Portal).

| File Path | Type | Purpose | Calls / Dependencies |
| :--- | :--- | :--- | :--- |
| [`frontend/src/App.jsx`](file:///frontend/src/App.jsx) | Source | Main application component. Manages view routing between `/` (Operator) and `/public` (Public). | Renders `OperatorDashboard` or `PublicDashboard` |
| [`frontend/src/pages/OperatorDashboard.jsx`](file:///frontend/src/pages/OperatorDashboard.jsx) | Source | Professional Control Room: Plan A/B/C scorecard, M5 firewall latch, M6 spillback warnings, TraCI audit log. | Uses `RightOperationsConsole`, `CorridorDigitalTwin` |
| [`frontend/src/pages/PublicDashboard.jsx`](file:///frontend/src/pages/PublicDashboard.jsx) | Source | Clean citizen view: Arterial schematic, countdown timers, advisory alerts, junction conditions. | Uses `trafficService.js` |
| [`frontend/src/components/CorridorDigitalTwin.jsx`](file:///frontend/src/components/CorridorDigitalTwin.jsx) | Source | Interactive corridor map schematic rendering J1–J4 signal heads, queues, and arterial links. | Rendered inside Operator Dashboard |
| [`frontend/src/components/RightOperationsConsole.jsx`](file:///frontend/src/components/RightOperationsConsole.jsx) | Source | Decision inspector showing M9 scoring breakdown, M5 safety validation, and simulation authorization. | Connects to `/api/recommendations/approve-simulation` |
| [`frontend/src/components/DecisionGraphFlow.jsx`](file:///frontend/src/components/DecisionGraphFlow.jsx) | Source | Visual node graph showing the 7-step control pipeline execution flow. | Rendered inside Operator Console |
| [`frontend/src/components/AnalyticsCharts.jsx`](file:///frontend/src/components/AnalyticsCharts.jsx) | Source | Recharts comparative performance graphs (Delay vs Queue, Controller metrics). | Rendered inside Operator Dashboard |
| [`frontend/src/services/trafficService.js`](file:///frontend/src/services/trafficService.js) | Source | Frontend data fetcher and WebSocket manager for backend integration. | Calls `http://127.0.0.1:8000/api/*` |
| [`frontend/src/App.css`](file:///frontend/src/App.css) | Style | Professional transportation engineering stylesheet (clean light theme, thin borders, no neon). | Imported by `App.jsx` |

---

### C. SUMO Simulation Network & Scenarios (`sumo/`)
Authentic micro-simulation configurations built using Eclipse SUMO XML specifications.

| File Path | Type | Purpose |
| :--- | :--- | :--- |
| [`sumo/net/corridor.net.xml`](file:///sumo/net/corridor.net.xml) | Network | SUMO compiled network: 4 signalized intersections ($J_1, J_2, J_3, J_4$), 4 cross-streets, lane connections, signal heads. |
| [`sumo/routes/corridor_normal.rou.xml`](file:///sumo/routes/corridor_normal.rou.xml) | Routes | Balanced daytime vehicular demand (arterial + cross-street flows). |
| [`sumo/routes/corridor_rush.rou.xml`](file:///sumo/routes/corridor_rush.rou.xml) | Routes | Heavy peak-hour arterial flows generating approach queues. |
| [`sumo/routes/corridor_blocked_downstream.rou.xml`](file:///sumo/routes/corridor_blocked_downstream.rou.xml) | Routes | Simulated bottleneck on link $J_4\_E_5$ causing upstream spillback toward $J_3$. |
| [`sumo/routes/corridor_ambulance.rou.xml`](file:///sumo/routes/corridor_ambulance.rou.xml) | Routes | Corridors with an active emergency vehicle (`amb_1`) requiring staged preemption. |
| [`sumo/scenarios/corridor_*.sumocfg`](file:///sumo/scenarios/corridor_normal.sumocfg) | Config | SUMO configuration files linking net and route files, step lengths (1.0s), and output XML destinations. |

---

### D. Experiments & Controllers (`experiments/`)
Standalone simulation scripts evaluating control algorithms via TraCI.

| File Path | Module | Purpose |
| :--- | :--- | :--- |
| [`experiments/run_fixed.py`](file:///experiments/run_fixed.py) | **M2** | Runs the fixed-time baseline (unresponsive 30s arterial green, 15s cross-street green). |
| [`experiments/run_reactive.py`](file:///experiments/run_reactive.py) | **M3** | Runs the queue-reactive controller (extends green based on incoming queue, but downstream-blind). |
| [`experiments/run_spillback.py`](file:///experiments/run_spillback.py) | **M6** | Runs the spillback-aware controller (blocks green when downstream storage $\ge 85\%$). |
| [`experiments/run_ambulance.py`](file:///experiments/run_ambulance.py) | **M7** | Runs integrated ambulance preemption, cross-street fairness debt tracking, and staged recovery. |
| [`experiments/run_planner.py`](file:///experiments/run_planner.py) | **M9** | Runs the complete Digital Twin Plan A/B/C Evaluator comparing candidate strategies in real time. |
| [`experiments/metrics/calculate_metrics.py`](file:///experiments/metrics/calculate_metrics.py) | Metrics | Parses raw SUMO tripinfo, queue, and summary XML outputs into standardized benchmark CSV files. |

---

### E. Data & Datasets (`data/`)
Stores generated benchmark metrics, synthetic vehicle probe logs, and safety records.

| File Path | Description |
| :--- | :--- |
| [`data/output/metrics/`](file:///data/output/metrics/) | Benchmark summary CSVs (`fixed_*_summary.csv`, `reactive_*_summary.csv`, `spillback_*_summary.csv`, `m7_*_summary.csv`, `planner_*_summary.csv`). |
| [`data/output/gps/`](file:///data/output/gps/) | Synthetic GPS-like JSONL vehicle streams (`normal.jsonl`, `rush.jsonl`, `blocked_downstream.jsonl`, `ambulance.jsonl`) generated from SUMO FCD traces. |
| [`data/output/safety/`](file:///data/output/safety/) | Immutable decision logs recording every M5 firewall check, M6 spillback block, and M9 plan selection. |
| [`data/README.md`](file:///data/README.md) | Comprehensive data dictionary defining column formats, units, and provenance. |

---

### F. Tests (`tests/`)
Pytest suite containing **142 automated unit and integration tests** guaranteeing 100% test pass rate across all modules (M1–M11).
