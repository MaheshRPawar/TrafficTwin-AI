# TrafficTwin AI — Testing Plan

Tests are written with each module and are part of its gate. Pure decision/safety logic must be testable without SUMO GUI or the frontend.

## Layers
- Unit: spillback calculation, fairness debt, phase validation, firewall checks, plan scoring, mode transitions, decision explanations, trust score
- Integration: state adapter vs SUMO, controller → firewall → TraCI mapping, audit storage, API role checks
- Scenario: normal, rush, blocked_downstream, ambulance, planner failure, GPS outage, API/UI failure, determinism (same seed twice ⇒ same metrics)

## Required safety tests
| Test | Expected |
|---|---|
| Invalid phase transition | rejected |
| Green > max / < min | rejected |
| Missing yellow/all-red | rejected |
| Conflicting greens | rejected |
| Downstream saturated | upstream release blocked + logged |
| Fairness debt over limit | service forced unless emergency |
| Ambulance with blocked downstream | downstream cleared first, staged green, no all-green |
| After ambulance | recovery logged and bounded |
| Planner/forecast exception | Safe Adaptive |
| Safe controller exception | Local Safe fixed plan |
| GPS outage | Local Safe ≤ GPS_STALE_S + 1 s, traffic keeps moving |
| Data restored | Shadow Recovery, resume only after stable window |
| Unauthorized approval | HTTP 403 |
| Missing recommendation | HTTP 404 |
| Invalid payload | HTTP 422 |
| Replay of a full run | 0 invalid commands reached TraCI |
| Summary vs CSV | summary equals CSV values |

## Failure table (independent failure)
Frontend down, API down, database down, planner down, SUMO GUI down, internet down: each must leave the safe core running (see ARCHITECTURE §8a).

## Commands
```
make test            # pytest
ruff check .
bandit -r backend sumo experiments
pip-audit
```

## Evidence
Save test output, scenario metrics, decision JSON, screenshots and the demo video under `data/demo_assets/`.
