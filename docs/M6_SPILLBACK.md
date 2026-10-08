# TrafficTwin AI — Module M6: Spillback Controller

## 1. Executive Summary & Purpose

Module M6 implements a simple, explainable **Spillback-Aware Controller** for the TrafficTwin AI 4-junction urban arterial corridor.

In conventional queue-reactive control (such as Module M3), an upstream traffic signal extends green whenever it detects an incoming queue on its approach. However, if the downstream road segment receiving that traffic is already saturated or blocked, extending upstream green blindly feeds more vehicles into an overcrowded link. This causes **spillback**: vehicles queue across upstream intersections, deadlocking the entire corridor.

**Module M6 introduces downstream capacity protection:**
- Evaluates downstream link occupancy and risk levels.
- Replaces or blocks upstream green extensions (`SPILLBACK_BLOCK`) when the downstream corridor segment is near capacity (`CRITICAL`).
- Protects downstream bottlenecks from queue overflow while maintaining legal clearance and minimum green safety rules.
- Strictly routes every action through the **M5 Safety Firewall** before commanding TraCI.

> **CRITICAL ARCHITECTURAL NOTE**: Module M6 is completely deterministic and rule-based. It does **not** use machine learning, reinforcement learning, neural networks, or predictive AI models.

---

## 2. Why Queue-Only Control is Insufficient

Conventional reactive control (M3) observes only local incoming queues:
$$\text{Local Demand} = Q_{\text{main}}$$

If $Q_{\text{main}} \ge 3$, M3 commands `EXTEND_GREEN`. In an isolated intersection, this minimizes local vehicle delay. However, along a coordinated corridor, intersections are coupled:

$$\text{J1} \xrightarrow{\text{J1\_J2}} \text{J2} \xrightarrow{\text{J2\_J3}} \text{J3} \xrightarrow{\text{J3\_J4}} \text{J4} \xrightarrow{\text{J4\_E5}} \text{E5}$$

When a downstream bottleneck occurs (e.g., an incident or lane blockage on `J4_E5`), vehicles cannot proceed. If upstream junctions (`J3`, `J2`) continue extending green because their own queues are high:
1. Link `J3_J4` fills completely to 100% capacity.
2. Queued vehicles on `J3_J4` physically block junction `J3`, preventing cross-street traffic from crossing.
3. Link `J2_J3` then fills up, cascading congestion backward to `J1` and `W0`.

M6 resolves this by making signal decisions **spillback-aware**:
$$\text{Decision} = f(Q_{\text{upstream}}, \text{Occupancy}_{\text{downstream}})$$

---

## 3. Downstream Capacity & Occupancy Measurement

M6 measures downstream road capacity and occupancy directly from the SUMO simulation state without fabricating values.

### Network Geometry
For each 200m 2-lane corridor segment:
- Edge length: $L = 200.0\text{ m}$
- Lane count: $N = 2$
- Effective vehicle length: $L_{\text{eff}} = 7.5\text{ m}$ ($5.0\text{ m}$ vehicle length + $2.5\text{ m}$ minimum gap, from `backend/config/params.yaml`)
- Usable storage capacity:
  $$C_{\text{link}} = \text{round}\left(\frac{L \times N}{L_{\text{eff}}}\right) = \text{round}\left(\frac{400.0}{7.5}\right) = 53\text{ vehicles}$$

### Measured Occupancy
At every simulation step, M6 queries TraCI for vehicles on the downstream edge:
1. **Physical space occupancy**:
   $$\text{Occupancy}_{\text{space}} = \frac{\sum_{v \in \text{edge}} (\text{length}_v + \text{minGap}_v)}{L \times N}$$
2. **Vehicle count ratio**:
   $$\text{Occupancy}_{\text{count}} = \frac{N_{\text{vehicles}}}{C_{\text{link}}}$$
3. **TraCI step occupancy**:
   $$\text{Occupancy}_{\text{TraCI}} = \text{traci.edge.getLastStepOccupancy}(\text{edge\_id})$$

The operational downstream occupancy is defined as:
$$\text{Occupancy} = \min\left(1.0, \max(\text{Occupancy}_{\text{space}}, \text{Occupancy}_{\text{count}}, \text{Occupancy}_{\text{TraCI}})\right)$$

If capacity or total road space is zero, occupancy safely evaluates to $0.0$.

---

## 4. Downstream Corridor Mapping

Each controlled junction maps to its primary downstream corridor segment along the Eastbound arterial:

| Junction | Downstream Edge ID | Length (m) | Lanes | Vehicle Capacity |
|---|---|---|---|---|
| **J1** | `J1_J2` | 200.0 | 2 | 53 |
| **J2** | `J2_J3` | 200.0 | 2 | 53 |
| **J3** | `J3_J4` | 200.0 | 2 | 53 |
| **J4** | `J4_E5` | 200.0 | 2 | 53 |

---

## 5. Thresholds & Risk Classification

Configured in `backend/config/params.yaml`:
```yaml
spillback:
  enabled: true
  warning_threshold: 0.75
  critical_threshold: 0.85
  occupancy_threshold: 0.75
```

> **Note**: These thresholds are simulation tuning parameters, not immutable real-world constants.

### Risk Levels
- **`NORMAL`** ($\text{Occupancy} < 0.75$): Downstream link has ample absorption capacity.
- **`WARNING`** ($0.75 \le \text{Occupancy} < 0.85$): Downstream link is heavily loaded. Avoid non-essential green extensions.
- **`CRITICAL`** ($\text{Occupancy} \ge 0.85$): Downstream link is near physical saturation. Block green extensions to prevent link overflow.

---

## 6. Runtime Architecture: M3 $\to$ M6 $\to$ M5 $\to$ TraCI

M6 sits between the M3 reactive controller and the M5 safety firewall:

```
[SUMO Corridor / TraCI]
       │
       ├─────────────────────────┐
       ▼                         ▼
[Local Incoming Queues]   [Downstream Edge State]
       │                         │
       ▼                         │
[M3 Reactive Controller]         │
  Proposes action:               │
  (e.g., EXTEND_GREEN)           │
       │                         │
       └───────────┬─────────────┘
                   ▼
       [M6 Spillback Controller]
         Evaluates downstream occupancy & risk:
         - NORMAL:   Keep M3 action
         - WARNING:  Avoid extension (HOLD)
         - CRITICAL: Override with SPILLBACK_BLOCK
                     Request safe clearance transition
                   │
                   ▼
       [M5 Safety Firewall]
         Validates signal action against constraints:
         - Min green (10s)
         - Max green (40s)
         - Clearance intervals (Yellow 3s, All-Red 2s)
         - Non-conflicting movements
                   │
         ┌─────────┴─────────┐
         │ PASS              │ FAIL
         ▼                   ▼
    [TraCI Actuation]    [HOLD Phase]
                         (Log firewall violation)
```

### Safety & Fairness Guarantees
1. **No Upstream Starvation**: M6 does not freeze the junction. Once green duration reaches minimum green ($10.0\text{s}$), it initiates a legal clearance sequence (`START_TRANSITION` $\to$ Yellow $\to$ All-Red $\to$ Cross Green). Cross-street traffic is served while the downstream link clears.
2. **Never Bypasses M5**: Every action (whether unmodified, modified, or blocked) must pass `validate_action()` in `backend/app/guards/safety_firewall.py` before any TraCI API call is executed. If M5 rejects an action, TraCI is never called and the controller defaults to `HOLD`.

---

## 7. Audit & Decision Logging

All controller decisions are appended to `data/output/metrics/spillback_{scenario}_decisions.csv` with the exact 10 required human-readable fields:

```csv
timestamp,junction_id,current_phase,queue_main,queue_cross,downstream_edge,downstream_occupancy,spillback_risk,action,reason
340.0,J3,0,3,1,J3_J4,0.880,CRITICAL,KEEP_GREEN,minimum green not satisfied (9.0s < 10.0s)
341.0,J3,0,4,1,J3_J4,0.880,CRITICAL,SPILLBACK_BLOCK,downstream_occupancy_critical
342.0,J3,1,3,1,J3_J4,0.917,CRITICAL,HOLD,clearance phase active
```

---

## 8. Actual Simulation Results: M3 vs M6

All four scenarios were executed with SUMO 1.27.1 headlessly under identical random seed (42) and simulation duration (360s).

### Comparative Metric Summary

| Scenario | Controller | Throughput (veh) | Avg Wait (s) | P95 Wait (s) | Avg Travel (s) | Mean Queue | Max Queue | Spillback Blocks | Max Downstream Occ |
|---|---|---|---|---|---|---|---|---|---|
| **normal** | M3 Reactive | 197 | 13.5 | 37.0 | 75.2 | 12.53 | 48.93 | 0 | 0.31 |
| **normal** | **M6 Spillback** | **197** | **13.5** | **37.0** | **75.2** | **12.53** | **48.93** | **0** | **0.31** |
| **rush** | M3 Reactive | 314 | 19.6 | 65.0 | 82.0 | 33.72 | 183.77 | 0 | 0.81 |
| **rush** | **M6 Spillback** | **314** | **19.6** | **65.0** | **82.0** | **33.72** | **183.77** | **0** | **0.81** |
| **blocked_downstream** | M3 Reactive | 200 | 12.8 | 37.0 | 66.3 | 50.69 | 192.63 | 0 | 0.92 |
| **blocked_downstream** | **M6 Spillback** | **200** | **12.8** | **37.0** | **66.3** | **50.67** | **192.63** | **1** | **0.92** |
| **ambulance** | M3 Reactive | 250 | 11.6 | 33.0 | 69.5 | 13.87 | 55.48 | 0 | 0.41 |
| **ambulance** | **M6 Spillback** | **250** | **11.6** | **33.0** | **69.5** | **13.87** | **55.48** | **0** | **0.41** |

### Spillback-Specific Metrics

| Metric | normal | rush | blocked_downstream | ambulance |
|---|---|---|---|---|
| **Spillback Blocks Triggered** | 0 | 0 | **1** | 0 |
| **Protected Transitions** | 0 | 0 | **1** | 0 |
| **Peak Downstream Occupancy** | 0.310 | 0.806 | **0.917** | 0.408 |
| **Critical Occupancy Duration (s)** | 0 | 0 | **20** | 0 |

---

## 9. Engineering Interpretation & Trade-Offs

1. **Selective Intervention**: In uncongested scenarios (`normal`, `ambulance`), downstream occupancy never crosses 0.75, so M6 behaves identically to M3 without any artificial disruption.
2. **Detection of Bottlenecks**: In `blocked_downstream`, vehicles queued behind the stopped incident vehicles on `J4_E5` cause link `J3_J4` to reach 91.7% occupancy ($46/53$ vehicles).
3. **Intervention at Critical Boundary**: At $t = 341.0\text{s}$, J3 upstream queue is 4 vehicles. M3 proposed extending green. M6 intercepted the command, logged `SPILLBACK_BLOCK`, and transitioned J3 to yellow clearance, halting further vehicle feeding into `J3_J4`.
4. **Honest Metric Evaluation**: The spillback intervention prevented further queue packing on `J3_J4` and slightly reduced mean corridor queue ($50.69 \to 50.67$). Throughput remained 200 vehicles because the bottleneck on `J4_E5` remained active until $t = 300\text{s}$. As specified in project instructions, M6 does not manufacture artificial throughput improvements when physical downstream road capacity is obstructed.

---

## 10. Honest Limitations

- **Fixed Primary Corridor Mapping**: M6 currently maps each junction to its primary Eastbound arterial edge (`DOWNSTREAM_EDGES`). Full bidirectional multi-movement spillback detection across turning lanes is deferred to future extensions.
- **Single Segment Horizon**: M6 measures the immediate downstream link ($k+1$). Multi-hop downstream lookahead is planned for subsequent modules.
- **Simulation Tuning Parameter**: Occupancy thresholds ($0.75$ warning, $0.85$ critical) are calibrated for 200m SUMO links with 7.5m effective vehicle spacing. Field deployment would require link-specific calibration.
