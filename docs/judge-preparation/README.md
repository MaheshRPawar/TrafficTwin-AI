# TrafficTwin AI — Judge Preparation & Viva Reference Suite

Welcome to the comprehensive Judge Preparation and Technical Viva Handbook for **TrafficTwin AI**. This folder provides complete, verified, and beginner-friendly documentation designed for student team presentation, live demonstrations, and rigorous faculty/judge questioning.

---

## 1. Documentation Index

| File | Document Title | Description & Target Audience |
| :--- | :--- | :--- |
| [`01-project-overview.md`](file:///docs/judge-preparation/01-project-overview.md) | **Project Overview & Elevator Pitches** | Problem statement, target stakeholders, 30s/60s/2min pitch scripts, and core innovations. |
| [`02-complete-folder-structure.md`](file:///docs/judge-preparation/02-complete-folder-structure.md) | **Annotated Codebase Structure** | End-to-end breakdown of directories, source files, configs, test fixtures, and data outputs. |
| [`03-architecture-and-data-flow.md`](file:///docs/judge-preparation/03-architecture-and-data-flow.md) | **Architecture & Data Flow** | System topology, Mermaid diagram, TraCI bridge, control order (M3→M7→M6→M9→M5), and REST/WS contracts. |
| [`04-tech-stack-and-libraries.md`](file:///docs/judge-preparation/04-tech-stack-and-libraries.md) | **Tech Stack & Verified Versions** | Exact versions, dependencies, rationale, and simple verbal viva answers for every tool used. |
| [`05-simulation-data-and-provenance.md`](file:///docs/judge-preparation/05-simulation-data-and-provenance.md) | **Simulation Data Provenance** | Honest origin analysis of SUMO networks, routes, synthetic GPS logs, and benchmark CSV outputs. |
| [`06-algorithms-and-decision-logic.md`](file:///docs/judge-preparation/06-algorithms-and-decision-logic.md) | **Algorithms & Decision Logic** | Math formulas, constants, thresholds, and logic for Queue-Reactive, Spillback M6, Firewall M5, and M9 Planner. |
| [`07-feature-by-feature-explanation.md`](file:///docs/judge-preparation/07-feature-by-feature-explanation.md) | **Feature-by-Feature Guide** | Breakdown of all 12 core capabilities with implementation source files, API routes, and viva explanations. |
| [`08-real-world-vs-our-innovation.md`](file:///docs/judge-preparation/08-real-world-vs-our-innovation.md) | **Real-World vs. Innovation** | Honest comparison: SUMO simulation capabilities vs. TrafficTwin's decision-support layer. |
| [`09-demo-and-troubleshooting.md`](file:///docs/judge-preparation/09-demo-and-troubleshooting.md) | **Live Demo Walkthrough & Run Guide** | Step-by-step instructions for running Normal, Rush, Spillback, and Ambulance demos with copy-paste commands. |
| [`10-judge-viva-questions.md`](file:///docs/judge-preparation/10-judge-viva-questions.md) | **50+ Judge & Faculty Viva Questions** | Categorized questions with short 1-3 sentence answers and detailed technical explanations. |
| [`11-presentation-script.md`](file:///docs/judge-preparation/11-presentation-script.md) | **Presentation Scripts & Demo Narration** | Word-for-word spoken scripts for slides, live SUMO demonstration, and closing statements. |
| [`12-results-and-limitations.md`](file:///docs/judge-preparation/12-results-and-limitations.md) | **Empirical Results & Limitations** | Reproducible benchmark comparisons across all 4 scenarios, trade-off analysis, and honest limitations. |
| [`13-feature-status-and-release-checklist.md`](file:///docs/judge-preparation/13-feature-status-and-release-checklist.md) | **Feature Status & Verification Checklist** | Complete verification status of all components, test pass rates, linting, security audits, and git release tag. |

---

## 2. Recommended Learning Order for Presenters

1. **First 10 Minutes**: Read [`01-project-overview.md`](file:///docs/judge-preparation/01-project-overview.md) and practice the 30-second and 60-second elevator pitches aloud.
2. **Next 15 Minutes**: Review [`03-architecture-and-data-flow.md`](file:///docs/judge-preparation/03-architecture-and-data-flow.md) so you can draw the 7-step control chain on a whiteboard:
   $$\text{Traffic State} \rightarrow \text{M3 Reactive} \rightarrow \text{M7 Fairness/Ambulance} \rightarrow \text{M6 Spillback} \rightarrow \text{M9 Plan Evaluator} \rightarrow \text{M5 Firewall} \rightarrow \text{SUMO/TraCI}$$
3. **Demo Practice**: Open [`09-demo-and-troubleshooting.md`](file:///docs/judge-preparation/09-demo-and-troubleshooting.md) and run `run.bat` and `launch_sumo_gui.bat` to see SUMO and the web dashboard in action.
4. **Viva Preparation**: Spend 30 minutes reading [`10-judge-viva-questions.md`](file:///docs/judge-preparation/10-judge-viva-questions.md). Pay special attention to:
   - *"Is this really AI?"* (No deep learning, deterministic digital twin evaluator)
   - *"What dataset did you use?"* (Authentic SUMO microscopic simulation, synthetic GPS-like probe logs)
   - *"How is spillback different from a normal queue?"* (Storage exhaustion on downstream link blocking upstream green)

---

## 3. Quick Run Commands

### One-Click Launch (Windows)
- Double-click [`run.bat`](file:///run.bat) to launch both FastAPI Backend (Port 8000) and React Frontend (Port 5173).
- Double-click [`launch_sumo_gui.bat`](file:///launch_sumo_gui.bat) to launch the SUMO simulation visualizer.
- Double-click [`stop.bat`](file:///stop.bat) to stop all background processes.

### Manual Terminal Commands
```powershell
# Terminal 1: Backend
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173

# Terminal 3: SUMO GUI (Live Corridor)
sumo-gui -c sumo/scenarios/corridor_normal.sumocfg --start
```
