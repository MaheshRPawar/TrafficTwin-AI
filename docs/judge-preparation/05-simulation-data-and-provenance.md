# Document 05 — Simulation Data & Provenance

## 1. Ground Truth & Provenance Principles

In traffic engineering and academic judging, **honest data provenance is paramount**. TrafficTwin AI adheres to strict data transparency:

1. **No Phantom Datasets**: TrafficTwin does **not** claim to use live municipal GPS feeds, Google Maps APIs, or external city camera datasets.
2. **Authentic Micro-Simulation**: All vehicle movements, queues, speeds, and signal interactions are generated natively by Eclipse SUMO using established car-following physics (Krauss model) and collision avoidance equations.
3. **Synthetic Probe Events**: The GPS-like stream (`.jsonl`) is generated synthetically from SUMO's Floating Car Data (FCD) output to demonstrate how connected vehicle probe streams are ingested by TrafficTwin.

---

## 2. Inventory of Data Assets & Streams

| Data Stream / Artifact | Provenance Type | Source Script / Generator | Storage Location | Schema & Format |
| :--- | :--- | :--- | :--- | :--- |
| **Corridor Network** | Deterministic Config | Eclipse SUMO `netconvert` | [`sumo/net/corridor.net.xml`](file:///sumo/net/corridor.net.xml) | XML network defining 4 junctions ($J_1 \dots J_4$), lane geometry ($L = 250\text{m}$), and signal logic. |
| **Traffic Demand (Routes)** | Deterministic Micro-Flows | SUMO `duarouter` / XML | [`sumo/routes/corridor_*.rou.xml`](file:///sumo/routes/) | XML vehicle flows with arrival rates, vehicle types, and routes. |
| **Raw Simulation Telemetry** | Simulated Microscopic State | Eclipse SUMO Engine | [`sumo/output/*.xml`](file:///sumo/output/) | Raw XML logs: `tripinfo.xml` (travel time), `queue.xml` (lane queues), `summary.xml` (step throughput). |
| **Benchmark CSV Metrics** | Parsed & Aggregated | [`calculate_metrics.py`](file:///experiments/metrics/calculate_metrics.py) | [`data/output/metrics/`](file:///data/output/metrics/) | CSV tables: Throughput, Avg Waiting Time, P95 Waiting Time, Mean Queue, Max Queue, Spillback Blocks. |
| **Synthetic GPS Probe Stream** | Synthetic Ingestion Stream | [`generate_gps_events.py`](file:///experiments/generate_gps_events.py) | [`data/output/gps/*.jsonl`](file:///data/output/gps/) | JSONL events: `timestamp`, `vehicle_id`, `speed_kmph`, `edge_id`, `lane_index`, `lat_sim`, `lon_sim`. |
| **Safety & Audit Decision Trail** | Runtime Execution Records | M5 Firewall & M9 Evaluator | [`data/output/safety/`](file:///data/output/safety/) | CSV logs recording every firewall check, reason code, elapsed green, and selected plan scores. |

---

## 3. Scenario Definitions & Parameters

All scenarios run on the four-junction East-West corridor with 1.0-second step lengths and random seed `42` for exact reproducibility:

### Scenario 1: Normal Daytime Traffic (`corridor_normal`)
- **Demand**: Balanced arterial flow (~600 veh/hr) and moderate cross-street flow (~150 veh/hr per junction).
- **Condition**: Free-flow progression. Downstream link occupancies remain below 40%.
- **Behavior**: Standard progression (Plan A) maintains free flow without interventions.

### Scenario 2: Rush Hour Congestion (`corridor_rush`)
- **Demand**: Heavy arterial flow (~1400 veh/hr) creating dense vehicular platoons.
- **Condition**: Approach queues build up ($Q_{main} \ge 12\text{veh}$). Downstream occupancy enters the **Warning Band** ($75\% \le \text{Occ} < 85\%$).
- **Behavior**: Queue-reactive extension (Plan B) provides bounded $+5\text{s}$ green extensions to discharge platoons while respecting the 40s maximum green ceiling.

### Scenario 3: Blocked Downstream & Spillback (`corridor_blocked_downstream`)
- **Demand**: Heavy arterial flow combined with a synthetic bottleneck on downstream link $J_4\_E_5$ (capacity restricted).
- **Condition**: Traffic queues backward from $J_4$ onto link $J_3\_J_4$. Storage occupancy reaches **88.7%** ($\ge 85\%$ **Critical Band**).
- **Behavior**: M6 Spillback Guard **blocks** green extensions. M9 selects Plan C to clear downstream capacity and prevent corridor gridlock.

### Scenario 4: Emergency Ambulance Preemption (`corridor_ambulance`)
- **Demand**: Moderate arterial traffic with an active emergency response vehicle (`amb_1`) inserted into the stream.
- **Condition**: Ambulance approaches $J_2$ with an ETA of 12.4 seconds.
- **Behavior**: M7 detects the vehicle, evaluates downstream link capacity, stages downstream green clearance, and grants prioritized progression while tracking cross-street fairness debt ($14.5\text{s}$).

---

## 4. Synthetic GPS Probe Generation Pipeline

```mermaid
flowchart LR
    SUMO[SUMO Simulation Run] -->|Generates FCD Output| FCD[fcd_scenario.xml]
    FCD -->|Parsed by generate_gps_events.py| GPSGen[GPS Stream Generator]
    GPSGen -->|Transforms Speed & Coordinates| JSONL[scenario.jsonl]
    JSONL -->|Streamed via replay_gps.py| Backend[FastAPI Stream Buffer]
```

### JSONL Schema Specification
```json
{
  "event_id": "gps_normal_000120_veh_12",
  "timestamp": 120.0,
  "vehicle_id": "veh_12",
  "speed_mps": 11.2,
  "speed_kmph": 40.32,
  "edge_id": "J2_J3",
  "lane_index": 0,
  "position_m": 85.4,
  "lat_sim": 12.9715,
  "lon_sim": 77.5946,
  "vehicle_type": "passenger"
}
```

---

## 5. Viva Answer for Data Provenance

**Judge Question**: *"Did you test this on real-world traffic data?"*

**Verbal Viva Answer**:
> *"We want to be completely transparent: we did not use real municipal sensor feeds, because testing unverified signal preemption on real physical intersections is dangerous and illegal without city permits. Instead, we used Eclipse SUMO, the global standard for microscopic traffic simulation. SUMO models authentic vehicular physics, car-following equations, and queue dynamics. Our GPS stream was generated directly from SUMO vehicle traces so we can prove that TrafficTwin safely handles connected vehicle telemetry before physical deployment."*
