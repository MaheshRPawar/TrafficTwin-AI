# TrafficTwin AI — Design (UI/UX)
Dashboard-first, light and dark safe, readable on a projector.

## 1. Principles
Operator-first clarity · every action explained · state encoded by color AND label (accessibility) · never show a number that is not from the sim · "SIMULATED GPS" badge always visible.

## 2. Color states
| State | Use | Token idea |
|---|---|---|
| Green | free flow, safe, passed check | success |
| Amber | moderate congestion, Safe Adaptive, caution | warning |
| Red | high congestion/spillback risk, rejected, Local Safe fault | danger |
| Blue | Predictive AI mode, info | accent |
| Purple | Shadow Recovery | secondary |
| Gray | inactive/unknown/stale | neutral |
Vehicle markers: car gray, taxi yellow, bus blue, ambulance red with pulse.
Mode badge: Predictive (blue) · Safe Adaptive (amber) · Local Safe (red) · Shadow Recovery (purple).

## 3. Global layout
Top bar: logo, scenario selector, controller selector (Fixed / Reactive / TrafficTwin), run/pause, seed, SIMULATED GPS badge, mode badge, trust %.
Left nav: Live Control Room · Decision Log · Comparison · What-If Lab.
Right rail (always on): active alerts, fault injector (demo), last fallback event.

## 4. Views

### 4.1 Live Control Room (P0)
- Corridor SVG: J1→J4 horizontal, links colored by congestion, queue bars per approach, signal light per junction (G/Y/R with phase age), vehicle dots, bus and ambulance icons.
- Link tooltips: vehicles/capacity, free capacity %, avg speed, forecast risk, trust.
- Panels: Corridor Health strip (per link current vs 3-min forecast, free capacity bar, trust), spillback alert banner, max-wait/fairness chip per junction, latest decision card.
- Updates: link/junction 1 Hz, GPS markers 0.5 Hz, decisions on event.

### 4.2 Decision Log (P0)
Table/list of cards: time, junction, action, reasons, checks (✓/✗ chips), predicted effect, measured effect after 60 s (fills in later), filter by junction/type/mode. Rejected actions shown in red with failing check.

### 4.3 Controller Comparison (P0)
Scenario + seed selector; grouped bar charts (avg wait, p95 wait, max queue, throughput, spillbacks, ambulance delay, bus delay); metrics table; footer "Same seed, same demand file". Empty state shows `TBD from run` until CSV exists.

### 4.4 What-If Lab (P1)
Scenario picker (normal, surge, blocked downstream, ambulance, GPS outage) · button "Evaluate plans" · three plan cards (A/B/C) with PlanScore breakdown stacked bar · chosen plan highlighted · explanation text · firewall verdict.

### 4.5 Reliability panel (P1)
Mode state diagram with active node highlighted; GPS freshness, stream latency, model confidence, API health; last fallback event with reason; "stored fallback plan: available"; shadow-recovery countdown.

## 5. Decision card (shared component)
```
Action: Extend N–S green by 8 s            [J2 · Predictive]
Why:   • 28 waiting N–S  • bus ETA 45 s  • downstream 43% free  • E–W wait < threshold
Checks: ✓ min/max green  ✓ conflicts  ✓ downstream  ✓ fairness  ✓ transition
Expected: queue −6 (twin)   Spillback risk: reduced   Cross-road impact: bounded
Measured (60 s later): queue −5
```

## 6. Component tree
```
App
├─ TopBar (ScenarioSelect, ControllerSelect, RunControls, SimBadge, ModeBadge, TrustBadge)
├─ SideNav
├─ views/
│  ├─ LiveControl: CorridorSvg(LinkSegment, JunctionSignal, VehicleMarker, QueueBar), HealthStrip, AlertBanner, DecisionCardLatest
│  ├─ DecisionLog: FilterBar, DecisionCard[]
│  ├─ Comparison: SelectorBar, MetricChart[], MetricsTable
│  └─ WhatIfLab: PlanCard×3, ScoreBreakdown, Explanation
└─ RightRail: AlertList, FaultInjector, FallbackEvent
```

## 7a. R1 online demo (partial prototype)
Show: corridor in SUMO, fixed vs reactive causing downstream spillback, replay dashboard (signals, queues, link colors), optional guard decision card. Say clearly: "simulated GPS; ambulance, twin and fail-safe are built in the 48-hour round."

## 7. Final demo choreography (≤ 3 min)
0:00 Fixed — J2 queue grows, downstream blocks · 0:30 Reactive — reacts, bottleneck risk remains · 0:55 TrafficTwin — forecast, capacity gate, plan chosen · 1:25 Ambulance — staged greens, downstream cleared first · 1:55 Recovery — cross-road fairness restored · 2:15 Fault — Local Safe, traffic continues · 2:40 Restore — Shadow → Predictive.

## 8. Accessibility & polish
Text ≥ 12 px, color never the only signal, keyboard-focusable controls, light/dark support, empty and error states ("Feed lost. Local Safe plan active.").
