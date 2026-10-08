import React from 'react';

export default function TopBar({ activeScenario, scenarioData }) {
  return (
    <header className="top-bar">
      <div className="top-bar-left">
        <span className="brand-title">TRAFFICTWIN</span>
        <span className="brand-separator">/</span>
        <span className="brand-sub">CORRIDOR OPERATIONS</span>
        <span className="status-indicator">
          <span className="status-dot"></span>
          OPERATIONAL
        </span>
      </div>

      <div className="top-bar-center">
        <span className="active-scenario-tag">
          SCENARIO: <strong>{scenarioData.name}</strong>
        </span>
      </div>

      <div className="top-bar-right">
        <div className="meta-item">
          <span className="meta-label">SOURCE</span>
          <span className="meta-val">RECORDED SIMULATION</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">ENGINE</span>
          <span className="meta-val mono">SUMO 1.27.1</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">SEED</span>
          <span className="meta-val mono">42</span>
        </div>
        <div className="meta-item">
          <span className="meta-label">STEP</span>
          <span className="meta-val mono">1.0s</span>
        </div>
      </div>
    </header>
  );
}
