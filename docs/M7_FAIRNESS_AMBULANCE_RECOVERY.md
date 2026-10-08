# Module M7: Fairness Debt, Staged Ambulance Priority, and Recovery

## Executive Summary
Module M7 delivers the authoritative final traffic-control intelligence layer for the TrafficTwin AI 4-junction urban corridor. It integrates three essential capabilities into the real-time control pipeline:
1. **Fairness Debt & Starvation Prevention**: Deterministic, explainable tracking of approach delay and missed service cycles to eliminate indefinite side-street starvation.
2. **Staged Route-Aware Ambulance Priority**: Proactive preemption along the emergency route ($J1 \rightarrow J2 \rightarrow J3 \rightarrow J4$) gated by downstream capacity protection.
3. **Post-Emergency Bounded Recovery**: Compensatory service allocation for cross-street approaches delayed by emergency preemption, bounded by strict timing caps.

---

## Authoritative Execution Order
TrafficTwin AI maintains an unalterable safety and capacity control hierarchy:

$$\mathbf{M3\ (Queue\text{-}Reactive\ Proposal)} \longrightarrow \mathbf{M7\ (Fairness\ /\ Emergency\ Policy)} \longrightarrow \mathbf{M6\ (Downstream\ Guard)} \longrightarrow \mathbf{M5\ (Safety\ Firewall)} \longrightarrow \mathbf{SUMO\ /\ TraCI}$$

```
                ┌───────────────────────────────────────┐
                │        M3: Queue-Reactive Engine      │
                │  - Computes local approach queues     │
                │  - Proposes EXTEND_GREEN / TRANSITION │
                └───────────────────┬───────────────────┘
                                    │
                                    ▼
                ┌───────────────────────────────────────┐
                │       M7: Intelligence & Policy       │
                │  - Staged Ambulance Preemption (EB)   │
                │  - Post-Emergency Bounded Recovery    │
                │  - Side-Street Fairness Debt Watch    │
                └───────────────────┬───────────────────┘
                                    │
                                    ▼
                ┌───────────────────────────────────────┐
                │     M6: Downstream Capacity Guard     │
                │  - Inspects downstream link occupancy │
                │  - Overrides with SPILLBACK_BLOCK if  │
                │    occupancy >= 85% (Critical)        │
                └───────────────────┬───────────────────┘
                                    │
                                    ▼
                ┌───────────────────────────────────────┐
                │        M5: Signal Safety Firewall     │
                │  - Min green (10s) & Max green (40s)  │
                │  - Mandatory Yellow (3s) & All-Red(2s)│
                │  - Strictly legal phase transitions   │
                └───────────────────┬───────────────────┘
                                    │
                                    ▼
                ┌───────────────────────────────────────┐
                │          SUMO Corridor / TraCI        │
                └───────────────────────────────────────┘
```

---

## Part A: Fairness Debt Tracker
### Mathematical Formulation
For each junction approach $a \in \{\text{main}, \text{cross}\}$:
$$\text{Fairness Debt}_a = \alpha \cdot \bar{W}_a + \beta \cdot W_{\max, a} + \gamma \cdot (N_{\text{missed}, a} \times 10.0)$$

Where:
- $\bar{W}_a$: Average waiting time of stopped vehicles on approach $a$ ($\alpha = 0.4$)
- $W_{\max, a}$: Maximum waiting time of any vehicle on approach $a$ ($\beta = 0.4$)
- $N_{\text{missed}, a}$: Number of full signal cycles the approach was queued without receiving green service ($\gamma = 0.2$)

### Starvation Detection & Action
- **Threshold**: $\text{Starvation Threshold} = 35.0\text{ debt points}$ or $W_{\max} \ge 90.0\text{s}$.
- **Decision Rule**: When side-street starvation risk is active:
  - If currently in **Main Green (Phase 0)** and $t_{\text{green}} \ge 10.0\text{s}$ (min green): Propose `START_TRANSITION` to Phase 1 (Yellow) to immediately schedule service for the starved approach.
  - If currently in **Cross Green (Phase 3)**: Grant green extension up to bounded maximum to clear the waiting queue and normalize debt.

---

## Part B: Staged Ambulance Priority
### Route & Geometry
- Emergency vehicle: `emerg_1` (`vType="ambulance"`, `vClass="emergency"`, departs at $t=50.0\text{s}$).
- Corridor route: Eastbound $W0\_J1 \rightarrow J1\_J2 \rightarrow J2\_J3 \rightarrow J3\_J4 \rightarrow J4\_E5$.

### Staged Workflow
1. **Detection**: Vehicle detection identifies `emerg_1` position, speed, and target junction stop-line.
2. **ETA Estimation**:
   $$\text{ETA} = \frac{\text{Distance to Stopline}}{\max(\text{Speed}, 2.0)}$$
3. **Staged Activation**: Priority activates only when $\text{ETA} \le \text{Lead Time}$ ($15.0\text{s}$).
4. **Downstream Capacity Gate (M6)**:
   - If downstream link occupancy $\ge 85\%$: Priority is held (`PRIORITY_DELAYED`) with reason `DOWNSTREAM_CAPACITY_CRITICAL` until the bottleneck clears.
   - If downstream link occupancy $< 85\%$: Priority is staged (`PRIORITY_STAGED`) to Eastbound Main Green (Phase 0).
5. **Firewall Safety Compliance (M5)**:
   - If opposing phase is active, min green ($10.0\text{s}$) is strictly satisfied before transitioning.
   - Transitions strictly follow legal clearance intervals: `Cross Green (3) -> Yellow (4) -> All-Red (5) -> Main Green (0)`.
   - Never triggers network-wide "all green" or direct phase jumps.

---

## Part C: Post-Emergency Bounded Recovery
1. **Passage Detection**: When the ambulance clears the stop-line into the downstream segment, preemption at the current junction terminates.
2. **Compensatory Green Allocation**:
   $$\text{Recovery Green Duration} = \max\left(10.0\text{s},\, \min(\text{Fairness Debt}_{\text{cross}} \times 0.8,\, 25.0\text{s})\right)$$
3. **Recovery Cap**: Hard timeout capped at $60.0\text{s}$ prevents perpetual recovery mode.
4. **Normalized Return**: Once the allocated recovery green completes, fairness debt resets and control transitions back to standard adaptive operation.

---

## Simulation Verification & Empirical Results
Executed via `experiments/run_ambulance.py --scenario ambulance`:
- **Ambulance Travel Time**: $112.0\text{s}$ across 1.0 km 4-junction corridor.
- **Ambulance Delay**: $9.0\text{s}$ (minimal delay meeting all safety clearance intervals).
- **Cross-Road Average Delay**: $5.54\text{s}$ (protected from excessive starvation).
- **Peak Fairness Debt**: $15.84\text{ debt points}$ (safely below starvation threshold).
- **Total Recovery Actions**: 8 bounded recovery stages executed across J1–J4.
- **Safety Record**: Zero collisions, zero clearance bypasses, 100% firewall validation pass rate.
