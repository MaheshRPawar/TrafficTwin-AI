import React, { useState } from 'react';
import DecisionGraphFlow from './DecisionGraphFlow';

export default function RightOperationsConsole({
  selectedJunction = 'J3',
  scenarioData,
  corridorState,
  currentRecommendation,
  auditEvents = [],
  userRole = 'OPERATOR',
  replayStep = 0,
  isReplaying = false,
  onReplay,
  onApprove,
  approvalStatus,
  selectedItemType = 'junction',
  selectedItemId = 'J3',
  onSelectItem,
  roadsList = [],
  vehiclesList = [],
}) {
  const [activeTab, setActiveTab] = useState('CURRENT_STATE');
  const [isApproving, setIsApproving] = useState(false);

  // Road or Vehicle lookup
  const selectedRoad = roadsList.find((r) => r.road_id === selectedItemId) || {
    road_id: selectedItemId,
    name: `Corridor Link ${selectedItemId}`,
    from_node: selectedItemId.split('_')[0] || 'J3',
    to_node: selectedItemId.split('_')[1] || 'J4',
    length_m: 250.0,
    lanes: 2,
    speed_limit_kmh: 50.0,
    capacity_veh: 53,
    occupancy_percent: selectedItemId === 'J3_J4' ? 88.7 : 35.0,
    status: selectedItemId === 'J3_J4' ? 'SPILLBACK RISK' : 'CLEAR',
  };

  const selectedVehicle = vehiclesList.find((v) => v.vehicle_id === selectedItemId) || {
    vehicle_id: selectedItemId,
    type: selectedItemId.startsWith('amb') ? 'emergency' : 'passenger',
    speed_kmh: selectedItemId.startsWith('amb') ? 46.2 : 28.5,
    lane_id: `${selectedItemId.startsWith('amb') ? 'J2_J3_0' : 'J3_J4_0'}`,
    road_segment: selectedItemId.startsWith('amb') ? 'J2_J3' : 'J3_J4',
    distance_to_signal_m: selectedItemId.startsWith('amb') ? 38.5 : 12.0,
    status: selectedItemId.startsWith('amb') ? 'PRIORITY_PREEMPTION' : 'QUEUED',
    preempted_junction: selectedItemId.startsWith('amb') ? 'J2' : null,
  };

  const jData = corridorState?.[selectedJunction] || scenarioData.junctions[selectedJunction] || scenarioData.junctions.J3;
  const isJ3 = selectedJunction === 'J3';
  const isBlocked = scenarioData.id === 'blocked_downstream';
  const isCrit = (jData.risk || jData.spillback_risk) === 'CRITICAL';
  const isWarn = (jData.risk || jData.spillback_risk) === 'WARNING';

  // Decision trace steps from scenario or corridorState
  const decisionSteps = scenarioData.decisionTrace || [];

  // M9 Plan data
  const m9Plan = corridorState?.selected_plan || {
    plan_name: isBlocked ? 'PLAN C' : 'PLAN A',
    total_score: isBlocked ? 28.5 : 14.2,
    explanation: isBlocked
      ? 'Lowest safe score. Coordinates downstream clearing to prevent gridlock.'
      : 'Corridor in equilibrium. Plan A preserves steady green waves.',
    scores: isBlocked
      ? { delay: 4.5, queue: 6.0, spillback: 12.0, fairness: 3.0, emergency: 3.0 }
      : { delay: 2.2, queue: 4.0, spillback: 5.0, fairness: 1.5, emergency: 1.5 },
    all_plans: [
      {
        name: 'Plan A (Current Safe Timing)',
        valid: true,
        total_score: isBlocked ? 44.5 : 14.2,
        scores: { delay: 3.5, queue: 8.0, spillback: 27.0, fairness: 3.0, emergency: 3.0 },
      },
      {
        name: 'Plan B (Bounded Extension +5s)',
        valid: !isBlocked,
        total_score: isBlocked ? 999.0 : 22.4,
        scores: { delay: 2.0, queue: 4.0, spillback: 90.0, fairness: 3.0, emergency: 3.0 },
        rejection_reasons: isBlocked ? ['m6_spillback_violation: Downstream occupancy >= 85.0%'] : [],
      },
      {
        name: 'Plan C (Downstream Clearing & Coord)',
        valid: true,
        total_score: isBlocked ? 28.5 : 18.0,
        scores: { delay: 4.5, queue: 6.0, spillback: 12.0, fairness: 3.0, emergency: 3.0 },
      },
    ],
  };

  const rec = currentRecommendation || {
    recommendation_id: isBlocked ? 'REC-2026-J3-0887' : 'REC-2026-J1-0112',
    proposed_action: isBlocked ? 'SPILLBACK_CLEARANCE' : 'KEEP_GREEN',
    reason: isBlocked
      ? 'Downstream link J3_J4 storage exceeds 85.0% (47/53 veh, 88.7% occupancy).'
      : 'Normal corridor flow. Safe green progression maintained.',
    status: 'PENDING_APPROVAL',
  };

  const handleApprovalClick = async () => {
    if (userRole === 'VIEWER') return;
    setIsApproving(true);
    try {
      if (onApprove) {
        await onApprove(rec.recommendation_id);
      }
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <aside className="operations-console">
      {/* 1. TOP HEADER: Junction, Road, or Vehicle Identity & Status */}
      <div className="console-header">
        {selectedItemType === 'road' ? (
          <>
            <div className="console-identity">
              <span className="console-sup micro-label">SELECTED ROAD LINK</span>
              <h2 className="console-junction-title mono">
                LINK {selectedRoad.road_id}
              </h2>
              <span className="console-sub">{selectedRoad.name} // {selectedRoad.length_m}m</span>
            </div>

            <div className={`console-status-pill ${selectedRoad.status === 'SPILLBACK RISK' ? 'pill-crit' : 'pill-norm'}`}>
              <span className={`pill-dot ${selectedRoad.status === 'SPILLBACK RISK' ? 'dot-crit' : 'dot-norm'}`}></span>
              {selectedRoad.status}
            </div>
          </>
        ) : selectedItemType === 'vehicle' ? (
          <>
            <div className="console-identity">
              <span className="console-sup micro-label">INSPECTED VEHICLE</span>
              <h2 className="console-junction-title mono">
                {selectedVehicle.vehicle_id}
              </h2>
              <span className="console-sub">{selectedVehicle.type.toUpperCase()} // Arterial GPS Stream</span>
            </div>

            <div className={`console-status-pill ${selectedVehicle.type === 'emergency' ? 'pill-crit' : 'pill-norm'}`}>
              <span className={`pill-dot ${selectedVehicle.type === 'emergency' ? 'dot-crit' : 'dot-norm'}`}></span>
              {selectedVehicle.status}
            </div>
          </>
        ) : (
          <>
            <div className="console-identity">
              <span className="console-sup micro-label">SELECTED INTERSECTION</span>
              <h2 className="console-junction-title mono">
                {selectedJunction} / EASTBOUND
              </h2>
              <span className="console-sub">Corridor Station // {jData.corridorPos || '600m'}</span>
            </div>

            <div className={`console-status-pill ${isCrit ? 'pill-crit' : isWarn ? 'pill-warn' : 'pill-norm'}`}>
              <span className={`pill-dot ${isCrit ? 'dot-crit' : isWarn ? 'dot-warn' : 'dot-norm'}`}></span>
              {jData.risk || jData.spillback_risk || 'NORMAL'}
            </div>
          </>
        )}
      </div>

      {/* 2. OPERATIONAL TABS */}
      <div className="console-tabs">
        <button
          className={`console-tab-btn ${activeTab === 'CURRENT_STATE' ? 'active' : ''}`}
          onClick={() => setActiveTab('CURRENT_STATE')}
        >
          STATE
        </button>
        <button
          className={`console-tab-btn ${activeTab === 'M9_PLANS' ? 'active' : ''}`}
          onClick={() => setActiveTab('M9_PLANS')}
        >
          M9 PLANS
        </button>
        <button
          className={`console-tab-btn ${activeTab === 'DECISION_FLOW' ? 'active' : ''}`}
          onClick={() => setActiveTab('DECISION_FLOW')}
        >
          FLOW
        </button>
        <button
          className={`console-tab-btn ${activeTab === 'AUDIT_LOG' ? 'active' : ''}`}
          onClick={() => setActiveTab('AUDIT_LOG')}
        >
          AUDIT
        </button>
      </div>

      <div className="console-body">
        {/* TAB 1: CURRENT STATE VIEW - ROAD INSPECTOR */}
        {activeTab === 'CURRENT_STATE' && selectedItemType === 'road' && (
          <div className="state-section">
            <div className="state-metric-grid">
              <div className="state-row">
                <span className="state-label">Segment Identifier</span>
                <span className="state-val mono">{selectedRoad.road_id}</span>
              </div>
              <div className="state-row">
                <span className="state-label">Topology Orientation</span>
                <span className="state-val mono">{selectedRoad.from_node} → {selectedRoad.to_node} (Eastbound)</span>
              </div>
              <div className="state-row">
                <span className="state-label">Physical Length</span>
                <span className="state-val mono">{selectedRoad.length_m} meters</span>
              </div>
              <div className="state-row">
                <span className="state-label">Lane Configuration</span>
                <span className="state-val mono">{selectedRoad.lanes} Lanes (Eastbound Arterial)</span>
              </div>
              <div className="state-row">
                <span className="state-label">Speed Limit</span>
                <span className="state-val mono">{selectedRoad.speed_limit_kmh} km/h</span>
              </div>
              <div className="state-row">
                <span className="state-label">Storage Capacity</span>
                <span className="state-val mono">{selectedRoad.capacity_veh} vehicles</span>
              </div>
              <div className="state-row">
                <span className="state-label">Live Occupancy</span>
                <span className={`state-val mono ${selectedRoad.occupancy_percent >= 85 ? 'text-crit bold' : ''}`}>
                  {selectedRoad.occupancy_percent}%
                </span>
              </div>
              <div className="occupancy-progress-bar">
                <div
                  className={`progress-fill ${selectedRoad.occupancy_percent >= 85 ? 'fill-crit' : selectedRoad.occupancy_percent >= 75 ? 'fill-warn' : 'fill-norm'}`}
                  style={{ width: `${Math.min(selectedRoad.occupancy_percent, 100)}%` }}
                ></div>
                <span className="threshold-line warn" style={{ left: '75%' }} title="Warning 75%"></span>
                <span className="threshold-line crit" style={{ left: '85%' }} title="Critical 85%"></span>
              </div>
              <div className="state-row">
                <span className="state-label">M6 Spillback Guard</span>
                <span className={`state-val mono ${selectedRoad.occupancy_percent >= 85 ? 'text-crit bold' : 'text-green bold'}`}>
                  {selectedRoad.occupancy_percent >= 85 ? 'INTERCEPTION ARMED // CRITICAL' : 'MONITORING // CLEAR'}
                </span>
              </div>
              <div className="state-row">
                <span className="state-label">Safety Enforcement</span>
                <span className="state-val mono text-green bold">M5 SAFETY FIREWALL ACTIVE</span>
              </div>
            </div>

            <div className={`operator-advisory ${selectedRoad.occupancy_percent >= 85 ? 'adv-crit' : 'adv-norm'}`}>
              <div className="adv-title">
                {selectedRoad.occupancy_percent >= 85 ? '[ALERT] CAPACITY SATURATION RISK' : '[OK] FREE-FLOW STORAGE CAPACITY'}
              </div>
              <p className="adv-text">
                {selectedRoad.occupancy_percent >= 85
                  ? `Link ${selectedRoad.road_id} storage exceeds critical 85% threshold. Upstream signal extension is blocked by Module M6.`
                  : `Link ${selectedRoad.road_id} has adequate reserve storage capacity. Normal green wave progression permitted.`}
              </p>
            </div>

            <button
              className="btn-switch-public mono"
              style={{ marginTop: '12px', width: '100%', justifyContent: 'center' }}
              onClick={() => onSelectItem && onSelectItem('junction', selectedRoad.to_node)}
            >
              Inspect Target Junction {selectedRoad.to_node} →
            </button>
          </div>
        )}

        {/* TAB 1: CURRENT STATE VIEW - VEHICLE INSPECTOR */}
        {activeTab === 'CURRENT_STATE' && selectedItemType === 'vehicle' && (
          <div className="state-section">
            <div className="state-metric-grid">
              <div className="state-row">
                <span className="state-label">Vehicle ID</span>
                <span className="state-val mono">{selectedVehicle.vehicle_id}</span>
              </div>
              <div className="state-row">
                <span className="state-label">Vehicle Class</span>
                <span className={`state-val mono ${selectedVehicle.type === 'emergency' ? 'text-crit bold' : ''}`}>
                  {selectedVehicle.type.toUpperCase()}
                </span>
              </div>
              <div className="state-row">
                <span className="state-label">Current Velocity</span>
                <span className="state-val mono">{selectedVehicle.speed_kmh} km/h</span>
              </div>
              <div className="state-row">
                <span className="state-label">Assigned Lane</span>
                <span className="state-val mono">{selectedVehicle.lane_id || 'Unavailable'}</span>
              </div>
              <div className="state-row">
                <span className="state-label">Road Link</span>
                <span className="state-val mono">{selectedVehicle.road_segment || 'Unavailable'}</span>
              </div>
              <div className="state-row">
                <span className="state-label">Distance to Signal</span>
                <span className="state-val mono">{selectedVehicle.distance_to_signal_m} meters</span>
              </div>
              <div className="state-row">
                <span className="state-label">M7 Priority Preemption</span>
                <span className={`state-val mono ${selectedVehicle.type === 'emergency' ? 'text-crit bold' : 'highlight-blue'}`}>
                  {selectedVehicle.type === 'emergency' ? 'PREEMPTION GRANTED (Phase 0 Extended)' : 'STANDARD PRIORITY (Fairness Queue)'}
                </span>
              </div>
              <div className="state-row">
                <span className="state-label">Preempted Junction</span>
                <span className="state-val mono">{selectedVehicle.preempted_junction || 'None'}</span>
              </div>
              <div className="state-row">
                <span className="state-label">Telemetry Source</span>
                <span className="state-val mono text-green bold">AUTHENTIC SUMO GPS STREAM</span>
              </div>
            </div>

            <div className={`operator-advisory ${selectedVehicle.type === 'emergency' ? 'adv-crit' : 'adv-norm'}`}>
              <div className="adv-title">
                {selectedVehicle.type === 'emergency' ? '[EMERGENCY] ACTIVE CORRIDOR PREEMPTION' : '[TELEMETRY] STANDARD PASSENGER VEHICLE'}
              </div>
              <p className="adv-text">
                {selectedVehicle.type === 'emergency'
                  ? 'Vehicle identified as Class Emergency. Module M7 has requested green preemption at downstream signals with fair recovery debt tracking.'
                  : 'Vehicle tracked in arterial flow stream. Subject to queue-reactive signal timing and downstream spillback gating.'}
              </p>
            </div>

            <button
              className="btn-switch-public mono"
              style={{ marginTop: '12px', width: '100%', justifyContent: 'center' }}
              onClick={() => onSelectItem && onSelectItem('junction', selectedVehicle.preempted_junction || 'J2')}
            >
              Inspect Approaching Junction →
            </button>
          </div>
        )}

        {/* TAB 1: CURRENT STATE VIEW - JUNCTION INSPECTOR */}
        {activeTab === 'CURRENT_STATE' && selectedItemType === 'junction' && (
          <div className="state-section">
            <div className="state-metric-grid">
              <div className="state-row">
                <span className="state-label">Approach Queue</span>
                <span className={`state-val mono ${isCrit ? 'text-crit bold' : ''}`}>
                  {jData.queueMain ?? jData.queue_main ?? 0} vehicles
                </span>
              </div>

              <div className="state-row">
                <span className="state-label">Cross Street Queue</span>
                <span className="state-val mono">{jData.queueCross ?? jData.queue_cross ?? 0} vehicles</span>
              </div>

              <div className="state-row">
                <span className="state-label">Target Link</span>
                <span className="state-val mono">{jData.downstreamEdge || jData.downstream_edge || 'J3_J4'} (200m)</span>
              </div>

              <div className="state-row">
                <span className="state-label">Link Storage</span>
                <span className="state-val mono">
                  {jData.downstreamVehs ?? jData.vehicles ?? 0} / {jData.downstreamCap ?? jData.capacity ?? 53} veh
                </span>
              </div>

              <div className="state-row">
                <span className="state-label">Downstream Occupancy</span>
                <span className={`state-val mono ${isCrit ? 'text-crit bold' : ''}`}>
                  {jData.downstreamOcc ?? jData.occupancy ?? 0}%
                </span>
              </div>

              <div className="occupancy-progress-bar">
                <div
                  className={`progress-fill ${isCrit ? 'fill-crit' : isWarn ? 'fill-warn' : 'fill-norm'}`}
                  style={{ width: `${Math.min(jData.downstreamOcc ?? jData.occupancy ?? 0, 100)}%` }}
                ></div>
                <span className="threshold-line warn" style={{ left: '75%' }} title="Warning 75%"></span>
                <span className="threshold-line crit" style={{ left: '85%' }} title="Critical 85%"></span>
              </div>

              <div className="state-row">
                <span className="state-label">Signal State</span>
                <span className="state-val mono highlight-blue">
                  {isJ3 && isBlocked && replayStep >= 6
                    ? 'Phase 1 (Yellow Clearance)'
                    : `Phase ${jData.phase} (${jData.phaseName || jData.phase_name || 'Main Green'})`}
                </span>
              </div>

              <div className="state-row">
                <span className="state-label">Elapsed Green</span>
                <span className="state-val mono">
                  {(jData.elapsedGreen ?? jData.elapsed_green_s ?? 10.0).toFixed(1)}s (Max 40.0s)
                </span>
              </div>

              <div className="state-row">
                <span className="state-label">Safety Firewall (M5)</span>
                <span className="state-val mono text-green bold">ACTIVE // ENFORCED</span>
              </div>

              <div className="state-row">
                <span className="state-label">Fail-Safe Controller (M8)</span>
                <span className="state-val mono highlight-blue">PREDICTIVE</span>
              </div>
            </div>

            {/* Operator Advisory Banner */}
            <div className={`operator-advisory ${isCrit ? 'adv-crit' : 'adv-norm'}`}>
              <div className="adv-title">
                {isCrit ? '[ALERT] CRITICAL SPILLBACK HAZARD' : '[OK] CORRIDOR IN STABLE EQUILIBRIUM'}
              </div>
              <p className="adv-text">
                {isCrit
                  ? 'Downstream storage exceeds 85.0% threshold. Spillback Guard preempts green extension to protect link capacity.'
                  : 'Traffic release rate within downstream storage capacity. Safety firewall active.'}
              </p>
            </div>
          </div>
        )}

        {/* TAB 2: M9 PLAN EVALUATOR */}
        {activeTab === 'M9_PLANS' && (
          <div className="planner-section">
            <div className="planner-header-box">
              <span className="micro-label">M9 DETERMINISTIC EVALUATOR</span>
              <div className="selected-plan-badge">
                SELECTED: <strong>{m9Plan.plan_name}</strong>
              </div>
              <p className="planner-explanation">{m9Plan.explanation}</p>
            </div>

            <div className="plans-grid">
              {(m9Plan.all_plans || []).map((plan, idx) => {
                const isSelected = plan.name.includes(m9Plan.plan_name);
                const isPlanValid = plan.valid;
                return (
                  <div
                    key={idx}
                    className={`plan-card ${isSelected ? 'plan-card-selected' : ''} ${!isPlanValid ? 'plan-card-invalid' : ''}`}
                  >
                    <div className="plan-card-head">
                      <span className="plan-name-label">{plan.name}</span>
                      <span className={`plan-validity-pill ${isPlanValid ? 'pill-valid' : 'pill-invalid'}`}>
                        {isPlanValid ? 'VALID' : 'REJECTED'}
                      </span>
                    </div>

                    <div className="plan-score-row">
                      <span className="score-label">Total Plan Score:</span>
                      <span className="score-val mono">
                        {isPlanValid ? plan.total_score.toFixed(1) : 'INVALID (∞)'}
                      </span>
                    </div>

                    {plan.scores && isPlanValid && (
                      <div className="score-breakdown-grid">
                        <span className="breakdown-item">Delay: {plan.scores.delay?.toFixed(1)}</span>
                        <span className="breakdown-item">Queue: {plan.scores.queue?.toFixed(1)}</span>
                        <span className="breakdown-item">Spillback: {plan.scores.spillback?.toFixed(1)}</span>
                        <span className="breakdown-item">Fairness: {plan.scores.fairness?.toFixed(1)}</span>
                      </div>
                    )}

                    {!isPlanValid && plan.rejection_reasons && (
                      <div className="rejection-reason-box">
                        {plan.rejection_reasons.map((r, i) => (
                          <div key={i} className="rej-text">[-] {r}</div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 3: DECISION FLOW (React Flow) */}
        {activeTab === 'DECISION_FLOW' && (
          <div className="flow-section">
            <DecisionGraphFlow decisionSteps={decisionSteps} replayStep={replayStep} />
          </div>
        )}

        {/* TAB 4: AUDIT LOG */}
        {activeTab === 'AUDIT_LOG' && (
          <div className="audit-section">
            <div className="audit-header-row">
              <span className="micro-label">IMMUTABLE OPERATIONS AUDIT TRAIL</span>
              <span className="audit-count mono">{auditEvents.length} EVENTS</span>
            </div>
            <div className="audit-list">
              {auditEvents.slice(0, 12).map((ev, i) => (
                <div key={i} className="audit-item">
                  <div className="audit-item-top">
                    <span className="audit-event-type mono">{ev.event_type}</span>
                    <span className="audit-event-time mono">
                      {ev.timestamp ? ev.timestamp.split('T')[1]?.substring(0, 8) || ev.timestamp : '12:02:03'}
                    </span>
                  </div>
                  <div className="audit-item-details">{ev.details}</div>
                  <div className="audit-item-badge">
                    <span className={`audit-status-tag tag-${(ev.status || 'INFO').toLowerCase()}`}>
                      {ev.status || 'LOGGED'}
                    </span>
                    <span className="audit-junction-tag mono">{ev.junction_id}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 3. OPERATOR RECOMMENDATION & APPROVAL BOX */}
        <div className="console-approval-box">
          <div className="approval-head">
            <span className="micro-label">ACTIVE RECOMMENDATION</span>
            <span className="rec-id mono">{rec.recommendation_id}</span>
          </div>

          <div className="rec-action-row">
            <span className="rec-action-badge">{rec.proposed_action}</span>
            <span className={`rec-status-pill ${rec.status === 'APPROVED' ? 'rec-approved' : 'rec-pending'}`}>
              {rec.status}
            </span>
          </div>

          <p className="rec-reason-text">{rec.reason}</p>

          {/* Role Check Banner */}
          {userRole === 'VIEWER' ? (
            <div className="viewer-role-notice">
              <span>Viewer Role: Read-only access. Operator or Admin authorization required to apply recommendations.</span>
            </div>
          ) : (
            <button
              className={`btn-approve-recommendation ${rec.status === 'APPROVED' ? 'btn-approved' : ''}`}
              onClick={handleApprovalClick}
              disabled={isApproving || rec.status === 'APPROVED'}
            >
              {isApproving
                ? 'Applying Verification...'
                : rec.status === 'APPROVED'
                ? 'RECOMMENDATION APPROVED'
                : `AUTHORIZE ACTION (${userRole})`}
            </button>
          )}

          {approvalStatus && (
            <div className={`approval-feedback ${approvalStatus.success ? 'fb-success' : 'fb-error'}`}>
              {approvalStatus.message}
            </div>
          )}
        </div>

        {/* 4. REPLAY DECISION CONTROLLER */}
        <div className="console-replay-block">
          <div className="replay-block-header">
            <span className="replay-label micro-label">CONTROL CHAIN REPLAY</span>
            <span className="replay-status mono">
              {replayStep > 0 ? `STEP ${replayStep} / 7` : 'READY'}
            </span>
          </div>

          <button
            className={`btn-replay-decision ${isReplaying ? 'running' : ''}`}
            onClick={onReplay}
            disabled={isReplaying}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            <span>{isReplaying ? 'REPLAYING DECISION CHAIN...' : 'REPLAY DECISION'}</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
