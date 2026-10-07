# TrafficTwin AI — Roles

## Team tracks (Spirit, 5 people; names to be assigned)
| Track | Owns | Modules |
|---|---|---|
| A Simulation Engineer | SUMO net, routes, scenarios, TraCI adapter, simulation metrics, experiment runner | M1, M2, M12 runs |
| B Decision Engine Engineer | state/forecast, spillback guard, fairness, firewall, ambulance + recovery, plan evaluator | M5, M6, M7, M11 |
| C API/Security Engineer | FastAPI, WebSocket, audit log, auth/role guard, validation, fault injector, reliability | M3, M8, M10 |
| D Frontend/Product Engineer | replay + live dashboard, decision log, comparison, UX, (P2) public page | M4, M9 |
| E QA/Docs/Deck Lead | tests, quality checks, README, demo script/recording, deck, third-party notices, GitHub board | M0, M12, M13 |
Every module has one owner and one reviewer (someone else who can explain it).

## Application roles
| Role | Can | Cannot |
|---|---|---|
| Viewer | read state, decisions, audit | approve or change anything |
| Operator | everything Viewer can; approve simulation-only signal actions | edit config or users |
| Admin (P2) | manage local demo users and fallback plan; read all audit data | bypass the firewall |

## Security rule
No role calls TraCI directly. All actions go API → authorization → safety firewall → TraCI adapter.
