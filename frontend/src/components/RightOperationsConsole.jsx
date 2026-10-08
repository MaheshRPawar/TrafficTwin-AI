import React, { useState } from 'react';
import DecisionGraphFlow from './DecisionGraphFlow';

export default function RightOperationsConsole({
  selectedJunction = 'J3',
  scenarioData,
  replayStep = 0,
  isReplaying = false,
  onReplay,
}) {
  const [activeTab, setActiveTab] = useState('CURRENT_STATE');

  const jData = scenarioData.junctions[selectedJunction] || scenarioData.junctions.J3;
  const isJ3 = selectedJunction === 'J3';
  const isBlocked = scenarioData.id === 'blocked_downstream';
  const isCrit = jData.risk === 'CRITICAL';
  const isWarn = jData.risk === 'WARNING';

  // Decision trace steps from scenario
  const decisionSteps = scenarioData.decisionTrace || [];

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
          {jData.risk}
        </div>
      </div>

      {/* 2. OPERATIONAL TABS */}
      <div className="console-tabs">
        <button
          className={`console-tab-btn ${activeTab === 'CURRENT_STATE' ? 'active' : ''}`}
          onClick={() => setActiveTab('CURRENT_STATE')}
        >
          CURRENT STATE
        </button>
        <button
          className={`console-tab-btn ${activeTab === 'DECISION_FLOW' ? 'active' : ''}`}
          onClick={() => setActiveTab('DECISION_FLOW')}
        >
          DECISION GRAPH
        </button>
      </div>

      <div className="console-body">
        {/* CURRENT STATE VIEW */}
        {activeTab === 'CURRENT_STATE' && (
          <div className="state-section">
            <div className="state-metric-grid">
              <div className="state-row">
                <span className="state-label">Approach Queue</span>
                <span className={`state-val mono ${isCrit ? 'text-crit bold' : ''}`}>
                  {jData.queueMain} vehicles
                </span>
              </div>

              <div className="state-row">
                <span className="state-label">Cross Street Queue</span>
                <span className="state-val mono">{jData.queueCross} vehicles</span>
              </div>

              <div className="state-row">
                <span className="state-label">Target Link</span>
                <span className="state-val mono">{jData.downstreamEdge} (200m)</span>
              </div>

              <div className="state-row">
                <span className="state-label">Link Storage</span>
                <span className="state-val mono">
                  {jData.downstreamVehs} / {jData.downstreamCap} veh
                </span>
              </div>

              <div className="state-row">
                <span className="state-label">Downstream Occupancy</span>
                <span className={`state-val mono ${isCrit ? 'text-crit bold' : ''}`}>
                  {jData.downstreamOcc}%
                </span>
              </div>

              <div className="occupancy-progress-bar">
                <div
                  className={`progress-fill ${isCrit ? 'fill-crit' : isWarn ? 'fill-warn' : 'fill-norm'}`}
                  style={{ width: `${Math.min(jData.downstreamOcc, 100)}%` }}
                ></div>
                <span className="threshold-line warn" style={{ left: '75%' }} title="Warning 75%"></span>
                <span className="threshold-line crit" style={{ left: '85%' }} title="Critical 85%"></span>
              </div>

              <div className="state-row">
                <span className="state-label">Signal State</span>
                <span className="state-val mono highlight-blue">
                  {isJ3 && isBlocked && replayStep >= 6 ? 'Phase 1 (Yellow Clearance)' : `Phase ${jData.phase} (${jData.phaseName})`}
                </span>
              </div>

              <div className="state-row">
                <span className="state-label">Elapsed Green</span>
                <span className="state-val mono">{jData.elapsedGreen?.toFixed(1)}s (Max 40.0s)</span>
              </div>

              <div className="state-row">
                <span className="state-label">Spillback Risk</span>
                <span className={`state-val mono ${isCrit ? 'text-crit bold' : ''}`}>
                  {jData.risk}
                </span>
              </div>
            </div>

            {/* Operator Advisory Banner */}
            <div className={`operator-advisory ${isCrit ? 'adv-crit' : 'adv-norm'}`}>
              <div className="adv-title">
                {isCrit ? '⚠ CRITICAL SPILLBACK HAZARD' : '✓ CORRIDOR IN STABLE EQUILIBRIUM'}
              </div>
              <p className="adv-text">
                {isCrit
                  ? 'Downstream storage exceeds 85.0% threshold. Signal controller preempts main extension to prevent link gridlock.'
                  : 'Traffic release rate within downstream storage capacity. Safety firewall active.'}
              </p>
            </div>
          </div>
        )}

        {/* DECISION GRAPH VIEW (React Flow) */}
        {activeTab === 'DECISION_FLOW' && (
          <div className="flow-section">
            <DecisionGraphFlow decisionSteps={decisionSteps} replayStep={replayStep} />
          </div>
        )}

        {/* 3. REPLAY DECISION CONTROLLER */}
        <div className="console-replay-block">
          <div className="replay-block-header">
            <span className="replay-label micro-label">CONTROL CHAIN REPLAY</span>
            <span className="replay-status mono">
              {replayStep > 0 ? `STEP ${replayStep} / 6` : 'READY'}
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

          <p className="replay-caption">
            Replays: <strong>M3 Reactive</strong> proposal → <strong>M6 Spillback</strong> guard check → <strong>M5 Safety Firewall</strong> boundary verification → <strong>TraCI</strong> actuation.
          </p>
        </div>
      </div>
    </aside>
  );
}
