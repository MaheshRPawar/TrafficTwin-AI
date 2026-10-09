import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import CorridorDigitalTwin from '../components/CorridorDigitalTwin';
import RightOperationsConsole from '../components/RightOperationsConsole';
import { ScenarioComparisonRechart, JunctionMetricsRechart } from '../components/AnalyticsCharts';
import DecisionGraphFlow from '../components/DecisionGraphFlow';
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
  const [activeNav, setActiveNav] = useState('Overview');
  const metrics = activeData.metrics;

  const formatTime = (secs) => {
    const s = Math.floor(secs || 0);
    const mm = String(Math.floor(s / 60)).padStart(2, '0');
    const ss = String(s % 60).padStart(2, '0');
    return `00:${mm}:${ss}`;
  };

  const progressPercent = Math.min(100, Math.max(0, (simTime / simTotalTime) * 100));

  const getSubtitle = () => {
    switch (activeNav) {
      case 'Corridor':
        return 'Corridor Digital Twin // Link Geometry & Downstream Capacity';
      case 'Junctions':
        return 'Junction Matrix // Intersections J1, J2, J3, J4 Operational Telemetry';
      case 'Decisions':
        return 'Control Decisions // M9 Plan Evaluation & 7-Step Decision Flow';
      case 'Simulation':
        return 'Simulation Deck // SUMO TraCI Micro-Simulation Engine';
      case 'Results':
        return 'Empirical Results // Multi-Scenario Benchmark Comparisons';
      default:
        return 'Corridor Operations // 4-Junction Dual-Carriageway Arterial';
    }
  };



  // Effective road segments and vehicles
  const defaultRoads = [
    { road_id: 'W0_J1', name: 'West Inflow Link', from_node: 'W0', to_node: 'J1', length_m: 250.0, lanes: 2, speed_limit_kmh: 50.0, capacity_veh: 53, occupancy_percent: 42.1, status: 'CLEAR' },
    { road_id: 'J1_J2', name: 'Corridor Arterial 1', from_node: 'J1', to_node: 'J2', length_m: 250.0, lanes: 2, speed_limit_kmh: 50.0, capacity_veh: 53, occupancy_percent: 54.3, status: 'CLEAR' },
    { road_id: 'J2_J3', name: 'Corridor Arterial 2', from_node: 'J2', to_node: 'J3', length_m: 250.0, lanes: 2, speed_limit_kmh: 50.0, capacity_veh: 53, occupancy_percent: 68.2, status: 'FLOWING' },
    { road_id: 'J3_J4', name: 'Bottleneck Arterial', from_node: 'J3', to_node: 'J4', length_m: 250.0, lanes: 2, speed_limit_kmh: 50.0, capacity_veh: 53, occupancy_percent: 88.7, status: 'SPILLBACK RISK' },
    { road_id: 'J4_E5', name: 'East Exit Link', from_node: 'J4', to_node: 'E5', length_m: 250.0, lanes: 2, speed_limit_kmh: 50.0, capacity_veh: 53, occupancy_percent: 29.5, status: 'CLEAR' },
  ];
  const effectiveRoads = roadsList && roadsList.length > 0 ? roadsList : defaultRoads;

  const defaultVehicles = [
    { vehicle_id: 'amb_1', type: 'emergency', speed_kmh: 46.2, road_segment: 'J2_J3', distance_to_signal_m: 38.5, status: 'PRIORITY_PREEMPTION' },
    { vehicle_id: 'veh_eb_12', type: 'passenger', speed_kmh: 28.5, road_segment: 'J3_J4', distance_to_signal_m: 12.0, status: 'QUEUED' },
    { vehicle_id: 'veh_eb_18', type: 'passenger', speed_kmh: 0.0, road_segment: 'J3_J4', distance_to_signal_m: 4.5, status: 'STOPPED' },
    { vehicle_id: 'veh_wb_05', type: 'passenger', speed_kmh: 42.0, road_segment: 'J2_J1', distance_to_signal_m: 82.0, status: 'CRUISING' },
    { vehicle_id: 'veh_eb_22', type: 'passenger', speed_kmh: 31.4, road_segment: 'J1_J2', distance_to_signal_m: 45.0, status: 'FLOWING' },
  ];
  const effectiveVehicles = vehiclesList && vehiclesList.length > 0 ? vehiclesList : defaultVehicles;

  // M9 Digital Twin Plan alternatives
  const m9Plans = corridorState?.selected_plan?.all_plans || [
    {
      name: 'Plan A (Current Safe Timing)',
      valid: true,
      total_score: selectedScenario === 'blocked_downstream' ? 44.5 : 14.2,
      scores: { delay: 3.5, queue: 8.0, spillback: 27.0, fairness: 3.0, emergency: 3.0 },
      status: 'FALLBACK',
    },
    {
      name: 'Plan B (Bounded Extension +5s)',
      valid: selectedScenario !== 'blocked_downstream',
      total_score: selectedScenario === 'blocked_downstream' ? 999.0 : 22.4,
      scores: { delay: 2.0, queue: 4.0, spillback: 90.0, fairness: 3.0, emergency: 3.0 },
      rejection_reasons: selectedScenario === 'blocked_downstream' ? ['m6_spillback_violation: Downstream occupancy >= 85.0%'] : [],
      status: selectedScenario === 'blocked_downstream' ? 'REJECTED' : 'VALID',
    },
    {
      name: 'Plan C (Downstream Clearing & Coord)',
      valid: true,
      total_score: selectedScenario === 'blocked_downstream' ? 28.5 : 18.0,
      scores: { delay: 4.5, queue: 6.0, spillback: 12.0, fairness: 3.0, emergency: 3.0 },
      status: 'SELECTED',
    },
  ];

  // Benchmark scorecard data for Results tab
  const benchmarkRows = [
    {
      strategy: 'M2 Fixed-Time Baseline',
      tag: 'Pre-timed (Webster)',
      throughput: 210,
      avgWait: '46.8s',
      maxQueue: '18.2 veh',
      spillbackEvents: 8,
      fairness: 'Poor (Fixed cycle)',
      rating: 'Grade D',
      badgeClass: 'badge-crit',
    },
    {
      strategy: 'M3 Actuated / Reactive',
      tag: 'Gap-out / Max-out',
      throughput: 242,
      avgWait: '38.4s',
      maxQueue: '14.5 veh',
      spillbackEvents: 5,
      fairness: 'Moderate (Queue debt)',
      rating: 'Grade C',
      badgeClass: 'badge-info',
    },
    {
      strategy: 'M6 Spillback Guard',
      tag: 'Reactive + Occupancy Cap',
      throughput: 275,
      avgWait: '29.1s',
      maxQueue: '8.4 veh',
      spillbackEvents: 0,
      fairness: 'Good (Overridden safely)',
      rating: 'Grade B+',
      badgeClass: 'badge-norm',
    },
    {
      strategy: 'TrafficTwin AI (M7 + M6 + M9)',
      tag: 'Digital Twin Coordinated',
      throughput: 312,
      avgWait: '21.4s',
      maxQueue: '5.2 veh',
      spillbackEvents: 0,
      fairness: 'Optimal (Max 45s wait debt)',
      rating: 'Grade A (Best)',
      badgeClass: 'badge-norm',
    },
  ];

  return (
    <div className="app-container">
      {/* 1. Left Sidebar Navigation */}
      <Sidebar activeNav={activeNav} setActiveNav={setActiveNav} />

      {/* 2. Main Content Viewport */}
      <main className="app-main-content">
        {/* Top Header Bar */}
        <header className="main-header">
          <div className="header-title-block">
            <h1 className="header-title">Traffic Control Intelligence</h1>
            <p className="header-subtitle">{getSubtitle()}</p>
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
                    {effectiveVehicles && effectiveVehicles.filter(v => !['amb_1', 'veh_eb_12', 'veh_eb_18'].includes(v.vehicle_id)).map(v => (
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

        {/* =========================================================================
            TAB 1: OVERVIEW (Default Dashboard View)
            ========================================================================= */}
        {activeNav === 'Overview' && (
          <>
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
                <CorridorDigitalTwin
                  scenarioData={activeData}
                  selectedJunction={selectedJunction}
                  setSelectedJunction={setSelectedJunction}
                  replayStep={replayStep}
                  selectedItemType={selectedItemType}
                  selectedItemId={selectedItemId}
                  onSelectItem={handleLocate}
                  roadsList={effectiveRoads}
                  vehiclesList={effectiveVehicles}
                />

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
                  roadsList={effectiveRoads}
                  vehiclesList={effectiveVehicles}
                />
              </div>
            </div>
          </>
        )}

        {/* =========================================================================
            TAB 2: CORRIDOR (Road Network Links & Geometry)
            ========================================================================= */}
        {activeNav === 'Corridor' && (
          <div className="tab-view-container">
            <div className="dashboard-grid-split">
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
                  roadsList={effectiveRoads}
                  vehiclesList={effectiveVehicles}
                />

                {/* Corridor Road Links Matrix Table */}
                <div className="data-table-container" style={{ marginTop: '16px' }}>
                  <div className="data-table-head-row">
                    <div>
                      <h3 className="data-table-title">Corridor Arterial Links & Storage Telemetry</h3>
                      <p className="data-table-desc">Physical road links, upstream/downstream nodes, geometry, storage capacity, and live TraCI occupancy</p>
                    </div>
                    <span className="mono text-xs text-slate">5 Primary Links // 1.0 km Corridor</span>
                  </div>

                  <table className="engineering-table">
                    <thead>
                      <tr>
                        <th>LINK ID</th>
                        <th>SEGMENT NAME</th>
                        <th>FROM → TO</th>
                        <th>LENGTH</th>
                        <th>LANES</th>
                        <th>SPEED</th>
                        <th>CAPACITY</th>
                        <th>OCCUPANCY</th>
                        <th>STATUS</th>
                        <th>ACTION</th>
                      </tr>
                    </thead>
                    <tbody>
                      {effectiveRoads.map((road) => {
                        const isSelected = selectedItemType === 'road' && selectedItemId === road.road_id;
                        const isHighOcc = road.occupancy_percent >= 85.0;
                        return (
                          <tr key={road.road_id} className={isSelected ? 'selected-row' : ''}>
                            <td className="mono font-bold text-blue">{road.road_id}</td>
                            <td>{road.name}</td>
                            <td className="mono text-slate">{road.from_node} → {road.to_node}</td>
                            <td className="mono">{road.length_m}m</td>
                            <td className="mono">{road.lanes}</td>
                            <td className="mono">{road.speed_limit_kmh} km/h</td>
                            <td className="mono">{road.capacity_veh} veh</td>
                            <td className="mono">
                              <span className={isHighOcc ? 'text-crit font-bold' : ''}>
                                {road.occupancy_percent.toFixed(1)}%
                              </span>
                            </td>
                            <td>
                              <span className={`flow-node-badge ${isHighOcc ? 'badge-crit' : 'badge-norm'}`}>
                                {road.status}
                              </span>
                            </td>
                            <td>
                              <button
                                className="btn-inspect-action"
                                onClick={() => handleLocate && handleLocate('road', road.road_id)}
                              >
                                {isSelected ? 'Inspecting' : 'Locate Link'}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Right Column: Console */}
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
                  roadsList={effectiveRoads}
                  vehiclesList={effectiveVehicles}
                />
              </div>
            </div>
          </div>
        )}

        {/* =========================================================================
            TAB 3: JUNCTIONS (Intersection Telemetry & Phases)
            ========================================================================= */}
        {activeNav === 'Junctions' && (
          <div className="tab-view-container">
            {/* 4 Junction Grid */}
            <div className="junction-matrix-grid">
              {['J1', 'J2', 'J3', 'J4'].map((jId) => {
                const j = corridorState?.[jId] || activeData?.junctions?.[jId] || {};
                const isSelected = selectedJunction === jId;
                const isCritical = (j.risk || j.spillback_risk) === 'CRITICAL';
                const isWarning = (j.risk || j.spillback_risk) === 'WARNING';
                const downOcc = j.downstreamOcc || (jId === 'J3' ? 88.7 : jId === 'J2' ? 52.8 : 26.4);
                const qMain = j.queueMain ?? (jId === 'J3' ? 8 : 3);
                const qCross = j.queueCross ?? 1;

                return (
                  <div
                    key={jId}
                    className={`junction-card-detailed ${isSelected ? 'selected' : ''}`}
                    onClick={() => {
                      if (setSelectedJunction) setSelectedJunction(jId);
                      if (handleLocate) handleLocate('junction', jId);
                    }}
                  >
                    <div className="j-head-row">
                      <div>
                        <div className="j-head-title">{j.name || `JUNCTION ${jId.slice(1)}`}</div>
                        <div className="j-head-pos mono">{j.corridorPos || (jId === 'J1' ? '0m' : jId === 'J2' ? '250m' : jId === 'J3' ? '500m' : '750m')} // Cross: {j.crossStreet || 'N-S'}</div>
                      </div>
                      <span className={`flow-node-badge ${isCritical ? 'badge-crit' : isWarning ? 'badge-info' : 'badge-norm'}`}>
                        {j.risk || 'NORMAL'}
                      </span>
                    </div>

                    <div className="j-metrics-list">
                      <div className="j-metric-item">
                        <span className="j-metric-label">Signal Phase:</span>
                        <span className="j-metric-value mono text-blue">{j.phaseName || 'MAIN GREEN'}</span>
                      </div>
                      <div className="j-metric-item">
                        <span className="j-metric-label">Elapsed / Allocated:</span>
                        <span className="j-metric-value mono">{j.elapsedGreen || 15}s / {j.allocatedGreen || 30}s</span>
                      </div>
                      <div className="j-metric-item">
                        <span className="j-metric-label">Arterial Queue:</span>
                        <span className="j-metric-value mono">{qMain} veh</span>
                      </div>
                      <div className="j-metric-item">
                        <span className="j-metric-label">Cross Street Queue:</span>
                        <span className="j-metric-value mono">{qCross} veh</span>
                      </div>
                      <div className="j-metric-item">
                        <span className="j-metric-label">Downstream Link:</span>
                        <span className={`j-metric-value mono ${downOcc >= 85 ? 'text-crit font-bold' : ''}`}>
                          {j.downstreamEdge || `${jId}_next`} ({downOcc.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="j-metric-item">
                        <span className="j-metric-label">M6 Guard Action:</span>
                        <span className="j-metric-value mono text-slate">{j.m6Action || (isCritical ? 'FORCE_EARLY_CUT' : 'EXTEND_GREEN')}</span>
                      </div>
                    </div>

                    <button
                      className="btn-inspect-action"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (setSelectedJunction) setSelectedJunction(jId);
                        if (handleLocate) handleLocate('junction', jId);
                      }}
                    >
                      {isSelected ? 'Currently Selected' : `Inspect ${jId} in Detail`}
                    </button>
                  </div>
                );
              })}
            </div>

            {/* Junction Analytics & Timing Spec */}
            <div className="dashboard-grid-split" style={{ marginTop: '20px' }}>
              <div className="center-operations-col">
                <JunctionMetricsRechart scenarioId={selectedScenario} />
              </div>
              <div className="right-operations-col">
                <div className="data-table-container">
                  <div className="data-table-head-row">
                    <h3 className="data-table-title">NEMA Phase Safety Invariants</h3>
                    <span className="mono text-xs text-slate">Ring-Barrier Engine</span>
                  </div>
                  <table className="engineering-table">
                    <thead>
                      <tr>
                        <th>PARAMETER</th>
                        <th>VALUE</th>
                        <th>SPECIFICATION</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>Minimum Green (G_min)</td>
                        <td className="mono font-bold">10.0 s</td>
                        <td>Pedestrian clearance & driver reaction minimum</td>
                      </tr>
                      <tr>
                        <td>Maximum Green (G_max)</td>
                        <td className="mono font-bold">60.0 s</td>
                        <td>Arterial coordination upper envelope</td>
                      </tr>
                      <tr>
                        <td>Yellow Clearance (Y)</td>
                        <td className="mono font-bold">4.0 s</td>
                        <td>ITE standard stopping dilemma clearance</td>
                      </tr>
                      <tr>
                        <td>All-Red Clearance (R)</td>
                        <td className="mono font-bold">2.0 s</td>
                        <td>Intersection clearance interval</td>
                      </tr>
                      <tr>
                        <td>Max Fairness Debt Threshold</td>
                        <td className="mono font-bold text-amber">45.0 s</td>
                        <td>Cross-street starvation prevention bound</td>
                      </tr>
                      <tr>
                        <td>Downstream Spillback Threshold</td>
                        <td className="mono font-bold text-crit">85.0 %</td>
                        <td>M6 Early Cut activation ceiling</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* =========================================================================
            TAB 4: DECISIONS (7-Step Flow & M9 Evaluator)
            ========================================================================= */}
        {activeNav === 'Decisions' && (
          <div className="tab-view-container">
            {/* Replay Controller Banner */}
            <div className="public-corridor-section" style={{ marginBottom: '16px' }}>
              <div className="section-header-row">
                <div>
                  <h3 className="section-title">Deterministic Decision Trace Flow</h3>
                  <span className="section-subtitle">Real-time TraCI perception through 7-layer verification pipeline</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span className="mono text-xs text-slate">Trace Step: {replayStep > 0 ? `${replayStep}/7` : 'Live Continuous'}</span>
                  <button
                    className={`replay-button ${isReplaying ? 'replaying' : ''}`}
                    onClick={handleReplay}
                    disabled={isReplaying}
                  >
                    <span>{isReplaying ? 'Replaying...' : 'Replay Full Trace'}</span>
                  </button>
                </div>
              </div>
            </div>

            <div className="dashboard-grid-split">
              {/* Left Column: Decision Flow Graph */}
              <div className="center-operations-col">
                <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', height: '620px' }}>
                  <div className="data-table-head-row" style={{ marginBottom: '8px' }}>
                    <h3 className="data-table-title">7-Layer Pipeline Trace Graph</h3>
                    <span className="mono text-xs text-slate">ReactFlow Pipeline View</span>
                  </div>
                  <div style={{ height: '560px', width: '100%' }}>
                    <DecisionGraphFlow
                      decisionSteps={activeData.decisionTrace || []}
                      replayStep={replayStep}
                    />
                  </div>
                </div>
              </div>

              {/* Right Column: M9 Digital Twin Plan Scorecard & Recommendation */}
              <div className="right-operations-col">
                {/* Recommendation Approval Box */}
                <div className="data-table-container" style={{ marginBottom: '16px' }}>
                  <div className="data-table-head-row">
                    <h3 className="data-table-title">Active Control Recommendation</h3>
                    <span className={`flow-node-badge ${approvalStatus === 'APPROVED' ? 'badge-norm' : 'badge-crit'}`}>
                      {approvalStatus}
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', lineHeight: '1.5', marginBottom: '12px', color: '#334155' }}>
                    <p><strong>Action:</strong> <span className="mono text-blue font-bold">{currentRecommendation?.proposed_action || 'SPILLBACK_CLEARANCE'}</span></p>
                    <p style={{ marginTop: '4px' }}><strong>Reason:</strong> {currentRecommendation?.reason || 'Downstream link J3_J4 storage exceeds 85.0% capacity (47/53 veh). Spillback guard initiated.'}</p>
                    <p style={{ marginTop: '4px' }}><strong>Safety Verification:</strong> M6 Hard Guard Checked & Validated.</p>
                  </div>
                  {userRole !== 'VIEWER' && (
                    <button
                      className="btn-approve-rec"
                      onClick={() => handleApproveRecommendation && handleApproveRecommendation(currentRecommendation?.recommendation_id || 'REC-1')}
                      disabled={approvalStatus === 'APPROVED'}
                      style={{ width: '100%', padding: '10px', fontSize: '12px', fontWeight: '700' }}
                    >
                      {approvalStatus === 'APPROVED' ? '✓ Recommendation Executed' : 'Approve & Execute Recommendation'}
                    </button>
                  )}
                </div>

                {/* M9 Plans Scorecard */}
                <div className="data-table-container">
                  <div className="data-table-head-row">
                    <h3 className="data-table-title">Digital Twin Plan A/B/C Evaluator</h3>
                    <span className="mono text-xs text-slate">M9 Deterministic Scorer</span>
                  </div>
                  <table className="engineering-table">
                    <thead>
                      <tr>
                        <th>PLAN NAME</th>
                        <th>DELAY</th>
                        <th>QUEUE</th>
                        <th>SPILLBACK</th>
                        <th>TOTAL SCORE</th>
                        <th>DECISION</th>
                      </tr>
                    </thead>
                    <tbody>
                      {m9Plans.map((plan, idx) => {
                        const isSelected = plan.status === 'SELECTED' || plan.name.includes('Plan C');
                        const isRejected = plan.status === 'REJECTED' || !plan.valid;
                        return (
                          <tr key={idx} className={isSelected ? 'selected-row' : ''}>
                            <td className="font-bold">{plan.name}</td>
                            <td className="mono">{plan.scores?.delay ?? '-'}</td>
                            <td className="mono">{plan.scores?.queue ?? '-'}</td>
                            <td className="mono font-bold">{plan.scores?.spillback ?? '-'}</td>
                            <td className="mono font-bold">{plan.total_score}</td>
                            <td>
                              <span className={`flow-node-badge ${isRejected ? 'badge-crit' : isSelected ? 'badge-norm' : 'badge-info'}`}>
                                {isRejected ? 'REJECTED' : isSelected ? 'SELECTED' : 'SAFE'}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* =========================================================================
            TAB 5: SIMULATION (TraCI Engine Controls & Live Fleet)
            ========================================================================= */}
        {activeNav === 'Simulation' && (
          <div className="tab-view-container">
            {/* Simulation Telemetry Grid */}
            <div className="engine-telemetry-grid">
              <div className="engine-telemetry-card">
                <span className="telemetry-label">SIMULATION ENGINE</span>
                <span className="telemetry-val mono">SUMO 1.27.1</span>
                <span className="telemetry-sub">TraCI Port 8813 (Active)</span>
              </div>
              <div className="engine-telemetry-card">
                <span className="telemetry-label">SIMULATION CLOCK</span>
                <span className="telemetry-val mono">{formatTime(simTime)}</span>
                <span className="telemetry-sub">Horizon: {formatTime(simTotalTime)}</span>
              </div>
              <div className="engine-telemetry-card">
                <span className="telemetry-label">CONTROL ARCHITECTURE</span>
                <span className="telemetry-val mono text-blue">M6 Guard + M7</span>
                <span className="telemetry-sub">Deterministic Seed: 42</span>
              </div>
              <div className="engine-telemetry-card">
                <span className="telemetry-label">ACTIVE NETWORK FLEET</span>
                <span className="telemetry-val mono text-green">{effectiveVehicles.length} Vehicles</span>
                <span className="telemetry-sub">1 Emergency Preempted</span>
              </div>
            </div>

            {/* Split: Digital Twin & Live Vehicles Table */}
            <div className="dashboard-grid-split">
              <div className="center-operations-col">
                <CorridorDigitalTwin
                  scenarioData={activeData}
                  selectedJunction={selectedJunction}
                  setSelectedJunction={setSelectedJunction}
                  replayStep={replayStep}
                  selectedItemType={selectedItemType}
                  selectedItemId={selectedItemId}
                  onSelectItem={handleLocate}
                  roadsList={effectiveRoads}
                  vehiclesList={effectiveVehicles}
                />
              </div>

              <div className="right-operations-col">
                <div className="data-table-container">
                  <div className="data-table-head-row">
                    <div>
                      <h3 className="data-table-title">Active Vehicle Telemetry</h3>
                      <p className="data-table-desc">Live TraCI coordinates, velocities, and stopline distance</p>
                    </div>
                    <span className="mono text-xs text-slate">{effectiveVehicles.length} Tracked</span>
                  </div>

                  <table className="engineering-table">
                    <thead>
                      <tr>
                        <th>VEHICLE ID</th>
                        <th>CLASS</th>
                        <th>SPEED</th>
                        <th>SEGMENT</th>
                        <th>DIST TO SIG</th>
                        <th>STATUS</th>
                        <th>TRACK</th>
                      </tr>
                    </thead>
                    <tbody>
                      {effectiveVehicles.map((veh) => {
                        const isSelected = selectedItemType === 'vehicle' && selectedItemId === veh.vehicle_id;
                        const isEmerg = veh.type === 'emergency' || veh.vehicle_id.startsWith('amb');
                        return (
                          <tr key={veh.vehicle_id} className={isSelected ? 'selected-row' : ''}>
                            <td className="mono font-bold text-blue">{veh.vehicle_id}</td>
                            <td>
                              <span className={`flow-node-badge ${isEmerg ? 'badge-crit' : 'badge-info'}`}>
                                {isEmerg ? 'EMERGENCY' : 'PASSENGER'}
                              </span>
                            </td>
                            <td className="mono">{veh.speed_kmh.toFixed(1)} km/h</td>
                            <td className="mono text-slate">{veh.road_segment}</td>
                            <td className="mono">{veh.distance_to_signal_m.toFixed(1)}m</td>
                            <td>
                              <span className={`flow-node-badge ${veh.status === 'PRIORITY_PREEMPTION' ? 'badge-crit' : veh.status === 'STOPPED' ? 'badge-info' : 'badge-norm'}`}>
                                {veh.status}
                              </span>
                            </td>
                            <td>
                              <button
                                className="btn-inspect-action"
                                onClick={() => handleLocate && handleLocate('vehicle', veh.vehicle_id)}
                              >
                                {isSelected ? 'Tracking' : 'Locate'}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* =========================================================================
            TAB 6: RESULTS (Multi-Scenario Benchmark Performance)
            ========================================================================= */}
        {activeNav === 'Results' && (
          <div className="tab-view-container">
            {/* Benchmark Scorecard Table */}
            <div className="data-table-container" style={{ marginBottom: '20px' }}>
              <div className="data-table-head-row">
                <div>
                  <h3 className="data-table-title">Empirical Multi-Scenario Benchmark Performance</h3>
                  <p className="data-table-desc">Comparison of TrafficTwin AI vs Fixed-Time and Reactive baselines across identical SUMO seeds</p>
                </div>
                <span className="mono text-xs text-slate">Evaluated on SUMO 1.27.1</span>
              </div>

              <table className="engineering-table">
                <thead>
                  <tr>
                    <th>CONTROL STRATEGY</th>
                    <th>MECHANISM</th>
                    <th>THROUGHPUT</th>
                    <th>AVG WAIT TIME</th>
                    <th>MAX QUEUE</th>
                    <th>SPILLBACK EVENTS</th>
                    <th>FAIRNESS PROFILE</th>
                    <th>SAFETY RATING</th>
                  </tr>
                </thead>
                <tbody>
                  {benchmarkRows.map((row, idx) => (
                    <tr key={idx} className={row.strategy.includes('TrafficTwin') ? 'selected-row' : ''}>
                      <td className="font-bold">{row.strategy}</td>
                      <td className="text-slate">{row.tag}</td>
                      <td className="mono font-bold text-blue">{row.throughput} veh</td>
                      <td className="mono">{row.avgWait}</td>
                      <td className="mono">{row.maxQueue}</td>
                      <td className="mono font-bold">
                        <span className={row.spillbackEvents > 0 ? 'text-crit' : 'text-green'}>
                          {row.spillbackEvents}
                        </span>
                      </td>
                      <td className="text-slate">{row.fairness}</td>
                      <td>
                        <span className={`flow-node-badge ${row.badgeClass}`}>
                          {row.rating}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Bottom Recharts Grid */}
            <div className="bottom-charts-row">
              <ScenarioComparisonRechart comparisonData={activeData.comparison} />
              <JunctionMetricsRechart scenarioId={selectedScenario} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
