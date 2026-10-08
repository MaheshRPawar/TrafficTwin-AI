import React from 'react';
import Sidebar from '../components/Sidebar';
import CorridorDigitalTwin from '../components/CorridorDigitalTwin';
import RightOperationsConsole from '../components/RightOperationsConsole';
import { ScenarioComparisonRechart, JunctionMetricsRechart } from '../components/AnalyticsCharts';
import { CarIcon, ClockIcon, ChartIcon, LinkIcon, ShieldIcon } from '../components/Icons';

export default function OperatorDashboard({
  selectedScenario,
  setSelectedScenario,
  selectedJunction,
  setSelectedJunction,
  userRole,
  setUserRole,
  activeData,
  corridorState,
  currentRecommendation,
  auditEvents,
  connectionStatus,
  isBackendConnected,
  replayStep,
  isReplaying,
  handleReplay,
  approvalStatus,
  handleApproveRecommendation,
  onSwitchToPublic,
}) {
  const metrics = activeData.metrics;

  return (
    <div className="app-container">
      {/* 1. Left Sidebar Navigation */}
      <Sidebar activeNav="Overview" />

      {/* 2. Main Content Viewport */}
      <main className="app-main-content">
        {/* Top Header Bar */}
        <header className="main-header">
          <div className="header-title-block">
            <h1 className="header-title">Traffic Control Intelligence</h1>
            <p className="header-subtitle">Corridor Operations // 4-Junction Dual-Carriageway Arterial</p>
          </div>

          <div className="header-controls">
            {/* View Switcher to Public Simulation */}
            {onSwitchToPublic && (
              <button
                className="btn-switch-public mono"
                onClick={onSwitchToPublic}
                title="Switch to Public Traffic Information Dashboard"
              >
                Public View →
              </button>
            )}

            {/* Connection Indicator */}
            <div className="connection-badge-wrapper">
              <span className={`connection-dot ${isBackendConnected ? 'dot-live' : 'dot-recorded'}`}></span>
              <span className="connection-text mono">{connectionStatus}</span>
            </div>

            {/* Local Role Selector */}
            <div className="control-group">
              <label className="control-label">ROLE</label>
              <div className="select-wrapper">
                <select
                  value={userRole}
                  onChange={(e) => setUserRole(e.target.value)}
                  className="role-select mono"
                >
                  <option value="VIEWER">Viewer (Read-Only)</option>
                  <option value="OPERATOR">Operator (Approved)</option>
                  <option value="ADMIN">Admin (Full Control)</option>
                </select>
                <span className="select-arrow">▼</span>
              </div>
            </div>

            {/* Scenario Selector */}
            <div className="control-group">
              <label className="control-label">SCENARIO</label>
              <div className="select-wrapper">
                <select
                  value={selectedScenario}
                  onChange={(e) => setSelectedScenario(e.target.value)}
                  className="scenario-select mono"
                >
                  <option value="blocked_downstream">Blocked Downstream</option>
                  <option value="normal">Normal Arterial</option>
                  <option value="rush">Peak Rush Hour</option>
                  <option value="ambulance">Emergency Corridor</option>
                </select>
                <span className="select-arrow">▼</span>
              </div>
            </div>

            {/* Replay Control Button */}
            <button
              className={`replay-button ${isReplaying ? 'replaying' : ''}`}
              onClick={handleReplay}
              disabled={isReplaying}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              <span>{isReplaying ? 'Replaying...' : 'Replay'}</span>
            </button>

            {/* Simulation Horizon Scrubber */}
            <div className="control-group time-control-group">
              <div className="time-label-row">
                <span className="control-label">SIMULATION TIME</span>
                <span className="time-value mono">00:02:03 / 00:06:00</span>
              </div>
              <div className="time-scrubber-track">
                <div className="time-scrubber-fill" style={{ width: '34%' }}></div>
                <div className="time-scrubber-thumb" style={{ left: '34%' }}></div>
              </div>
            </div>
          </div>
        </header>

        {/* 5 KPI Metric Cards Row (Technical Labels) */}
        <section className="kpi-cards-grid">
          {/* Card 1: Throughput */}
          <div className="kpi-card">
            <div className="kpi-icon-box bg-blue-soft text-blue">
              <CarIcon />
            </div>
            <div className="kpi-content">
              <div className="kpi-label">Throughput</div>
              <div className="kpi-value-row">
                <span className="kpi-value mono">{metrics.throughput}</span>
                <span className="kpi-unit">veh</span>
                <span className="kpi-trend trend-down">
                  <span className="trend-arrow">↓</span> 0%
                </span>
              </div>
              <div className="kpi-compare-label">vs Reactive Baseline</div>
            </div>
          </div>

          {/* Card 2: Avg Waiting Time */}
          <div className="kpi-card">
            <div className="kpi-icon-box bg-amber-soft text-amber">
              <ClockIcon />
            </div>
            <div className="kpi-content">
              <div className="kpi-label">Avg Waiting Time</div>
              <div className="kpi-value-row">
                <span className="kpi-value mono">{metrics.avgWait}</span>
                <span className="kpi-unit">s</span>
                <span className="kpi-trend trend-down">
                  <span className="trend-arrow">↓</span> 0%
                </span>
              </div>
              <div className="kpi-compare-label">vs Reactive Baseline</div>
            </div>
          </div>

          {/* Card 3: Max Queue Length */}
          <div className="kpi-card">
            <div className="kpi-icon-box bg-green-soft text-green">
              <ChartIcon />
            </div>
            <div className="kpi-content">
              <div className="kpi-label">Max Queue Length</div>
              <div className="kpi-value-row">
                <span className="kpi-value mono">{metrics.maxQueue.toFixed(1)}</span>
                <span className="kpi-unit">veh</span>
                <span className="kpi-trend trend-down">
                  <span className="trend-arrow">↓</span> 0%
                </span>
              </div>
              <div className="kpi-compare-label">vs Reactive Baseline</div>
            </div>
          </div>

          {/* Card 4: Peak Downstream Occupancy */}
          <div className="kpi-card">
            <div className="kpi-icon-box bg-blue-soft text-blue">
              <LinkIcon />
            </div>
            <div className="kpi-content">
              <div className="kpi-label">Peak Downstream</div>
              <div className="kpi-value-row">
                <span className={`kpi-value mono ${metrics.peakDownstreamOcc >= 85 ? 'text-crit' : ''}`}>
                  {metrics.peakDownstreamOcc}%
                </span>
                <span className="kpi-trend trend-up">
                  <span className="trend-arrow">↑</span> +11.1%
                </span>
              </div>
              <div className="kpi-compare-label">Target Link J3_J4</div>
            </div>
          </div>

          {/* Card 5: Spillback Blocks / Safety Enforced */}
          <div className="kpi-card">
            <div className="kpi-icon-box bg-blue-soft text-blue">
              <ShieldIcon />
            </div>
            <div className="kpi-content">
              <div className="kpi-label">Spillback Overrides</div>
              <div className="kpi-value-row">
                <span className="kpi-value mono">{metrics.spillbackBlocks}</span>
                <span className="kpi-status-dash">—</span>
              </div>
              <div className="kpi-compare-label text-slate">M6 Guard Protected</div>
            </div>
          </div>
        </section>

        {/* Dashboard Center Split: Left Operations (Corridor + Recharts) & Right Operations Console */}
        <div className="dashboard-grid-split">
          {/* Left Column (Hero Corridor Digital Twin + Recharts Analytics) */}
          <div className="center-operations-col">
            {/* 3D Corridor Digital Twin */}
            <CorridorDigitalTwin
              scenarioData={activeData}
              selectedJunction={selectedJunction}
              setSelectedJunction={setSelectedJunction}
              replayStep={replayStep}
            />

            {/* Bottom Recharts Grid */}
            <div className="bottom-charts-row">
              <ScenarioComparisonRechart comparisonData={activeData.comparison} />
              <JunctionMetricsRechart scenarioId={selectedScenario} />
            </div>
          </div>

          {/* Right Column (Operations Console + M9 Plans + Decision Flow Graph + Audit Log) */}
          <div className="right-operations-col">
            <RightOperationsConsole
              selectedJunction={selectedJunction}
              scenarioData={activeData}
              corridorState={corridorState}
              currentRecommendation={currentRecommendation}
              auditEvents={auditEvents}
              userRole={userRole}
              replayStep={replayStep}
              isReplaying={isReplaying}
              onReplay={handleReplay}
              onApprove={handleApproveRecommendation}
              approvalStatus={approvalStatus}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
