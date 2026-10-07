# TrafficTwin AI — Security Plan

## Goal
Prevent unauthorized access, unsafe signal actions, secret leakage and loss of audit history.

## Trust boundary
Dashboard → API → authorization → safety firewall → SUMO adapter. The dashboard never reaches TraCI.

## Controls (MVP)
- Local operator token + role checks (Viewer / Operator); hashed passwords and signed token only if JWT is built (P1)
- Input validation on every endpoint (pydantic); invalid ⇒ 422
- Approval endpoint: authenticated Operator/Admin only, recommendation must exist, action must pass the firewall, logged before and after application
- Append-only audit JSONL for recommendations, approvals, rejections, actions, mode changes, faults
- No secrets in git: `.env` ignored, `.env.example` has names only
- Fixed-time fallback plan and safe rejection of invalid phase actions
- No LLM or AI tool has direct signal-control access

## Checks to run and save (under `data/demo_assets/quality/`)
```
ruff check .
pytest
bandit -r backend sumo experiments
pip-audit
npm audit            # frontend
git grep -nEi "(api[_-]?key|secret|password|token)\s*=" -- . ':!docs'   # quick secret scan
```

## Out of scope / limits
The MVP does not connect to live municipal controllers. A real deployment would need authority approval, certified controllers, network segmentation, stronger identity, encrypted telemetry, key rotation, privacy review and safety certification.
