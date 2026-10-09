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
  // Simulation playback & locate
  isPlaying = true,
  simTime = 123.0,
  simTotalTime = 360.0,
  simSpeed = 1.0,
  handlePlay,
  handlePause,
  handleStep,
  handleReset,
  handleSpeedChange,
  selectedItemType = 'junction',
  selectedItemId = 'J3',
  handleLocate,
  roadsList = [],
  vehiclesList = [],
}) {
  const metrics = activeData.metrics;

  const formatTime = (secs) => {
    const s = Math.floor(secs || 0);
    const mm = String(Math.floor(s / 60)).padStart(2, '0');
    const ss = String(s % 60).padStart(2, '0');
    return `00:${mm}:${ss}`;
  };

  const progressPercent = Math.min(100, Math.max(0, (simTime / simTotalTime) * 100));

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

            {/* Locate Object Selector */}
            <div className="control-group">
              <label className="control-label">LOCATE</label>
              <div className="select-wrapper">
                <select
                  value={`${selectedItemType}:${selectedItemId}`}
                  onChange={(e) => {
                    const [type, id] = e.target.value.split(':');
                    if (handleLocate) handleLocate(type, id);
                  }}
                  className="locate-select mono"
                >
                  <optgroup label="Junctions">
                    <option value="junction:J1">J1 (West Entry)</option>
                    <option value="junction:J2">J2 (West-Central)</option>
                    <option value="junction:J3">J3 (Bottleneck)</option>
                    <option value="junction:J4">J4 (East Exit)</option>
                  </optgroup>
                  <optgroup label="Road Segments">
                    <option value="road:W0_J1">W0_J1 (Inflow 250m)</option>
                    <option value="road:J1_J2">J1_J2 (Corridor 250m)</option>
                    <option value="road:J2_J3">J2_J3 (Corridor 250m)</option>
                    <option value="road:J3_J4">J3_J4 (Bottleneck 250m)</option>
                    <option value="road:J4_E5">J4_E5 (Exit 250m)</option>
                  </optgroup>
                  <optgroup label="Vehicles">
                    <option value="vehicle:amb_1">amb_1 (Emergency Ambulance)</option>
                    <option value="vehicle:veh_eb_12">veh_eb_12 (Passenger Eastbound)</option>
                    <option value="vehicle:veh_eb_18">veh_eb_18 (Passenger Queued)</option>
                    {vehiclesList && vehiclesList.filter(v => !['amb_1', 'veh_eb_12', 'veh_eb_18'].includes(v.vehicle_id)).map(v => (
                      <option key={v.vehicle_id} value={`vehicle:${v.vehicle_id}`}>
                        {v.vehicle_id} ({v.type || 'passenger'})
                      </option>
                    ))}
                  </optgroup>
                </select>
                <span className="select-arrow">▼</span>
              </div>
            </div>

            {/* Interactive Simulation Controls (Play, Pause, Step, Reset, Speed) */}
            <div className="sim-control-btn-group">
              <button
                className={`sim-btn-play ${isPlaying ? 'active' : ''}`}
                onClick={isPlaying ? handlePause : handlePlay}
                title={isPlaying ? 'Pause Simulation' : 'Play Simulation'}
              >
                {isPlaying ? (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <rect x="6" y="4" width="4" height="16" />
                    <rect x="14" y="4" width="4" height="16" />
                  </svg>
                ) : (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                )}
                <span>{isPlaying ? 'PAUSE' : 'PLAY'}</span>
              </button>

              <button
                className="sim-btn-step"
                onClick={handleStep}
                title="Advance simulation by 1 step (+1s)"
              >
                <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor">
                  <polygon points="5 4 15 12 5 20 5 4" />
                  <line x1="19" y1="5" x2="19" y2="19" stroke="currentColor" strokeWidth="3" />
                </svg>
                <span>STEP</span>
              </button>

              <button
                className="sim-btn-reset"
                onClick={handleReset}
                title="Reset simulation to beginning (t=0s)"
              >
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                  <path d="M3 3v5h5" />
                </svg>
                <span>RESET</span>
              </button>

              {/* Speed Selector */}
              <div className="select-wrapper sim-speed-wrapper">
                <select
                  value={simSpeed}
                  onChange={(e) => handleSpeedChange && handleSpeedChange(e.target.value)}
                  className="sim-speed-select mono"
                  title="Simulation Speed Multiplier"
                >
                  <option value="1">1x</option>
                  <option value="2">2x</option>
                  <option value="4">4x</option>
                </select>
                <span className="select-arrow">▼</span>
              </div>
            </div>

            {/* Replay Control Button */}
            <button
              className={`replay-button ${isReplaying ? 'replaying' : ''}`}
              onClick={handleReplay}
              disabled={isReplaying}
              title="Replay 7-step decision flow trace"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              <span>{isReplaying ? 'Replaying...' : 'Replay'}</span>
            </button>

            {/* Simulation Horizon Scrubber */}
            <div className="control-group time-control-group">
              <div className="time-label-row">
                <span className="control-label">SIMULATION TIME</span>
                <span className="time-value mono">{formatTime(simTime)} / {formatTime(simTotalTime)}</span>
              </div>
              <div className="time-scrubber-track">
                <div className="time-scrubber-fill" style={{ width: `${progressPercent}%` }}></div>
                <div className="time-scrubber-thumb" style={{ left: `${progressPercent}%` }}></div>
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
              selectedItemType={selectedItemType}
              selectedItemId={selectedItemId}
              onSelectItem={handleLocate}
              roadsList={roadsList}
              vehiclesList={vehiclesList}
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
              selectedItemType={selectedItemType}
              selectedItemId={selectedItemId}
              onSelectItem={handleLocate}
              roadsList={roadsList}
              vehiclesList={vehiclesList}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
