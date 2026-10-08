# TrafficTwin AI — Simulation Datasets and Output Catalogs

This directory contains the simulation outputs, metrics, telematics streams, and safety audit logs generated across Modules M1 through M11.

---

## 1. Directory Structure

```
data/
├── output/
│   ├── metrics/       # Travel time, queue length, and performance summaries
│   ├── safety/        # Safety firewall validation records
│   ├── fairness/      # Cross-street fairness debt and starvation logs
│   └── gps/           # Synthesized telematics/GPS event streams (JSONL)
├── demo_assets/       # Chart comparisons and visual evaluation assets
└── README.md          # Dataset documentation (this file)
```

---

## 2. Simulation Scenarios

All datasets originate from deterministic runs in Eclipse SUMO 1.27.1 with random seed `42` across the four-junction arterial corridor (`J1 → J2 → J3 → J4`):

| Scenario ID | Name | Duration | Description |
| :--- | :--- | :---: | :--- |
| `normal` | Normal Arterial | 300s | Balanced daytime arterial flow; baseline progression |
| `rush` | Peak Rush Hour | 300s | High arrival volume; main arterial approaches saturation |
| `blocked_downstream` | Blocked Downstream | 300s | Physical storage blockage on link `J4_E5` propagating upstream to `J3` |
| `ambulance` | Emergency Corridor | 300s | Priority emergency vehicle dispatch with staged green-wave preemption |

---

## 3. Metric File Conventions

In `data/output/metrics/`, files are named according to:
`{controller}_{scenario}_{metric}.csv`

### Controllers:
- `fixed_` — M2 Fixed-Time Baseline (cyclic, no adaptive overrides)
- `reactive_` — M3 Queue-Reactive Controller (bounded green extensions)
- `spillback_` — M6 Spillback-Aware Guard (downstream capacity lock at $\ge 85\%$)
- `m7_` — M7 Fairness Debt + Ambulance Preemption + Post-Emergency Recovery
- `planner_` — M9 Digital Twin Plan A/B/C Evaluator

### Metric Types:
- `*_summary.csv` — Throughput (veh), average waiting time (s), average travel time (s), mean queue length (veh), peak occupancy (%).
- `*_queues.csv` — Per-second queue length per approach across J1, J2, J3, and J4.
- `*_trips.csv` — Vehicle-level trip completion records (depart, arrival, duration, time loss).
- `*_decisions.csv` — Real-time signal control decision trace.

---

## 4. Safety & Audit Records

- `data/output/safety/` contains timestamped verdicts from the M5 Signal Safety Firewall (`firewall_decisions.csv`), recording proposed vs. allowed phase transitions, minimum green enforcement, and clearance interval verifications.
- `data/output/fairness/` records cross-street debt accumulation and starvation prevention triggers.

---

## 5. Telematics Streams

In `data/output/gps/`, `gps_stream_{scenario}.jsonl` contains deterministic GPS telematics events conforming to the JSON schema in `shared/schemas/vehicle_position.schema.json`.

---

## 6. Data Integrity & Honesty

- **Authenticity:** All metrics are derived from actual Eclipse SUMO simulation outputs (`summary.xml`, `tripinfo.xml`, `queue.xml`).
- **No Fabrication:** No metrics or curves are artificially smoothed or altered.
- **Scope Boundary:** These datasets represent simulation-derived operational benchmarks, not municipal field telemetry from physical street hardware.
