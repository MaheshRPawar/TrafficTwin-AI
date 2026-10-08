import React from 'react';

export default function DecisionTrace({
  decisionSteps,
  replayStep,
  isReplaying,
  onReplay,
}) {
  return (
    <div className="decision-trace-container">
      <div className="trace-header">
        <div className="trace-header-left">
          <span className="section-title">DECISION RECORD</span>
          <span className="trace-sub mono">M3 → M6 → M5 → TraCI EXECUTION CHAIN</span>
        </div>
        <div className="trace-header-right">
          <button
            className={`btn-replay ${isReplaying ? 'active' : ''}`}
            onClick={onReplay}
            disabled={isReplaying}
          >
            <span className="replay-icon">↺</span>
            {isReplaying ? 'REPLAYING TRACE...' : 'REPLAY DECISION'}
          </button>
        </div>
      </div>

      <div className="trace-grid">
        {decisionSteps.map((step, idx) => {
          const stepNum = idx + 1;
          const isActive = stepNum <= replayStep;
          const isCurrent = stepNum === replayStep;

          let cardClass = 'trace-card';
          if (isActive) cardClass += ' active';
          if (isCurrent) cardClass += ' current';
          if (step.status === 'CRITICAL') cardClass += ' status-critical';
          if (step.status === 'BLOCKED') cardClass += ' status-blocked';

          return (
            <div key={step.step} className={cardClass}>
              <div className="card-top">
                <span className="step-num mono">{step.step}</span>
                <span className={`card-badge badge badge-${
                  step.status === 'CRITICAL' ? 'critical' :
                  step.status === 'BLOCKED' ? 'critical' :
                  step.status === 'VALIDATED' ? 'normal' :
                  step.status === 'EXECUTED' ? 'active' : 'muted'
                }`}>
                  {step.status}
                </span>
              </div>
              <div className="card-title">{step.title}</div>
              <div className="card-headline">{step.headline}</div>
              <div className="card-data mono">{step.data}</div>
              <div className="card-detail">{step.detail}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
