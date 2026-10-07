# TrafficTwin AI — GSD (Get Stuff Done)

## Goal
A reliable, software-only, four-junction SUMO prototype: GPS-like stream → forecast → safe plan → firewall → signals, with measurable results and fail-safe modes. Built one module at a time.

## The loop (every module)
1. Pick the next module in TASKS.md. Read its gate.
2. Write the gate as a test or a run command **first**.
3. Build only that module. Touch only its files.
4. Run it from a documented command. Capture proof (output file, screenshot, test result).
5. `make test` green ⇒ commit small, descriptive message.
6. Merge to `main`, tag `mN-<name>-ok`, push.
7. Tick the box in TASKS.md, add a line to MEMORY.md. Only now start the next module.

If the gate fails after the time box: cut scope inside the module, never carry a broken module forward.

## Definition of done (module)
- Runs from one documented command
- Input/output defined; failure behaviour known
- Tests pass; no invented numbers
- README/module note updated; no secrets committed
- Any teammate can explain it

## Priorities
P0 = needed for the end-to-end demo · P1 = after P0 is stable · P2 = only with spare time.
P0: M0–M10. P1: M11. P2: public page, ML forecast, rain/closure.

## Git workflow
- `main` is always runnable. Work on `feature/<module>` branches; merge only when the gate passes.
- Tags: `m0-ready` … `m13`, `r1-prototype`, `v1.0`.
- Commits: `feat|fix|test|docs|chore(scope): message` (e.g. `feat(guards): add safety firewall with tests`).
- GitHub Project columns: Backlog → Ready → In Progress → Review/Test → Done → Blocked. One issue per module (TT-01…TT-15).
- Anything built before the on-site event is tagged `r1-prototype` and disclosed in the README.

## Timeboxes and cut rules
- Module overruns by 50% ⇒ stop, cut scope, ship the smaller version.
- Total budget is 24 build-hours. Checkpoint A at H18 without an end-to-end path ⇒ drop M11, public page, bus priority, trust score.
- H22 = feature freeze; after that only experiments, quality checks, recording, rehearsal.
- Blocked more than 20 minutes ⇒ use the fallback below or simplify the module.

## Failure fallbacks
| Failure | Fallback |
|---|---|
| Dashboard fails | SUMO GUI + terminal + metrics CSV |
| API fails | run controller directly, inspect JSON/CSV |
| Database fails | JSONL/CSV local outputs (primary store anyway) |
| Planner fails | Safe Adaptive controller |
| Controller fails | Local Safe fixed-time plan |
| SUMO GUI fails | headless SUMO + metrics + recorded demo |
| Internet fails | whole core runs locally |
- Never cut: firewall, spillback guard, ambulance staging, Local Safe, comparison from real runs.

## Prompting rule for Antigravity (one module per prompt)
Use this template. Never ask for the whole project in one prompt.
```
Module: M<N> <name> (issue TT-<NN>)
Read first: docs/RULES.md, docs/TASKS.md (this module), docs/SRS.md (FR ids), docs/DESIGN.md
Goal: <one sentence>
Files you may create/change: <list>   Do NOT touch anything else.
Gate (must pass): <acceptance criteria from TASKS.md>
Output: files, code, run command, tests, pass/fail against gate.
Stop after the gate passes. Do not start the next module. Update TASKS.md and MEMORY.md.
```

## Honesty rules
No metric appears unless it came from `experiments/results/*.csv`. Label data "simulated GPS". Report trade-offs. State that results are simulation-based.

## Non-goals
Real signal control, municipal CCTV, YOLO/OpenCV as core (future adapter only), custom model training, deep RL, mobile app, blockchain, whole-city model, public control access.
