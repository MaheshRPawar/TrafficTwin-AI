# TrafficTwin AI — Project Rules
Applies to humans and AI assistants. Short on purpose.

## 1. Scope rules
1. Software only, 4 junctions, SUMO + TraCI. 6 junctions only after 4 are stable.
2. Forbidden unless it directly strengthens spillback-safe control, emergency recovery, Digital Twin testing or fail-safe reliability: blockchain, AR/VR, chatbot, mobile app, deep RL as core, full city simulation, hardware/IoT, proprietary data.
3. If scope creep is suggested, reply: "Keep the project scope locked. We need a reliable, software-only, four-intersection SUMO prototype with measurable results."
4. Every feature must map to an FR in SRS.md and the official problem statement.

## 2. Safety rules (non-negotiable)
1. Nothing writes to TraCI signals except through `firewall.apply()`.
2. Firewall checks: min green, max green, yellow, all-red, no conflicting greens, valid transitions, downstream capacity, fairness, emergency policy.
3. A firewall reject falls back to the stored plan step and is logged.
4. AI never issues raw durations; controllers propose from the valid-phase set only.
5. Local Safe must work with the backend ML/forecast/twin code fully disabled.

## 3. Honesty rules
1. No metric appears in code, docs, UI or slides unless produced by `experiments/results/*.csv`.
2. Use placeholders (`TBD from run`) until runs exist.
3. Label data as "simulated GPS". Never claim real-city control or proven real-world gains.
4. Report losses and trade-offs; do not cherry-pick seeds.
5. Predicted effect and measured effect are shown separately in decision cards.

## 4. Engineering rules
1. Lean: minimum files, no abstraction without two concrete uses, no design patterns for their own sake.
2. Python 3.11, type hints on public functions, `ruff` + `black`. TypeScript strict mode.
3. All tunables live in `backend/config/params.yaml`; no magic numbers in logic.
4. Determinism: seed passed explicitly; same route file for all controllers.
5. Functions that decide signals are pure where possible (state in → action out) so they are unit-testable.
6. Schemas change only via `shared/schemas`; bump `schema_version` and update frontend types.
7. Logs: structured JSON, one decision per line.

## 5. Testing rules
1. Firewall and guard unit tests written before controller code.
2. Each FR with P0 has at least one test or scripted scenario check.
3. CI-lite: `make test` must pass before merge to main.

## 6. Git and process rules
1. Branches: `feat/<module>-<short>`; small PRs; main always runs the demo.
2. Commit format: `type(scope): message` (feat, fix, test, docs, chore).
3. Feature freeze at H22 of the 24 build-hours; after that only experiments, quality checks, recording, rehearsal. Before R1, tag `r1-prototype`.
4. Third-party code: only with a compatible licence, recorded in THIRD_PARTY_NOTICES.md.
5. Update MEMORY.md at the end of every working session.

## 6a. Time and disclosure rules
1. Timeline is 24 build-hours: Block A for R1, Block B at the event. Plan in hours, not days. Follow the cut rules in TASKS.md.
2. Anything built before the event is disclosed in the README and tagged `r1-prototype`.
3. R1 materials show only real output; unbuilt features are labelled "planned".

## 6b. Module-by-module rules
1. One module per prompt/PR; follow the gate in TASKS.md; stop when the gate passes.
2. Push to GitHub and tag only after the gate passes. Never carry a broken module forward.
3. Reuse policy: MIT/Apache-2.0 → selective adaptation with attribution in THIRD_PARTY_NOTICES.md; GPL/AGPL → study only; no licence → read only, never copy; official docs → learn and implement yourself. Reference repos stay outside this repo.
4. Approved copyable sources: SUMO (as dependency), RoadwayVR/SUMO-Traffic-Simulator-Tutorial (MIT), LucasAlegre/sumo-rl (MIT). Skip `nets/RESCO` in sumo-atclib (GPL origin unchecked).
5. Computer vision (OpenCV/YOLO) is not part of the MVP; AGPL licensing of Ultralytics would also apply.

## 7. AI-assistant rules
1. Read MEMORY.md, SRS.md and TASKS.md before proposing changes.
2. Give implementation-ready output: file paths, code, tests, acceptance criteria.
3. Separate MUST / SHOULD / OPTIONAL; state assumptions.
4. Say plainly when an idea is too complex, unnecessary or not innovative.
5. Prefer robust heuristics and a working end-to-end system over unstable complexity.
