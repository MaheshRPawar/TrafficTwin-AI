# TrafficTwin AI — Product Requirements Document (PRD)

Event: AARAMBH WCE-HACKATHON 2026 · Problem: "AI-Powered Traffic Flow Optimization"
Version 1.0 · Status: LOCKED SCOPE

## 1. Product summary
TrafficTwin AI is a software-only, simulation-driven Digital Twin for a 4-junction traffic corridor. It ingests (simulated) bus/taxi/vehicle GPS, predicts congestion waves, tests safe signal plans, blocks actions that would cause downstream spillback, runs staged ambulance preemption with fairness recovery, and falls back to safe control when AI or data fails.
Tagline: Predict. Simulate. Protect. Recover.

## 2. Problem
- Local green extension pushes vehicles into a full downstream link → spillback → corridor gridlock.
- Emergency preemption creates a second congestion problem (cross-traffic backlog, blocked downstream).
- High-volume roads can starve side roads.
- GPS, network or AI failure must not stop traffic.
- Operators need explainable, testable decisions, not black boxes.

## 3. Official requirement → feature map
| Official requirement | TrafficTwin feature | Priority |
|---|---|---|
| Centralized software platform | FastAPI control engine + React control room | P0 |
| Ingest real-time transit/ride-share GPS | SUMO-generated GPS-like event stream (source-agnostic adapter) | P0 |
| Predict congestion zones | Congestion-wave forecast per link (rule-based) | P0 |
| Dynamically adjust signal timing | TraCI phase control through safety firewall | P0 |
| Multi-intersection coordination | Downstream capacity guard across J1–J4 | P0 |
| Measurable benefit | Fixed vs Reactive vs TrafficTwin, same seed | P0 |

## 4. Users
1. Traffic control-room operator: sees state, forecast, decisions, approves or overrides.
2. Traffic engineer: compares plans, reads metrics, tests scenarios.
3. Hackathon judge: must understand value and see a working demo in under 3 minutes.

## 5. Goals / Non-goals
Goals: reliable 4-junction prototype; measurable results from SUMO; explainable decisions; visible fail-safe.
Non-goals: physical hardware, IoT, cameras, real signal control, city-scale sim, deep RL/MARL, blockchain, AR/VR, chatbot, mobile app, proprietary Uber/Ola/Google data.

## 6. Feature scope
MUST (P0): corridor in SUMO; GPS-like stream; traffic state estimator; three controllers (fixed, reactive, TrafficTwin); downstream capacity guard; fairness debt; safety firewall; ambulance staged preemption + recovery; Local Safe fallback; metrics logger; decision cards; live dashboard; recorded demo fallback.
SHOULD (P1): Plan A/B/C twin evaluator; bus bounded priority; GPS trust score; Safe Adaptive mode; Shadow Recovery; one incident playbook (blocked downstream).
OPTIONAL (P2): rain slowdown, road closure, ML forecast, 6 junctions, Docker Compose, cloud deploy.

## 7. Demo scenarios
S1 rush-hour directional surge · S2 blocked downstream link · S3 ambulance during rush hour · S4 GPS/network failure · S5 (optional) closure or rain.

## 8. Success metrics (all measured from SUMO, never invented)
avg wait, p95 wait, avg/max queue, throughput, avg travel time, spillback events, ambulance delay, bus delay, max cross-road wait, recovery time, idle-emission proxy, decision time, fail-safe activations.
Success = TrafficTwin reported honestly against both baselines on identical seeds; any trade-offs are stated.

## 9. Positioning (must be used in all materials)
"Human-in-the-loop decision-support and simulation platform. Real deployment requires traffic-authority approval and certified signal-controller integration."
Never claim: controls real city signals; proven real-world gains; results not produced by our runs.

## 10. Assumptions & risks
Assumptions: 5-member team working in parallel tracks, native SUMO install, laptop demo. Real timeline: online presentation round (R1) with a partial prototype, then the on-site event; total build budget 24 hours. Risks: see TASKS.md §Risks.

## 11. Release plan (24 build-hours)
- Block A, R1 (H0–H8): corridor, fixed vs reactive baselines on identical seeds, spillback visible, GPS-like stream recorder, replay dashboard, 7-slide deck. Tag `r1-prototype`.
- Block B, event (H8–H24): firewall, TrafficTwin controller (guard, fairness, forecast, decision cards), ambulance staging + recovery, API + audit + approval, dashboard, fail-safe modes, Twin A/B/C lite, evidence, quality checks, demo pack. Freeze at H22.
- Optional: public advisory page, bus priority, trust score, ML forecast.
- Disclosure: code built before the event is tagged `r1-prototype` and declared in the README.

## 12. MVP user stories
- Operator sees J1–J4 queues, phases, mode and spillback risk.
- Operator sees a recommendation with reason, safety checks and predicted effect, and can approve a simulation action.
- Operator sees ambulance staged priority followed by recovery.
- Viewer can read state and audit log but cannot approve (HTTP 403).
- Engineer compares Fixed vs Reactive vs TrafficTwin on the same seed.
- Every action is in the audit log; the system keeps running safely if the planner, API, UI or feed fails.

## 13. Roles
Operator (approve simulation actions), Viewer (read-only), Admin (P2: config, users). See ROLES.md.
