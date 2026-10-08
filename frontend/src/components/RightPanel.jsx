import React, { useState } from 'react';
import { CarIcon, LinkIcon, ClockIcon, ShieldIcon } from './Icons';

export default function RightPanel({ selectedJunction }) {
  const [activeTab, setActiveTab] = useState('Current State');

  const decisions = [
    {
      num: 1,
      color: 'blue',
      title: 'Traffic State',
      time: '02:03',
      detail: 'J3 queue = 12, downstream occupancy = 88.7%',
    },
    {
      num: 2,
      color: 'blue',
      title: 'Reactive Control (M3)',
      time: '02:03',
      detail: 'Proposed: EXTEND GREEN (+5s)',
    },
    {
      num: 3,
      color: 'red',
      isBlocked: true,
      title: 'Spillback Protection (M6)',
      time: '02:03',
      headline: 'EXTENSION BLOCKED',
      detail: 'Reason: downstream_occupancy_critical',
    },
    {
      num: 4,
      color: 'green',
      title: 'Safety Firewall (M5)',
      time: '02:03',
      detail: 'Safe transition validated\nPhase 0 → Phase 1',
    },
    {
      num: 5,
      color: 'blue',
      title: 'Signal Action',
      time: '02:04',
      detail: 'J3 transitioned to Phase 1 (Yellow)',
    },
  ];

  return (
    <aside className="right-panel">
      {/* Junction Header */}
      <div className="rp-header">
        <div className="rp-title-row">
          <h2 className="rp-title">{selectedJunction || 'J3'} / Eastbound</h2>
          <span className="rp-badge-critical">+ CRITICAL</span>
        </div>
        <p className="rp-subtitle">Live Junction State (Recorded)</p>
      </div>

      {/* Tabs */}
      <div className="rp-tabs">
        {['Current State', 'Signal Phase', 'Downstream'].map((tab) => (
          <button
            key={tab}
            className={`rp-tab-btn ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* State List */}
      <div className="rp-state-list">
        <div className="rp-state-row">
          <div className="rp-state-label">
            <span className="rp-state-icon"><CarIcon /></span>
            <span>Main Queue</span>
          </div>
          <span className="rp-state-val">12 vehicles</span>
        </div>

        <div className="rp-state-row">
          <div className="rp-state-label">
            <span className="rp-state-icon"><LinkIcon /></span>
            <span>Downstream Link</span>
          </div>
          <span className="rp-state-val mono">J3_J4</span>
        </div>

        <div className="rp-state-row">
          <div className="rp-state-label">
            <span className="rp-state-icon"><CarIcon /></span>
            <span>Downstream Vehicles</span>
          </div>
          <span className="rp-state-val mono">47 / 53</span>
        </div>

        <div className="rp-state-row">
          <div className="rp-state-label">
            <span className="rp-state-icon"><ClockIcon /></span>
            <span>Downstream Occupancy</span>
          </div>
          <span className="rp-state-val val-crit">88.7%</span>
        </div>

        <div className="rp-state-row">
          <div className="rp-state-label">
            <span className="rp-state-icon"><ShieldIcon /></span>
            <span>Spillback Risk</span>
          </div>
          <span className="rp-state-val val-crit bold">CRITICAL</span>
        </div>
      </div>

      {/* Decision Record (This Event) */}
      <div className="rp-decision-section">
        <h3 className="rp-section-title">Decision Record (This Event)</h3>

        <div className="rp-decision-timeline">
          {decisions.map((step) => (
            <div
              key={step.num}
              className={`rp-step-item ${step.isBlocked ? 'step-blocked-bg' : ''}`}
            >
              <div className={`rp-step-circle circle-${step.color}`}>
                {step.num}
              </div>
              <div className="rp-step-content">
                <div className="rp-step-header">
                  <span className="rp-step-title">{step.title}</span>
                  <span className="rp-step-time mono">{step.time}</span>
                </div>
                {step.headline && (
                  <div className="rp-step-headline val-crit bold">
                    {step.headline}
                  </div>
                )}
                <div className="rp-step-detail">
                  {step.detail.split('\n').map((line, idx) => (
                    <div key={idx}>{line}</div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
