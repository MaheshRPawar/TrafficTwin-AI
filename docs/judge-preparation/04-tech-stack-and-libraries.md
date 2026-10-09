# Document 04 — Tech Stack & Verified Libraries

## 1. Verified Technology Stack Table

All technologies listed below are directly verified from project configuration files ([`package.json`](file:///frontend/package.json), [`pyproject.toml`](file:///pyproject.toml), [`params.yaml`](file:///backend/config/params.yaml)) and environment diagnostics ([`verify_environment.py`](file:///scripts/verify_environment.py)).

| Technology / Library | Verified Version | Where It Is Used | Engineering Rationale | Short Viva Answer |
| :--- | :--- | :--- | :--- | :--- |
| **Eclipse SUMO** | 1.27.1 | `sumo/`, `experiments/` | Open-source microscopic road traffic simulator modeling car-following and lane-changing physics. | *"SUMO provides the physical ground truth for vehicle physics and signal heads."* |
| **TraCI (Python SDK)**| 1.27.1 | `experiments/`, `backend/` | TCP socket bridge allowing Python scripts to subscribe to simulation state and actuate signals. | *"TraCI is the standard protocol for real-time programmatic control of SUMO."* |
| **Python** | 3.14.7 / $\ge 3.11$ | Backend & Experiments | High-productivity language for traffic control logic, data analysis, and mathematical modeling. | *"Python powers our backend control logic, safety guards, and test suite."* |
| **FastAPI** | 0.142.3 | `backend/app/main.py` | High-performance asynchronous REST API framework with native OpenAPI/Swagger documentation. | *"FastAPI serves simulation telemetry and decision endpoints with low latency."* |
| **Uvicorn** | 0.54.0 | Backend runtime | Lightning-fast ASGI server for running FastAPI and managing WebSocket connections. | *"Uvicorn is the ASGI web server hosting our FastAPI application locally."* |
| **Pydantic** | 2.13.5 | `backend/app/planner/` | Strongly-typed data validation for corridor snapshots, plans, and API payloads. | *"Pydantic guarantees strict type validation for our digital twin state models."* |
| **PyYAML** | 6.0.3 | `backend/config/` | Parser for system configuration parameters (`params.yaml`). | *"PyYAML loads our authoritative safety constants and scoring weights."* |
| **React** | 19.2.8 | `frontend/src/` | Modern reactive user interface library for building dynamic dashboard components. | *"React powers our real-time operator control room and public simulation dashboard."* |
| **Vite** | 8.3.3 | `frontend/` | Next-generation frontend build tool and local development server with instant HMR. | *"Vite bundles and serves our frontend application with sub-second reload times."* |
| **Recharts** | 3.10.1 | `frontend/src/components/` | Declarative SVG charting library for rendering delay, queue, and throughput metrics. | *"Recharts renders our comparative performance curves and metric charts."* |
| **@xyflow/react** | 12.12.0 | `frontend/src/components/` | Node-based workflow diagram library visualizing the 7-step decision flow. | *"XYFlow visualizes our 7-step control pipeline execution graph."* |
| **Lucide React** | 1.53.0 | `frontend/src/components/` | Clean, purposeful industrial iconography without emojis or decorative clutter. | *"Lucide React provides clean transportation engineering icons."* |
| **Pytest** | 9.1.1 | `tests/` | Automated testing framework executing all 142 unit and integration tests. | *"Pytest validates all 142 tests across modules M1 through M11."* |
| **Ruff** | Installed | Repository-wide | Extremely fast Python linter ensuring PEP 8 code quality and formatting. | *"Ruff enforces clean, error-free Python code across all modules."* |
| **Bandit** | 1.9.4 | Security audit | AST-based static security analyzer finding common vulnerabilities in Python code. | *"Bandit scans our codebase for security flaws and unsafe function calls."* |
| **pip-audit** | 2.10.1 | Dependency audit | Automated vulnerability scanner checking dependencies against PyPA Advisory Database. | *"pip-audit ensures our Python environment has zero known CVE vulnerabilities."* |

---

## 2. What Is NOT in the Tech Stack (Crucial Viva Defenses!)

To prevent judges from assuming unnecessary complexity, explicitly declare what is **omitted by design**:

- **No Docker**: The application is built to run natively and locally on Windows/Linux with zero containerization overhead.
- **No Cloud / AWS / GCP**: TrafficTwin is strictly **local-first**; traffic control rooms require air-gapped reliability without internet dependencies.
- **No Heavy Relational Database (No PostgreSQL / MySQL)**: Data persistence uses immutable, high-speed CSV benchmarks and JSONL streams.
- **No Neural Networks / Deep Learning (No PyTorch / TensorFlow)**: Decisions are deterministic, mathematically verified, and 100% explainable.
- **No External Fleet APIs or Hardware Actuation**: The system operates as a decision-support prototype on simulated traffic; it does not connect to live municipal signals.
