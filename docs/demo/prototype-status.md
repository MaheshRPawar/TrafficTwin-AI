# TrafficTwin AI — Prototype Status

## Overview
**Project Name:** TrafficTwin AI  
**Problem Domain:** AI-Powered Traffic Flow Optimization & Safety  
**Phase:** Hackathon Working Prototype Validation

---

## 1. What Runs Today
- **Microsimulation Engine:** Eclipse SUMO 1.27.1 (`sumo-gui`) running a multi-lane urban intersection scenario (`SUMOSample/Sample.net.xml`, `Sample.sumocfg`).
- **TraCI Runtime Connection:** Python 3.14 interacting directly with the live simulation via TraCI socket interface on port/default loopback.
- **Traffic Signal State Monitoring:** Python queries junction `J6` traffic light phase in real-time (`traci.trafficlight.getPhase('J6')`).
- **Dynamic Signal Priority / Preemption Control:**
  - Real-time vehicle telematics inspection (`traci.vehicle.getIDList()`, `traci.vehicle.getTypeID(veh)`).
  - Approaching vehicle distance & next traffic signal detection (`traci.vehicle.getNextTLS(veh)`).
  - Dynamic phase switching and green-phase extension (`traci.trafficlight.setPhaseDuration()`) to clear priority corridors safely.
  - Automatic restoration to default cyclic signal operation after vehicle passage.

---

## 2. Exact Run Commands

### Option A: Direct Python Execution
```powershell
# From project root:
cd d:\X\Aarambh-WCE\Project\SUMO-Traffic-Simulator-Tutorial-Prototype
python Traci4.py
```

### Option B: PowerShell Automation Script
```powershell
.\scripts\run_prototype.ps1
```

### Option C: Windows Batch Runner
```cmd
.\scripts\run_prototype.bat
```

---

## 3. What the Screen Recording Proves
1. **Bi-directional Integration:** Python/TraCI successfully connects to and commands Eclipse SUMO in real time.
2. **Deterministic Signal Manipulation:** Traffic signals at intersection `J6` change states according to programmed logic rather than arbitrary SUMO fixed schedules.
3. **Emergency Corridor Clearing:** When an emergency vehicle (`emerg_1`) appears on corridor `E5`, the Python controller detects it, preempts the cross-traffic green phase, grants green priority (`rGGr`), and safely resets.
4. **Foundation for Digital Twin:** Proves the closed-loop control architecture (Sensing -> Logic -> Actuation) necessary for future AI/RL model deployment.

---

## 4. What Is Roadmap Only (Honest Disclaimers)
- **Deep Reinforcement Learning (DQN / PPO):** Multi-agent RL policy training is currently roadmap work; today's prototype demonstrates the actuation pipeline and rule-based preemption.
- **Physical GPS / Real-world Telematics:** Physical hardware integration and edge sensor feeds are future milestones; simulated telemetry in SUMO serves as the surrogate.
- **Real Municipal Deployment:** Real-world traffic signal cabinet controllers (NEMA TS2/ATC) require specialized field hardware, safety certification, and municipal partnerships.

---

## 5. Attribution
- **Simulation Scenario & Controller Base:** Derived from [RoadwayVR/SUMO-Traffic-Simulator-Tutorial](https://github.com/RoadwayVR/SUMO-Traffic-Simulator-Tutorial).
- **License:** MIT License.
- **Core Engine:** Eclipse SUMO (Simulation of Urban MObility) by the German Aerospace Center (DLR) (EPL-2.0 / GPL-2.0).
