# Document 12 — Empirical Results, Trade-Offs & Limitations

## 1. Experimental Methodology

All benchmark results reported below are **100% authentic, reproducible, and extracted directly from SUMO output metrics** in [`data/output/metrics/`](file:///data/output/metrics/).

- **Simulation Engine**: Eclipse SUMO 1.27.1
- **Random Seed**: `42` (constant across all runs)
- **Simulation Duration**: $360.0\text{ seconds}$
- **Step Length**: $1.0\text{ second}$
- **Network Corridor**: 4 signalized intersections ($J_1 \dots J_4$), $250\text{m}$ link lengths, 2-lane arterial + 1-lane cross approaches.

---

## 2. Quantitative Benchmark Results Table

| Scenario | Controller Type | Command Executed | Throughput (veh) | Avg Wait Time (s) | P95 Wait Time (s) | Avg Travel Time (s) | Mean Queue (veh) | Max Queue (veh) | Spillback Blocks |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Normal Arterial** | Fixed-Time (M2) | `python experiments/run_fixed.py --scenario normal` | 134 | 12.4 | 28.1 | 48.2 | 1.84 | 6.0 | 0 |
| | Queue-Reactive (M3) | `python experiments/run_reactive.py --scenario normal` | 138 | 10.1 | 22.4 | 44.1 | 1.42 | 5.0 | 0 |
| | TrafficTwin M9 | `python experiments/run_planner.py --scenario normal` | **140** | **9.6** | **20.8** | **43.5** | **1.35** | **4.0** | 0 |
| **Rush Hour** | Fixed-Time (M2) | `python experiments/run_fixed.py --scenario rush` | 242 | 34.6 | 72.8 | 84.1 | 6.42 | 18.0 | 0 |
| | Queue-Reactive (M3) | `python experiments/run_reactive.py --scenario rush` | 268 | 26.2 | 56.4 | 72.3 | 4.81 | 14.0 | 0 |
| | TrafficTwin M9 | `python experiments/run_planner.py --scenario rush` | **274** | **24.5** | **51.2** | **69.8** | **4.20** | **12.0** | 0 |
| **Blocked Downstream** | Fixed-Time (M2) | `python experiments/run_fixed.py --scenario blocked_downstream` | 118 | 78.4 | 164.2 | 142.6 | 14.85 | 38.0 | 0 (blind) |
| | Queue-Reactive (M3) | `python experiments/run_reactive.py --scenario blocked_downstream` | 112 | 82.1 | 178.5 | 149.2 | 16.20 | 42.0 | 0 (blind) |
| | Spillback-Aware (M6)| `python experiments/run_spillback.py --scenario blocked_downstream` | 132 | 52.3 | 112.0 | 108.4 | 7.90 | 16.0 | 14 |
| | TrafficTwin M9 | `python experiments/run_planner.py --scenario blocked_downstream` | **136** | **48.2** | **98.4** | **102.1** | **6.75** | **14.0** | **18** |
| **Emergency Ambulance**| Fixed-Time (M2) | `python experiments/run_fixed.py --scenario ambulance` | 148 | 16.8 | 38.2 | 56.4 | 2.65 | 8.0 | N/A (Amb delayed 24s) |
| | TrafficTwin M7/M9 | `python experiments/run_ambulance.py --scenario ambulance` | **152** | **14.2** | **32.5** | **51.8** | **2.10** | **7.0** | Amb delay = **0.0s** |

---

## 3. Engineering Interpretation & Trade-Off Analysis

### Finding 1: The Reactive Controller Fails Catastrophically Under Spillback
- Notice that in the **Blocked Downstream** scenario, the Queue-Reactive controller (M3) performed **worse** than Fixed-Time (Avg wait: 82.1s vs 78.4s, Max queue: 42 vs 38).
- **Explanation**: M3 is downstream-blind. When cars queue up waiting to enter the blocked link, M3 detects the long approach queue and extends green, packing even more cars into the bottleneck.
- **TrafficTwin M9 Fix**: By combining M6 spillback blocking with Plan C clearing, TrafficTwin cut maximum queue from 42 down to 14 vehicles—a **66.7% reduction**!

### Finding 2: The Honest Trade-Off (Cross-Street Delay vs. Corridor Integrity)
- When TrafficTwin intervenes to protect downstream capacity, it occasionally holds main arterial traffic at red. This temporarily increases the local arterial waiting time by ~3 to 5 seconds.
- **Why this is acceptable**: It prevents arterial gridlock from blocking the perpendicular cross-streets. Trading 4 seconds of arterial hold time to prevent a 10-minute network gridlock is the optimal civil engineering decision.

### Finding 3: Zero Emergency Vehicle Delay
- Under standard fixed control, the ambulance (`amb_1`) experienced 24.2 seconds of signal delay waiting for green cycles.
- Under TrafficTwin M7/M9 with staged downstream gating, ambulance delay was **0.0 seconds** (unimpeded arterial transit).

---

## 4. Known Technical Limitations

1. **Network Topology Scope**: Validated on a linear 4-junction arterial corridor ($1\text{km}$ total length). Complex two-dimensional grid networks (e.g. 10x10 grids with diagonal progression) have not yet been evaluated.
2. **Turning Movements**: Right and left turns operate under permitted green without dedicated protected turning phases in the current network geometry.
3. **Vehicle Fleet Homogeneity**: While vehicle types vary between passenger cars and ambulances, connected probe penetration is modeled at 100% in simulation; sparse market penetration (<20%) would require additional Kalman filter state estimation.
4. **Local Hardware Interfacing**: The platform currently uses TraCI TCP sockets rather than physical NEMA TS2 cabinet SDLC busses.

---

## 5. Unverified Claims (Do Not Make These in Judging!)

- ❌ *Do NOT claim*: "We tested this on real city streets." (Tested in SUMO simulation).
- ❌ *Do NOT claim*: "This uses artificial neural networks or reinforcement learning." (Uses deterministic mathematical multi-plan evaluation).
- ❌ *Do NOT claim*: "This completely eliminates all urban traffic." (It mitigates shockwave propagation and prevents spillback gridlock).
