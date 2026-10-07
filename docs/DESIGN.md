# TrafficTwin AI — Product & Technical Design
(UI layout, colors and component tree: see `UI_DESIGN.md`.)

## Problem
Local, queue-only signal decisions release traffic into full downstream roads, causing spillback and corridor gridlock. Emergency priority can create a second jam, side roads can starve, and signals have no safe fallback when data or AI fails.

## Users
- Operator: monitors the corridor, reviews recommendations, approves simulation actions.
- Engineer: compares controllers and tests scenarios.
- Admin (P1): access and configuration.
- Public viewer (P2): sanitized read-only status.

## Product boundary
Decision support and simulation software. It does not control real municipal signals. Real deployment needs traffic-authority approval and certified controller integration.

## Core flow
Simulated GPS (SUMO) → estimator → wave forecast → candidate plans → Digital Twin score → safety firewall → apply in SUMO (or operator approval) → metrics + audit → recovery.

## Modules and contracts
| Module | Consumes | Produces |
|---|---|---|
| M1 SUMO corridor | scenario, seed | simulation + tripinfo/fcd/queue/summary |
| M2 estimator + baselines | TraCI state | link/junction state, metrics CSV |
| M3 GPS stream | TraCI vehicles | `gps` events, recorded .jsonl |
| M5 firewall | proposed action + state | valid/invalid + failed checks |
| M6 controller | state + forecast | action + decision card |
| M7 ambulance/recovery | ambulance events + state | staged phases, recovery plan |
| M8 backend | all events | REST + `/ws/live`, audit log |
| M9 dashboard | `/ws/live`, CSV | operator views |
| M10 reliability | trust, faults | mode events, fallback plan use |
| M11 twin | state snapshot | Plan A/B/C scores |

Event shapes live in `shared/schemas` (frozen at M3). Types: `gps`, `link`, `junction`, `decision`, `mode`.

## Decision rules
- Never release into a link with `free_capacity < expected_released + BUFFER`.
- Valid transitions only; respect min/max green, yellow, all-red, no conflicting greens.
- Fairness override when any approach exceeds MAX_WAIT (except emergency).
- Ambulance: ETA per junction, clear downstream first, staged green, then bounded recovery.
- Low trust ⇒ Safe Adaptive; no data / AI fault / unsafe command ⇒ Local Safe (stored plan); AI resumes after Shadow Recovery stable window.
- Every decision has reasons, checks, predicted effect; measured effect added after 60 s.

## Architecture rules
1. Modules fail independently (stream, controller, API, frontend, SUMO).
2. Frontend never calls TraCI. Only `firewall.apply()` writes signals.
3. Every approval and action creates an audit event.
4. Local files/SQLite remain the fallback if services fail.
5. Source adapter is swappable: SUMO GPS now, GTFS-Realtime / fleet GPS later, cameras as a future optional adapter.

## Known limits (state them)
GPS covers only participating vehicles; data is simulated; no pedestrians; emissions are an idle-time proxy; twin is a lightweight queue-propagation model; results do not transfer automatically to real roads.
