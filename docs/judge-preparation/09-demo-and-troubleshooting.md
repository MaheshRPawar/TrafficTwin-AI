# Document 09 — Live Demo Walkthrough & Troubleshooting

## 1. Pre-Demo Quick Start Checklist

Before presenting to judges, ensure your environment is clean:
1. Python 3.11+ virtual environment active at `.venv`.
2. Node.js & npm installed (`node -v` $\ge 18$).
3. Eclipse SUMO installed and on PATH (`sumo --version` and `sumo-gui --version`).
4. Ports 8000 and 5173 free.

---

## 2. One-Click Startup (Recommended)

1. **Step 1**: Double-click [`run.bat`](file:///run.bat) in the repository root.
   - Starts FastAPI Backend on `http://127.0.0.1:8000`.
   - Starts Vite React Frontend on `http://localhost:5173`.
   - Automatically opens your default web browser to the **Operator Control Room**.
2. **Step 2**: Double-click [`launch_sumo_gui.bat`](file:///launch_sumo_gui.bat) to launch the simulation window in SUMO GUI.
   - Select option `[1]` for Normal, `[2]` for Rush, `[3]` for Blocked Downstream, or `[4]` for Ambulance.

---

## 3. Manual Terminal Startup (3 Terminals)

If presenting from a terminal-only setup, open three terminal tabs:

```powershell
# Terminal 1 — Backend API
d:\X\Aarambh-WCE\Project\TrafficTwin-AI\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend Dev Server
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173

# Terminal 3 — SUMO GUI Simulation
sumo-gui -c sumo/scenarios/corridor_normal.sumocfg --start
```

---

## 4. Scenario Walkthrough for Judges (The 4 Demos)

### Demo A: Normal Traffic (Progression Baseline)
1. In the web dashboard top bar, select **Normal Arterial**.
2. **What to Show**:
   - Corridor schematic shows steady green progression through $J_1 \dots J_4$.
   - Downstream link occupancies remain $<30\%$ (green).
   - In the Right Console, the Digital Twin Evaluator selects **Plan A (Progression)** with the lowest penalty score ($14.2$).
   - Safety Firewall confirms elapsed green within safe bounds $[10\text{s}, 40\text{s}]$.
3. **What to Say**: *"Under normal conditions, TrafficTwin identifies balanced demand and chooses Plan A, maintaining free-flow progression without unnecessary interventions."*

---

### Demo B: Rush Hour Congestion (Approach Queue Clearance)
1. Select **Rush Hour Congestion** in the top bar.
2. **What to Show**:
   - Approach queues build on $J_2$ and $J_3$ ($Q_{main} \ge 14\text{veh}$).
   - Downstream occupancy rises to $77.4\%$ (Yellow Warning Band).
   - Digital Twin Evaluator selects **Plan B (Approach Clearance)** with score $36.8$.
   - Safety Firewall verifies that elapsed green ($15\text{s}$) plus proposed extension ($5\text{s}$) does not exceed the $40\text{s}$ maximum green limit.
3. **What to Say**: *"During peak flow, approach queues spike. TrafficTwin selects Plan B to extend green by 5 seconds, clearing platoons while strictly adhering to the 40-second safety ceiling."*

---

### Demo C: Blocked Downstream (Spillback Protection) — The Star Feature!
1. Select **Blocked Downstream** in the top bar.
2. **What to Show**:
   - Link $J_3\_J_4$ turns red, reaching **88.7% occupancy** (Critical Band).
   - Module M3 attempts to extend green due to local queue ($Q=12$).
   - **M6 Spillback Guard intercepts and blocks the extension**: `BLOCK_EXTENSION`.
   - In the Plan Scorecard, **Plan B is explicitly marked REJECTED** due to M6 capacity violation!
   - Digital Twin Evaluator selects **Plan C (Downstream Flushing)** with score $28.5$.
   - Safety Firewall validates transition to Yellow (Phase 1).
3. **What to Say**: *"This is our core innovation. An incident downstream has filled link J3–J4 to 88% capacity. A traditional controller would keep turning green to clear local cars, causing total corridor gridlock. TrafficTwin's M6 Spillback Guard intercepts the extension, rejects Plan B, and selects Plan C to protect corridor capacity."*

---

### Demo D: Emergency Ambulance Preemption
1. Select **Emergency Ambulance** in the top bar.
2. **What to Show**:
   - Top banner alerts: `EMERGENCY VEHICLE DETECTED: amb_1 approaching J2 (ETA: 12.4s)`.
   - Downstream capacity on $J_2\_J_3$ is checked.
   - Stage transitions to `DOWNSTREAM_CLEARANCE` to flush ahead of the ambulance.
   - Fairness Debt tracker registers $14.5\text{s}$ of cross-street waiting time.
   - After ambulance passage, staged recovery clears cross-street queues.
3. **What to Say**: *"Notice that TrafficTwin doesn't blindly turn the signal green. It first flushes the downstream link so the ambulance doesn't enter a traffic jam, and tracks fairness debt to rapidly compensate cross-street traffic afterward."*

---

## 5. Live Standalone Terminal Demonstrations

You can also run standalone demonstration scripts directly in front of judges:

```powershell
# 1. Demonstrate M5 Safety Firewall Invariant Checks
.venv\Scripts\python.exe experiments/demo_safety_firewall.py

# 2. Demonstrate M6 Spillback Guard Interception
.venv\Scripts\python.exe experiments/demo_spillback.py

# 3. Run Complete M9 Digital Twin Planner (all 4 scenarios with summary table)
.venv\Scripts\python.exe experiments/run_planner.py --all
```

---

## 6. Troubleshooting & Recovery

| Issue / Error | Root Cause | Immediate Fix |
| :--- | :--- | :--- |
| `Address already in use: 8000` | Stale Uvicorn or Python process | Double-click [`stop.bat`](file:///stop.bat) or run `Get-Process python \| Stop-Process -Force` |
| `Address already in use: 5173` | Stale Vite dev server | Double-click [`stop.bat`](file:///stop.bat) or run `Get-Process node \| Stop-Process -Force` |
| `TraCI connection failed` | SUMO did not launch or port blocked | Ensure no other SUMO process is open: `Get-Process sumo* \| Stop-Process -Force` |
| Frontend shows "Backend Disconnected" | Backend server not running | Start backend via Terminal 1 or run `run.bat` |
| Public view shows 403 on approval | Working as intended! | Public portal is strictly read-only; use Operator Dashboard (`/`) to approve actions |
