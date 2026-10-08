import React from 'react';

export default function OperationPanel({ junctionData, selectedJunction, scenarioData, replayStep }) {
  const isJ3 = selectedJunction === 'J3';
  const isBlocked = scenarioData.id === 'blocked_downstream';
  const isCritical = junctionData.risk === 'CRITICAL';
  const isWarning = junctionData.risk === 'WARNING';

  // Badge class
  let badgeClass = 'badge-normal';
  if (isCritical) badgeClass = 'badge-critical';
  else if (isWarning) badgeClass = 'badge-warning';

  return (
    <aside className="operation-panel">
      {/* Header */}
      <div className="op-panel-header">
        <div>
          <div className="micro-label">OPERATION PANEL</div>
          <div className="op-junction-title mono">
            {selectedJunction} // EASTBOUND
          </div>
        </div>
        <span className={`badge ${badgeClass}`}>
          {junctionData.risk}
        </span>
      </div>

      <div className="op-panel-body">
        {/* Metric Grid: Link State */}
        <div className="op-section">
          <div className="section-title">DOWNSTREAM CORRIDOR LINK</div>
          <div className="op-metric-box">
            <div className="op-metric-row">
              <span className="op-metric-lbl">TARGET SEGMENT</span>
              <span className="op-metric-val mono">{junctionData.downstreamEdge} (200m)</span>
            </div>
            <div className="op-metric-row">
              <span className="op-metric-lbl">OCCUPANCY</span>
              <span className={`op-metric-val mono ${isCritical ? 'highlight-crit' : ''}`}>
                {junctionData.downstreamOcc}%
              </span>
            </div>
            {/* Occupancy Progress Bar */}
            <div className="op-progress-track">
              <div
                className={`op-progress-fill ${isCritical ? 'fill-crit' : isWarning ? 'fill-warn' : 'fill-norm'}`}
                style={{ width: `${Math.min(junctionData.downstreamOcc, 100)}%` }}
              ></div>
              <div className="threshold-marker warn" style={{ left: '75%' }} title="Warning 75%"></div>
              <div className="threshold-marker crit" style={{ left: '85%' }} title="Critical 85%"></div>
            </div>
            <div className="op-metric-row">
              <span className="op-metric-lbl">VEHICLES / CAPACITY</span>
              <span className="op-metric-val mono">
                {junctionData.downstreamVehs} / {junctionData.downstreamCap} VEH
              </span>
            </div>
          </div>
        </div>

        {/* Approach Queues & Signal State */}
        <div className="op-section">
          <div className="section-title">APPROACH & SIGNAL STATE</div>
          <div className="op-metric-grid">
            <div className="op-stat-card">
              <span className="micro-label">MAIN QUEUE</span>
              <span className="op-stat-num mono">{junctionData.queueMain}</span>
              <span className="op-stat-sub">VEHICLES (EB)</span>
            </div>
            <div className="op-stat-card">
              <span className="micro-label">CROSS QUEUE</span>
              <span className="op-stat-num mono">{junctionData.queueCross}</span>
              <span className="op-stat-sub">VEHICLES (NS)</span>
            </div>
            <div className="op-stat-card">
              <span className="micro-label">SIGNAL PHASE</span>
              <span className="op-stat-num mono">
                {isJ3 && replayStep >= 6 ? 'P1' : `P${junctionData.phase}`}
              </span>
              <span className="op-stat-sub">
                {isJ3 && replayStep >= 6 ? 'MAIN YELLOW' : junctionData.phaseName}
              </span>
            </div>
            <div className="op-stat-card">
              <span className="micro-label">ELAPSED GREEN</span>
              <span className="op-stat-num mono">{junctionData.elapsedGreen.toFixed(1)}s</span>
              <span className="op-stat-sub">MIN 10s / MAX 40s</span>
            </div>
          </div>
        </div>

        {/* Controller Decision Chain */}
        <div className="op-section">
          <div className="section-title">CONTROLLER AUDIT VERDICT</div>
          <div className="op-decision-list">
            <div className="op-decision-item">
              <div className="op-dec-header">
                <span className="op-dec-layer mono">M3 REACTIVE PROPOSAL</span>
                <span className="badge badge-muted mono">{junctionData.m3Action}</span>
              </div>
              <div className="op-dec-desc">
                {isJ3 && isBlocked
                  ? 'Q_main (12) >= 3; proposes extending green by +5.0s.'
                  : junctionData.reason}
              </div>
            </div>

            <div className={`op-decision-item ${isCritical ? 'item-critical' : ''}`}>
              <div className="op-dec-header">
                <span className="op-dec-layer mono">M6 SPILLBACK GUARD</span>
                <span className={`badge ${isCritical ? 'badge-critical' : 'badge-active'} mono`}>
                  {junctionData.m6Action}
                </span>
              </div>
              <div className="op-dec-desc">
                {isCritical
                  ? 'Downstream occupancy >= 85.0% threshold. Green extension BLOCKED to protect link J3_J4.'
                  : 'Downstream capacity adequate; no spillback intervention required.'}
              </div>
            </div>

            <div className="op-decision-item">
              <div className="op-dec-header">
                <span className="op-dec-layer mono">M5 SAFETY FIREWALL</span>
                <span className="badge badge-normal mono">{junctionData.m5Verdict}</span>
              </div>
              <div className="op-dec-desc">
                Min green 10.0s satisfied (elapsed: {junctionData.elapsedGreen.toFixed(1)}s). Safe yellow clearance (3.0s) verified.
              </div>
            </div>
          </div>
        </div>

        {/* Operational Commentary */}
        <div className="op-section">
          <div className="section-title">OPERATIONAL ADVISORY</div>
          <div className="op-note-box">
            {isJ3 && isBlocked ? (
              <p>
                <strong>PROTECTING DOWNSTREAM BUFFER:</strong> J3 main green terminates early to prevent link J3_J4 from overflowing. Halting release allows downstream bottleneck to recover and maintains cross-street progression.
              </p>
            ) : (
              <p>
                <strong>CYCLIC HARMONY:</strong> Intersection operates within normal capacity limits. Reactive queue balancing active with M5 safety boundary enforcement.
              </p>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
