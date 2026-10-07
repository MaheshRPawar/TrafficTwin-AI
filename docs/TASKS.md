# TrafficTwin AI — Tasks (24 build-hours, module by module)

Rule: **one module → one test → one proof → one commit → one push → next module.** A module is DONE only when its gate passes. Never start the next module on a broken one.

## Time budget
- Total build budget: **24 wall-clock hours** with 5 people working in parallel tracks. (Solo or 2 people cannot do this; cut P1 per the cut rules.)
- Block A (before/for the online round R1): H0–H8, modules M0–M4. Ends with tag `r1-prototype`.
- Block B (on-site event, 48-hour window): H8–H24, modules M5–M13. The remaining event hours are buffer: sleep, rehearsal, fixes. No new features in the buffer.
- Checkpoint A = H18: end-to-end demo path works. FEATURE FREEZE = H22.

## Tracks (who owns what)
A Simulation · B Decision engine · C API/Security · D Frontend/Product · E QA/Docs/Deck. See ROLES.md.

## Module map
| Module | Block | Hours | Owner | Issue | Gate (must pass to push) | Tag |
|---|---|---|---|---|---|---|
| M0 Repo + tooling | A | H0–1 | E | TT-01 | `make test` runs, `sumo --version` ok, docs in place, board + issues created | m0-ready |
| M1 SUMO corridor | A | H1–4 | A | TT-02 | normal/rush/blocked_downstream run headless, no collisions, same seed ⇒ identical routes, 4 output files written | m1-sumo-ok |
| M2 Baselines + metrics | A | H4–6 | A | TT-03 | fixed vs reactive on same seed, metrics CSV, one comparison chart | m2-baselines-ok |
| M3 GPS stream + recorder | A | H6–7 | C | TT-04 | events every 2 s match schema; recorded .jsonl replays | m3-stream-ok |
| M4 Replay dashboard | A | H6–8 | D | TT-05 | opens offline, shows signals/queues/link colors from recording; backup video | m4-replay-ok |
| R1 freeze | A | H8 | all | — | demo runs 3× in a row, deck rehearsed, backup video saved | r1-prototype |
| M5 Safety firewall | B | H8–11 | B | TT-06 | every check has pass+fail test; 0 invalid commands in replay | m5-firewall-ok |
| M6 TrafficTwin controller | B | H11–15 | B | TT-07 | spillback guard + fairness + forecast + decision cards; avoids unsafe release in blocked_downstream | m6-controller-ok |
| M7 Ambulance + recovery | B | H15–18 | B+A | TT-08 | staged green, downstream-clear-first, recovery logged, ambulance metric reported | m7-ambulance-ok |
| M8 Backend API + audit | B | H9–16 (parallel) | C | TT-09 | /health, /ws/live, scenario start, fault inject, approve (role check ⇒ 403 when unauthorised), audit written | m8-api-ok |
| M9 Dashboard | B | H9–18 (parallel) | D | TT-10 | Live Control Room, Decision Log, Comparison on live stream. **CHECKPOINT A (H18)** | m9-dashboard-ok |
| M10 Reliability | B | H18–21 | C+B | TT-11 | GPS outage ⇒ Local Safe ≤ GPS_STALE_S+1 s; Shadow Recovery resumes only after stable window; failure table passes | m10-failsafe-ok |
| M11 Twin A/B/C lite | B | H21–22 | B | TT-12 | Plan A/B/C scored and shown; selected plan passes firewall | m11-twin-ok |
| **H22 FEATURE FREEZE** | | | | | no new features | |
| M12 Evidence + quality | B | H18–24 (runs in background from H18) | A+E | TT-13 | multi-seed CSV, figures from CSV only, `ruff`+`pytest`+`bandit`+`pip-audit` results saved, no secrets in git | m12-evidence-ok |
| M13 Demo pack + release | B | H22–24 | E | TT-14 | README run steps work on a second laptop, 3-min demo clean 3×, backup video + screenshots | v1.0 |
| P2 Public advisory page | — | only with spare time | D | TT-15 | read-only /public, generic status only | m14-public-ok |

Cut rule (decide at checkpoints, no debate): behind ⇒ drop from the end: P2 → M11 → trust score/bus priority → What-If. **Never drop** M5 firewall, M6 guard, M7 ambulance + recovery, M10 Local Safe, real-metric comparison.

## Checklists (compact)
**M0** scaffold.sh · venv + `pip install eclipse-sumo traci sumolib pandas matplotlib pytest ruff bandit pip-audit` · `.gitignore` `.env.example` · `make test` · GitHub repo + Project (Backlog → Ready → In Progress → Review/Test → Done → Blocked) · issues TT-01…TT-15. Commit `chore: initialize TrafficTwin project and documentation`.
**M1** net J1–J4 (finite links ~200 m, main road + side roads) · safe 2-phase plans with yellow/all-red · vtypes car/taxi/bus/ambulance · `gen_routes.py --seed` · scenarios normal/rush/blocked_downstream/ambulance · bus schedule · enable tripinfo/fcd/queue/summary · `fallback_plan.json`. Commit `feat(sumo): add four-junction corridor and scenarios`.
**M2** `sim_runner.py` · estimator (queue, wait, speed, free space) · fixed + queue-reactive (min/max green, yellow, all-red) · metrics CSV · `run_all.py` · chart. Commit `feat(sim): add baseline controllers and metrics`.
**M3** GPS-like event builder · schemas frozen in `shared/schemas` · recorder + replay reader. Commit `feat(stream): add simulated GPS events and recorder`.
**M4** React corridor SVG from recorded events · 60–90 s recording · deck metrics from real baselines only. Commit `feat(web): add replay corridor dashboard`.
**M5** tests first (min green, max green, yellow, all-red, conflict, transition, downstream, fairness, emergency) · `firewall.py` single choke point · verdict log. Commit `feat(guards): add safety firewall with tests`.
**M6** spillback guard + test · fairness debt + override + test · rule-based forecast · controller pipeline · decision cards. Commit `feat(controller): add spillback-aware TrafficTwin controller`.
**M7** ambulance ETA · staged green · downstream-clear-first · bounded recovery. Commit `feat(emergency): add staged ambulance priority and recovery`.
**M8** FastAPI · `/ws/live` · REST (scenario, fault, approve, audit, metrics) · audit JSONL (SQLite optional) · operator token + role guard · pydantic validation. Commit `feat(api): add live stream, approval and audit endpoints`.
**M9** Live Control Room · Decision Log · Comparison (CSV) · mode/trust badges · approve button. Commit `feat(web): add operator control-room dashboard`.
**M10** fault injector · Local Safe · Safe Adaptive · Shadow Recovery (timer) · reliability panel. Commit `feat(reliability): add fail-safe modes and fault injection`.
**M11** plan generator + score · What-If view · (P1) bus priority, trust score. Commit `feat(twin): add plan A/B/C evaluation`.
**M12** multi-seed runs · figures from CSV · quality checks saved under `data/demo_assets/` · secrets check. Commit `docs: add results and quality evidence`.
**M13** README · demo script · screenshots · rehearsal · tag `v1.0`.

## Risks
| # | Risk | Mitigation |
|---|---|---|
| 1 | SUMO/TraCI setup slips | M0 verifies install first; generated net as fallback; commit a working scenario by H4 |
| 2 | 24 hours is tight | tracks in parallel, schemas frozen at M3, cut rule at H18, never drop firewall/guard/ambulance/Local Safe |
| 3 | TrafficTwin does not beat a baseline | choose spillback-prone demand, tune params, report honestly with trade-offs |
| 4 | Unsafe signal behavior | firewall single choke point, tests first, stored-plan fallback |
| 5 | Integration drift | dashboard built against recorded events; contracts in `shared/schemas` |
| 6 | Live demo failure | recorded video, screenshots, pre-run CSV, fixed seed, replay mode |
| 7 | Pre-built code dispute | ask organizers, tag `r1-prototype`, disclose in README |

## Blocked
- none

## Completed
- [x] Prototype PPT submitted
- [x] Product scope locked, docs written
- [x] M0 Repo + tooling (TT-01) — environment verified, gate passed
- [x] M1 SUMO corridor (TT-02) — 4-junction corridor J1-J4, safe 6-phase signals, 4 scenarios verified headless & GUI, fallback_plan.json created
- [x] M2 Baselines + metrics (TT-03) — fixed-time baseline runner, 3 parsers, 6 metrics (avg_wait, p95_wait, avg_travel, throughput, mean_queue, max_queue), CSV exports, baseline chart, 24 tests pass
- [x] M3 Safe queue-reactive controller (TT-04) — TraCI controller for J1-J4, bounded green extension, min/max green, yellow/all-red clearance, decision log, reactive metrics CSVs, comparison chart, 45 tests pass
- [x] M4 GPS-like stream + replay (TT-05) — Simulated GPS event extraction from SUMO, JSONL stream generator for 4 scenarios, replay utility with validation, 59 tests pass
