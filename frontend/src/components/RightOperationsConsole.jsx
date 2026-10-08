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
}) {
  const [activeTab, setActiveTab] = useState('CURRENT_STATE');
  const [isApproving, setIsApproving] = useState(false);

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
      {/* 1. TOP HEADER: Junction Identity & Status */}
      <div className="console-header">
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
        {/* TAB 1: CURRENT STATE VIEW */}
        {activeTab === 'CURRENT_STATE' && (
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
                {isCrit ? '⚠ CRITICAL SPILLBACK HAZARD' : '✓ CORRIDOR IN STABLE EQUILIBRIUM'}
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
                          <div key={i} className="rej-text">✕ {r}</div>
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
              <span>🔒 Viewer Role: Read-only access. Operator or Admin authorization required to apply recommendations.</span>
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
                ? '✓ RECOMMENDATION APPROVED'
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
