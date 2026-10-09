# Document 06 — Algorithms & Decision Logic

## 1. Algorithmic Overview

TrafficTwin AI uses **rigorous, deterministic traffic engineering algorithms** rather than ungrounded black-box models. Every decision is mathematically verifiable and explainable.

---

## 2. Algorithm 1: Queue-Reactive Controller (Module M3)

- **Purpose**: Adapt green duration dynamically based on real-time vehicle arrivals.
- **Source File**: [`experiments/reactive_controller.py`](file:///experiments/reactive_controller.py)
- **Mathematical Logic**:
  - Main Approach Queue: $Q_{main} = \sum_{\text{main lanes}} \text{haltingVehicles}$
  - Cross Approach Queue: $Q_{cross} = \sum_{\text{cross lanes}} \text{haltingVehicles}$
  - **Extension Condition**:
    $$\text{If } Q_{main} \ge Q_{th} \text{ and } (G_{elapsed} + \Delta G) \le G_{max} \implies \text{EXTEND\_GREEN}(\Delta G)$$
  - **Transition Condition**:
    $$\text{If } Q_{main} < Q_{th} \text{ and } G_{elapsed} \ge G_{min} \text{ and } Q_{cross} \ge Q_{th} \implies \text{TRANSITION\_CROSS}()$$
- **Parameters & Constants**:
  - $Q_{th} = 3\text{ vehicles}$ (queue activation threshold)
  - $\Delta G = 5.0\text{ seconds}$ (extension increment)
  - $G_{min} = 10.0\text{ seconds}$ (minimum green)
  - $G_{max} = 40.0\text{ seconds}$ (maximum green cap)
- **Viva Defense**: *"M3 adapts green time to queues, but it is downstream-blind; it does not know if the next intersection is blocked."*

---

## 3. Algorithm 2: Spillback Guard & Downstream Capacity (Module M6)

- **Purpose**: Prevent gridlock by blocking green lights when the downstream road segment has no physical space left.
- **Source File**: [`backend/app/guards/spillback_guard.py`](file:///backend/app/guards/spillback_guard.py), [`experiments/spillback_controller.py`](file:///experiments/spillback_controller.py)
- **Physical Capacity Formula**:
  $$N_{cap} = \left\lfloor \frac{L_{edge}}{l_{veh} + d_{gap}} \right\rfloor \times N_{lanes}$$
  - $L_{edge} = 250.0\text{ m}$ (arterial block length)
  - $l_{veh} = 5.0\text{ m}$ (average vehicle length)
  - $d_{gap} = 2.5\text{ m}$ (minimum stopped headway)
  - For a 2-lane segment: $N_{cap} = \lfloor 250 / 7.5 \rfloor \times 2 = 33 \times 2 = 66\text{ vehicles}$. (For our modeled corridor: 53 vehicles accounting for lane merges).
- **Occupancy Formula**:
  $$\text{Occ}_{down} = \frac{N_{veh\_on\_downstream\_edge}}{N_{cap}}$$
- **Three-Tier Action Matrix**:
  1. **Normal Band ($\text{Occ} < 75\%$)**: Action = `PASS`. No intervention needed.
  2. **Warning Band ($75\% \le \text{Occ} < 85\%$)**: Action = `PASS_WITH_WARNING`. Green extensions allowed with caution.
  3. **Critical Band ($\text{Occ} \ge 85\%$)**: Action = `BLOCK_EXTENSION`. **Intercepts and cancels** the proposed green extension. Forces yellow clearance.

---

## 4. Algorithm 3: Safety Firewall & Legal Transitions (Module M5)

- **Purpose**: Deterministic, immutable safety gate protecting against illegal signal transitions, phase skipping, or clearance violations.
- **Source File**: [`backend/app/guards/safety_firewall.py`](file:///backend/app/guards/safety_firewall.py)
- **Enforced Safety Invariants**:
  1. **Minimum Green Invariant**: A phase transition from Green to Yellow is strictly forbidden if elapsed green $t_{green} < G_{min} = 10.0\text{s}$.
  2. **Maximum Green Invariant**: Elapsed green $t_{green}$ cannot exceed $G_{max} = 40.0\text{s}$.
  3. **Clearance Integrity**: Direct jumps from Green to Red or Green to Green are rejected. All transitions must follow:
     $$\text{Green (0)} \xrightarrow{t \ge 10s} \text{Yellow (1) [3s]} \rightarrow \text{All-Red (2) [2s]} \rightarrow \text{Cross Green (3)} \xrightarrow{t \ge 10s} \text{Yellow (4) [3s]} \rightarrow \text{All-Red (5) [2s]} \rightarrow \text{Green (0)}$$
  4. **Clearance Phase Hold**: During Yellow or All-Red, green extensions are rejected.

---

## 5. Algorithm 4: Fairness Debt & Starvation Risk (Module M7)

- **Purpose**: Prevent side-street traffic from waiting indefinitely while main arterial traffic is extended.
- **Source File**: [`experiments/emergency_controller.py`](file:///experiments/emergency_controller.py)
- **Debt Accumulation Formula**:
  $$D_{cross}(t) = \begin{cases} D_{cross}(t-1) + \Delta t & \text{if phase is arterial green and } Q_{cross} > 0 \\ 0 & \text{when cross-street green is served} \end{cases}$$
- **Starvation Rule**: If $D_{cross} \ge T_{starve} = 30.0\text{s}$, the system flags `STARVATION_RISK` and prioritizes cross-street service.

---

## 6. Algorithm 5: Emergency Vehicle Preemption & Downstream Gating (Module M7)

- **Purpose**: Provide rapid, safe corridor transit for ambulances without driving them into gridlocked links.
- **Source File**: [`experiments/emergency_controller.py`](file:///experiments/emergency_controller.py)
- **Detection & Staging Logic**:
  - Distance: $d_{amb} = \text{distance from vehicle to junction stop line}$.
  - Estimated Time of Arrival: $\text{ETA} = d_{amb} / v_{amb}$.
  - Preemption Window: Triggered when $\text{ETA} \le 15.0\text{s}$.
- **Downstream Gating Rule**:
  - If downstream link occupancy $\text{Occ}_{down} < 85\%$: Grant immediate green preemption.
  - If downstream link is $\ge 85\%$ (blocked): **Delay preemption** and initiate downstream green flushing to clear the exit before the ambulance arrives.
- **Staged Recovery**: After the emergency vehicle clears, the controller grants extended green ($G_{recovery} = 25\text{s}$) to starved cross-streets to rapidly reset fairness debt.

---

## 7. Algorithm 6: Digital Twin Plan A/B/C Evaluator (Module M9)

- **Purpose**: Multi-criteria digital twin evaluation comparing 3 distinct operational strategies before actuation.
- **Source File**: [`backend/app/planner/evaluator.py`](file:///backend/app/planner/evaluator.py)
- **Candidate Plans**:
  - **Plan A (Progression)**: Maintain current green progression.
  - **Plan B (Approach Clearance)**: Extend green by $+5\text{s}$ for approach queue clearance.
  - **Plan C (Downstream Flushing & Coordination)**: Force clearance to flush downstream link.
- **Multi-Objective Penalty Function**:
  $$S_{total} = w_d \cdot S_{delay} + w_q \cdot S_{queue} + w_{sp} \cdot S_{spillback} + w_f \cdot S_{fairness} + w_e \cdot S_{emergency}$$
- **Scoring Weights** (from [`params.yaml`](file:///backend/config/params.yaml)):
  - Delay Weight: $w_d = 1.0$
  - Queue Weight: $w_q = 1.0$
  - Spillback Weight: $w_{sp} = 3.0$ (Spillback carries 3x penalty!)
  - Fairness Weight: $w_f = 1.5$
  - Emergency Weight: $w_e = 5.0$ (Emergency carries highest priority!)
- **Selection Rule**:
  $$\text{Selected Plan} = \arg\min_{p \in \text{Valid Plans}} S_{total}(p)$$
  If a plan violates M5 Safety Firewall or M6 Spillback limits, it is marked `INVALID` and discarded. If all plans fail, TrafficTwin falls back to `SAFE_ADAPTIVE` baseline.
