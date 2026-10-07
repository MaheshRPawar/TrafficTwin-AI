# TrafficTwin AI — Architecture
Version 1.0

## 1. Overview
Single-machine, three-process system. Simulation authority is SUMO; the control engine reads state and writes phases through TraCI; the dashboard is a read-mostly client.

```
SUMO (net, routes, seed)
   ↕ TraCI (1 s step)
Backend (Python / FastAPI)
  sim_runner → stream (GPS-like events, fault injector)
     → estimator (link/junction state, trust)
     → forecast (wave risk)
     → twin (Plan A/B/C)
     → controller (fixed | reactive | traffictwin)
     → firewall (validate)
     → TraCI apply  ──→ metrics logger (CSV)
     → mode manager (Predictive / Safe Adaptive / Local Safe / Shadow)
  WebSocket /ws/live · REST
   ↓
React dashboard (SVG corridor, decision log, charts)
```

## 2. Control loop (every 1 s sim step)
1. Read vehicles/edges/signals via TraCI.
2. Build GPS-like events; apply fault injector; compute trust.
3. Update state (link, junction).
4. Mode manager picks mode from trust, faults, firewall rejects.
5. Active controller proposes an action per junction.
6. Firewall validates; on reject → stored plan step + log.
7. Apply to TraCI; log decision card.
8. Metrics logger appends; WebSocket publishes (throttled).
Twin runs every TWIN_PERIOD_S (default 15 s) and on triggers (ambulance detected, spillback risk High).

## 3. Modules and responsibilities
| Module | Responsibility | Depends on |
|---|---|---|
| sim_runner | scenario launch, step loop, determinism | TraCI |
| stream | event build, outage/latency/duplicate injection | sim_runner |
| state/estimator | link and junction state | stream |
| state/trust | trust score per link | stream |
| predict/wave_forecast | rule-based risk and ETA of queue wave | estimator |
| controllers/* | propose action | estimator, forecast |
| guards/spillback | free-capacity gate | estimator |
| guards/fairness | debt, starvation override | estimator |
| guards/firewall | final validation, verdict log | all controllers |
| priority/bus, ambulance, recovery | bounded priority logic | guards |
| twin/* | candidate plans, evaluator, score | estimator, forecast |
| reliability/mode_manager | state machine, fallback plan | trust, faults |
| metrics/* | CSV logging, summaries | sim_runner |

## 4. Key algorithms
**Link capacity** = floor(length_m × lanes / (avg_vehicle_len + min_gap)). Default 7.5 m per vehicle; tune after calibration.
**Wave forecast** per link: travel_time = length / free_speed; inflow(t) = vehicles released upstream at t − travel_time; risk = clamp((vehicles + Σ inflow − Σ expected_outflow) / capacity, 0, 1) over H.
**Downstream guard**: allow iff free_capacity ≥ expected_released + BUFFER.
**Fairness debt**: D_i = α·avg_wait_i + β·max_wait_i + γ·missed_cycles_i.
**Ambulance staging**: ETA_k from position and speed; open green at J_k in window [ETA_k − LEAD, ETA_k + PASS]; before opening, if downstream link of J_k is below free-capacity threshold, hold upstream and give clearing green to J_{k+1} first.
**Recovery**: after ambulance passes J4 (or leaves), serve approaches in descending D_i with bounded green RECOVERY_MAX per approach until debt < target or RECOVERY_CAP_S reached.
**Plan score**: weighted sum, lower is better (weights in params.yaml).
**Trust** = Σ w_k · metric_k, k ∈ {freshness, 1−missing, coverage, speed-consistency, 1−duplicates, latency-score}.

## 5. Mode state machine
```
Predictive ──trust<T_PRED──▶ Safe Adaptive ──trust<T_LOCAL or no GPS or ML fail or unsafe cmd──▶ Local Safe
     ▲                                                                                             │
     └──── STABLE_S window passed, trust≥T_RESUME, 0 rejects ◀── Shadow Recovery ◀── services back ┘
```
Local Safe uses `fallback_plan.json` (fixed-time, pre-validated). Shadow Recovery: AI computes and logs recommendations, never applies.

## 6. Interfaces
Event types on `/ws/live`: `gps`, `link`, `junction`, `decision`, `mode`.
REST: `POST /scenario/start`, `POST /fault/inject`, `POST /decision/{id}/approve`, `GET /metrics/summary`, `GET /decisions`, `GET /health`.
Schemas (JSON Schema) in `shared/schemas/`; TypeScript types generated or hand-mirrored in `frontend/src/lib/types.ts`.

## 6a. Replay mode
Every event is written to `data/recorded/*.jsonl` during a run. The dashboard can replay them offline with the same schemas, used for R1, as demo backup, and for frontend development without SUMO.

## 7. Deployment
Local: `make sim`, `make api`, `make web`. Docker Compose is P2. Always keep a recorded demo and pre-run results CSV.

## 8. Architecture decisions (ADR summary)
- ADR-1 Rule-based forecast over ML: explainable, no training risk. ML is P2.
- ADR-2 Lightweight twin over SUMO forks: speed and reliability; SUMO fork is stretch.
- ADR-3 Firewall as single choke point to TraCI writes.
- ADR-4 SQLite/CSV/JSON instead of PostgreSQL/Redis: no operational overhead.
- ADR-5 Custom SVG corridor instead of Leaflet: schematic 4-junction view is clearer.
- ADR-6 Three control modes plus Shadow Recovery transition (not four peer modes).
- ADR-7 Source-agnostic ingestion adapter so a real GTFS-realtime/telematics feed can plug in later.

## 8a. Failure isolation and trust boundary
Dashboard → API → authorization → safety firewall → TraCI adapter. The dashboard never touches TraCI.
| Component fails | System behavior |
|---|---|
| Dashboard | API and controller continue |
| API | controller keeps writing JSONL/CSV locally |
| Database | JSONL/CSV (primary store) |
| Planner / forecast | Safe Adaptive controller |
| Safe controller | Local Safe fixed-time plan |
| GPS feed | trust drops ⇒ Safe Adaptive ⇒ Local Safe |
| SUMO GUI | headless run + metrics + recorded demo |
| Internet | no impact; everything runs locally |

## 9. Known limits (state these honestly)
Simulation results do not transfer automatically to real roads; GPS is simulated; no pedestrians; emissions are a proxy; twin is a simplified model.
