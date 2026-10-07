# Module M4 — Simulated GPS-Like Stream & Replay

## 1. Purpose

Module M4 converts simulated vehicle state from the 4-junction SUMO corridor into a normalized, GPS-like event stream stored in JSON Lines (`.jsonl`) format, and provides an offline replay utility.

> **SIMULATED GPS ONLY:**  
> This module does NOT connect to real GPS devices, mobile GPS, Google Maps, Mapbox, fleet APIs, GTFS, MQTT, external telemetry APIs, or real vehicle hardware. The stream originates 100% from the existing SUMO simulation.

The purpose is to establish a realistic, normalized internal event format that downstream TrafficTwin modules can consume sequentially. Later, real GPS or CCTV adapters can produce this same schema without altering downstream logic.

---

## 2. Event Schema

Each vehicle observation produces one JSONL record adhering to `shared/schemas/vehicle_position.schema.json`:

```json
{
  "event_type": "vehicle_position",
  "event_id": "gps_car_12_45.0",
  "vehicle_id": "car_12",
  "vehicle_type": "passenger",
  "timestamp": 45.0,
  "corridor_id": "corridor_4j",
  "junction_id": "J2",
  "lane_id": ":J2_0_0",
  "road_segment_id": ":J2_0",
  "x": 420.5,
  "y": 1.6,
  "speed_kmph": 41.2,
  "heading_degrees": 90.0,
  "source": "simulated_sumo",
  "freshness_seconds": 0.0
}
```

### Field Definitions

| Field | Type | Description | Source |
|---|---|---|---|
| `event_type` | string | Always `"vehicle_position"` | Constant |
| `event_id` | string | Deterministic ID: `gps_<vehicle_id>_<timestamp:.1f>` | Derived |
| `vehicle_id` | string | SUMO vehicle identifier | `traci.vehicle.getIDList()` |
| `vehicle_type` | string | Vehicle type (`passenger`, `emergency`, etc.) | `traci.vehicle.getTypeID()` |
| `timestamp` | number | Simulation time in seconds | `traci.simulation.getTime()` |
| `corridor_id` | string | Fixed corridor identifier (`"corridor_4j"`) | Constant |
| `junction_id` | string \| null | Junction ID (`J1`..`J4`) if vehicle is inside junction, else `null` | Derived from edge name |
| `lane_id` | string | Current lane identifier | `traci.vehicle.getLaneID()` |
| `road_segment_id` | string | Current road edge / segment | Derived from lane ID |
| `x`, `y` | number | 2D coordinates in meters | `traci.vehicle.getPosition()` |
| `speed_kmph` | number | Vehicle speed in km/h (`speed_mps * 3.6`) | `traci.vehicle.getSpeed()` |
| `heading_degrees` | number | Normalized heading 0–360° | `traci.vehicle.getAngle() % 360.0` |
| `source` | string | Always `"simulated_sumo"` | Constant |
| `freshness_seconds` | number | Observation age in seconds (0.0 at capture) | Constant |

---

## 3. SUMO → JSONL Pipeline

The generator script `experiments/generate_gps_events.py`:
1. Resolves the SUMO configuration (`corridor_normal.sumocfg`, `corridor_rush.sumocfg`, etc.).
2. Starts TraCI with deterministic seed (default 42).
3. At each simulation step (`1.0 s` by default):
   - Queries `traci.vehicle.getIDList()`.
   - Extracts position, speed, angle, lane, type for each vehicle.
   - Converts speed ($m/s \times 3.6 = km/h$) and normalizes angle ($0–360^\circ$).
   - Maps internal junction edges (`:J1_...`) vs free inter-junction links (`J1_J2_...`).
   - Builds deterministic event ID (`gps_<vehicle_id>_<timestamp>`).
   - Validates required fields and types.
   - Streams line-by-line UTF-8 JSON to disk.
4. Cleanly closes TraCI / SUMO.

---

## 4. Replay Usage

The replay script `experiments/replay_gps.py` reads a previously generated `.jsonl` file **without launching SUMO**:

```bash
# Basic replay
python experiments/replay_gps.py data/output/gps/normal.jsonl

# Limit events displayed and adjust replay speed
python experiments/replay_gps.py data/output/gps/rush.jsonl --limit 50 --delay 0.01

# Replay summary only (no per-event printing)
python experiments/replay_gps.py data/output/gps/blocked_downstream.jsonl --quiet
```

### Replay Output Example

```text
timestamp=12.0 vehicle=car_west_1 speed=38.4 km/h segment=W0_J1 lane=W0_J1_0 pos=(15.2, 1.6)
timestamp=12.0 vehicle=car_west_2 speed=28.1 km/h segment=W0_J1 lane=W0_J1_1 pos=(8.5, 4.8)
...
==================================================
TRAFFICTWIN REPLAY SUMMARY
==================================================
File:               data/output/gps/normal.jsonl
Events replayed:    9,162
Valid events:       9,162
Invalid events:     0
Unique vehicles:    175
Vehicle types:      passenger: 175
Start time:         1.0 s
End time:           360.0 s
Duration:           359.0 s
Max speed:          49.9 km/h
Avg speed:          35.4 km/h
Junction hits:      J1: 412, J2: 398, J3: 385, J4: 370
==================================================
```

---

## 5. How to Regenerate Streams

To generate GPS-like streams for all four standard scenarios:

```bash
# Generate all 4 scenario streams (normal, rush, blocked_downstream, ambulance)
python experiments/generate_gps_events.py --all

# Or generate a single scenario
python experiments/generate_gps_events.py --scenario normal --steps 360
python experiments/generate_gps_events.py --scenario rush --steps 360
python experiments/generate_gps_events.py --scenario blocked_downstream --steps 360
python experiments/generate_gps_events.py --scenario ambulance --steps 360
```

Streams are saved to: `data/output/gps/<scenario>.jsonl`.
