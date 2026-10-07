# TrafficTwin AI — Tech Stack
Pin exact versions in lockfiles at install time (requirements.txt, package-lock.json). Versions are not asserted here.

## LOCKED (verified Oct 2026: SUMO 1.27.0 released 21 May 2026, EPL-2.0; `pip install eclipse-sumo traci`)
Pin SUMO 1.27.x for all team machines. Everything below is final unless a blocker appears.

## Core (MUST)
| Layer | Choice | Why |
|---|---|---|
| Simulator | Eclipse SUMO (native install) | open-source microscopic multimodal sim |
| Sim control | TraCI via Python (`traci`; `libsumo` only if speed needed) | read state, set phases live |
| Backend | Python 3.11, FastAPI, Uvicorn | async REST + WebSocket, fast to build |
| Data | NumPy, Pandas | metrics, summaries |
| Config | PyYAML (`params.yaml`) | all tunables in one place |
| Validation | Pydantic (FastAPI built-in) | schema-checked events and requests |
| Storage | JSONL/CSV primary, SQLite optional | zero ops; JSONL is the audit fallback |
| Auth | local operator token (JWT only if time) | role guard on approval endpoint |
| Quality | pytest, ruff, bandit, pip-audit | results saved to `data/demo_assets/` |
| Frontend | React + TypeScript (Vite), Tailwind CSS | fast dev, typed events |
| Charts | Recharts | simple comparison and time-series charts |
| Corridor view | Custom SVG in React | schematic 4-junction layout |
| Tests | pytest (backend), Vitest (frontend, light) | firewall and guard tests first |
| Quality | ruff, black, ESLint, Prettier | lean linting |
| Task runner | Makefile | `make sim|api|web|test|experiments` |

## Optional (only if time remains)
scikit-learn or XGBoost for forecast · Docker Compose · Vercel/Render deploy · ECharts · Leaflet.

## Explicitly excluded
Blockchain, AR/VR, chatbot, mobile app, deep RL/MARL as dependency, PostgreSQL, Redis, Kafka, hardware/IoT, proprietary mobility data, city-scale simulation.

## Reference projects (study, don't blindly copy; log in THIRD_PARTY_NOTICES.md)
SUMO, SUMO TraCI tutorials, SUMO-RL, sumolights, PressLight, CityFlow, LibSignal, Sim2Signal, emergency-preemption repos listed in Prompt.md. Reuse code only where the licence permits.

## Dev environment
Python venv, Node LTS, SUMO on PATH with `SUMO_HOME` set. Windows/Linux/macOS supported (NFR-6).
