# TrafficTwin AI
Predict. Simulate. Protect. Recover.

A local, authority-facing **traffic corridor decision-support prototype**. A SUMO four-junction Digital Twin consumes simulated GPS-like vehicle events, forecasts congestion, tests safe signal plans, blocks downstream spillback, stages ambulance priority with fair recovery, and falls back to safe control when data or AI fails.

**Scope boundary:** simulation and decision support only. It does not control live municipal traffic lights. Camera/YOLO, real GPS/GTFS feeds and ML models are future adapters. Data is simulated GPS. Results below are produced by our SUMO runs only.

## Quick start (fill commands as modules land)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
make sim            # run a scenario (see Makefile)
make api            # FastAPI backend
make web            # dashboard
make test           # tests
make experiments    # fixed vs reactive vs TrafficTwin, same seeds
```

## Results
TBD from run (see `experiments/results/`).

## Docs
PRD · SRS · ARCHITECTURE · DESIGN · UI_DESIGN · TASKS · GSD · ROLES · RULES · SECURITY · TESTING · TECH_STACK · MEMORY (all in `docs/`).

## Disclosure
Code built before the event is tagged `r1-prototype`.

## Third-party
See THIRD_PARTY_NOTICES.md.
