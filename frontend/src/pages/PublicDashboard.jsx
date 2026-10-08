import React from 'react';

export default function PublicDashboard({
  selectedScenario,
  setSelectedScenario,
  selectedJunction,
  setSelectedJunction,
  activeData,
  corridorState,
  connectionStatus,
  isBackendConnected,
  onSwitchToOperator,
}) {
  // Junction data lookup with real fallback
  const getJunctionInfo = (jid) => {
    const raw = corridorState?.[jid] || activeData.junctions?.[jid] || {};
    const qMain = raw.queue_main ?? raw.queueMain ?? 0;
    const qCross = raw.queue_cross ?? raw.queueCross ?? 0;
    const occ = raw.occupancy ?? raw.downstreamOcc ?? 0;
    const phase = raw.current_phase ?? raw.phase ?? 0;
    const elapsed = raw.elapsed_green_s ?? raw.elapsedGreen ?? 10.0;
    const risk = raw.spillback_risk ?? raw.risk ?? 'NORMAL';

    // Public signal state derivation
    let signal = 'GREEN';
    let nextSignal = 'YELLOW';
    let remainingSec = 15;

    if (phase === 0) {
      signal = 'GREEN';
      nextSignal = 'YELLOW';
      remainingSec = Math.max(2, Math.round(30 - elapsed));
    } else if (phase === 1) {
      signal = 'YELLOW';
      nextSignal = 'RED';
      remainingSec = Math.max(1, Math.round(3 - (elapsed % 3)));
    } else if (phase === 3) {
      signal = 'RED'; // Red for main arterial while cross street is green
      nextSignal = 'GREEN';
      remainingSec = Math.max(2, Math.round(20 - elapsed));
    } else if (phase === 4) {
      signal = 'RED';
      nextSignal = 'GREEN';
      remainingSec = 2;
    } else {
      signal = 'RED';
      nextSignal = 'GREEN';
      remainingSec = 2;
    }

    // Traffic condition
    let trafficLevel = 'Normal Flow';
    let trafficClass = 'status-green';
    if (risk === 'CRITICAL' || occ >= 85 || qMain >= 10) {
      trafficLevel = 'Heavy Congestion';
      trafficClass = 'status-red';
    } else if (risk === 'WARNING' || occ >= 65 || qMain >= 5) {
      trafficLevel = 'Moderate Traffic';
      trafficClass = 'status-amber';
    }

    // Public advisory note
    let advisory = 'Normal arterial progression.';
    if (jid === 'J3' && (selectedScenario === 'blocked_downstream' || risk === 'CRITICAL')) {
      advisory = 'Downstream bottleneck. Signal managed to prevent gridlock.';
    } else if (jid === 'J2' && selectedScenario === 'ambulance') {
      advisory = 'Emergency vehicle approach. Priority clearance active.';
    } else if (qMain >= 10) {
      advisory = 'High approach queue. Green cycle active.';
    }

    return {
      id: jid,
      name: raw.name || `Junction ${jid.slice(1)}`,
      crossStreet: raw.cross_street || raw.crossStreet || 'Cross Street',
      location: jid === 'J1' ? 'West Entry (200m)' : jid === 'J2' ? 'Mid-West (400m)' : jid === 'J3' ? 'Mid-East (600m)' : 'East Exit (800m)',
      qMain,
      qCross,
      occ,
      phase,
      signal,
      nextSignal,
      remainingSec,
      trafficLevel,
      trafficClass,
      advisory,
      risk,
    };
  };

  const junctions = ['J1', 'J2', 'J3', 'J4'].map(getJunctionInfo);
  const activeJunctionInfo = junctions.find((j) => j.id === selectedJunction) || junctions[0];

  // Active public alert configuration based on scenario & real state
  const getPublicAlert = () => {
    if (selectedScenario === 'blocked_downstream') {
      return {
        type: 'TRAFFIC ALERT',
        severity: 'alert-critical',
        title: 'Downstream Congestion Advisory',
        message: 'Heavy congestion detected near Junction J3 toward East Exit. Traffic signals are actively coordinated to clear downstream bottlenecks and protect arterial flow.',
      };
    }
    if (selectedScenario === 'ambulance') {
      return {
        type: 'EMERGENCY IN TRANSIT',
        severity: 'alert-priority',
        title: 'Emergency Vehicle Priority Active',
        message: 'Emergency priority vehicle detected entering the corridor near J1_J2. Traffic signals are dynamically adjusted to ensure safe, unobstructed passage.',
      };
    }
    if (selectedScenario === 'rush') {
      return {
        type: 'TRAFFIC ADVISORY',
        severity: 'alert-warning',
        title: 'Peak Volume In Progress',
        message: 'Elevated traffic volumes along the East-West arterial corridor. Expect moderate waiting times on cross streets. Coordinated signal timing active.',
      };
    }
    return {
      type: 'NORMAL CONDITIONS',
      severity: 'alert-normal',
      title: 'Normal Traffic Operations',
      message: 'All corridor intersections are operating within standard parameters. No significant delays or bottlenecks detected along the corridor.',
    };
  };

  const alert = getPublicAlert();

  return (
    <div className="public-dashboard-container">
      {/* 1. PUBLIC HEADER */}
      <header className="public-header">
        <div className="public-header-brand">
          <div className="public-brand-title-row">
            <span className="public-brand-name">TrafficTwin</span>
            <span className="public-badge-citizen">PUBLIC TRAFFIC INFORMATION</span>
          </div>
          <p className="public-brand-subtitle">
            East-West Corridor Traffic & Signal Information
          </p>
        </div>

        <div className="public-header-controls">
          <div className="public-meta-item">
            <span className="meta-label">STATUS</span>
            <span className="meta-value mono">
              {isBackendConnected ? 'LIVE SIMULATION' : 'SIMULATION RUN'}
            </span>
          </div>

          <div className="public-meta-item">
            <span className="meta-label">SCENARIO</span>
            <select
              className="public-scenario-select mono"
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
            >
              <option value="blocked_downstream">Blocked Downstream</option>
              <option value="normal">Normal Arterial</option>
              <option value="rush">Peak Rush Hour</option>
              <option value="ambulance">Emergency Vehicle</option>
            </select>
          </div>

          {onSwitchToOperator && (
            <button
              className="btn-switch-operator mono"
              onClick={onSwitchToOperator}
              title="Open Operator Control Room"
            >
              Operator View →
            </button>
          )}
        </div>
      </header>

      {/* 2. PUBLIC ALERT BANNER */}
      <section className={`public-alert-banner ${alert.severity}`}>
        <div className="alert-type-tag mono">{alert.type}</div>
        <div className="alert-content">
          <strong className="alert-title">{alert.title}</strong>
          <p className="alert-body">{alert.message}</p>
        </div>
      </section>

      {/* 3. CORRIDOR OVERVIEW SCHEMATIC */}
      <section className="public-corridor-section">
        <div className="section-header-row">
          <h2 className="section-title">Corridor Overview</h2>
          <span className="section-subtitle mono">West Entry → J1 → J2 → J3 → J4 → East Exit</span>
        </div>

        <div className="public-corridor-flow">
          <div className="flow-boundary start">
            <span className="boundary-label">West Entry</span>
            <span className="boundary-sub">Arterial Inflow</span>
          </div>

          {junctions.map((j) => {
            const isSelected = j.id === selectedJunction;
            return (
              <div
                key={j.id}
                className={`public-junction-card ${isSelected ? 'selected' : ''}`}
                onClick={() => setSelectedJunction(j.id)}
              >
                <div className="card-top-row">
                  <span className="j-title mono">{j.id}</span>
                  <span className={`signal-lamp lamp-${j.signal.toLowerCase()}`}>
                    {j.signal}
                  </span>
                </div>

                <div className="j-timing-row">
                  <span className="time-remaining mono">{j.remainingSec}s</span>
                  <span className="time-sub">remaining</span>
                </div>

                <div className="j-queue-row">
                  <span className="queue-label">Queue:</span>
                  <span className="queue-val mono">{j.qMain} veh</span>
                </div>

                <div className="j-status-row">
                  <span className={`traffic-badge ${j.trafficClass}`}>
                    {j.trafficLevel}
                  </span>
                </div>

                <div className="j-next-row mono">
                  Next: {j.nextSignal}
                </div>
              </div>
            );
          })}

          <div className="flow-boundary end">
            <span className="boundary-label">East Exit</span>
            <span className="boundary-sub">Discharge</span>
          </div>
        </div>
      </section>

      {/* 4. SPLIT DETAILS: FOCUSED SIGNAL PANEL + TRAFFIC STATUS TABLE */}
      <div className="public-details-split">
        {/* Left Focus Box: Detailed Signal Status for Selected Junction */}
        <div className="public-signal-focus-box">
          <div className="focus-box-header">
            <span className="micro-label">INTERSECTION FOCUS</span>
            <h3 className="focus-title mono">{activeJunctionInfo.name} ({activeJunctionInfo.id})</h3>
            <span className="focus-location">{activeJunctionInfo.location} // Cross Street: {activeJunctionInfo.crossStreet}</span>
          </div>

          <div className="focus-signal-display">
            <div className={`signal-light-box light-${activeJunctionInfo.signal.toLowerCase()}`}>
              <div className="light-glow"></div>
              <span className="light-text mono">{activeJunctionInfo.signal}</span>
            </div>

            <div className="focus-countdown-col">
              <span className="countdown-number mono">{activeJunctionInfo.remainingSec}</span>
              <span className="countdown-label">Seconds Remaining</span>
              <div className="next-phase-indicator mono">
                Next Signal: <strong>{activeJunctionInfo.nextSignal}</strong>
              </div>
            </div>
          </div>

          <div className="focus-stats-list">
            <div className="focus-stat-item">
              <span className="stat-label">Main Approach Queue</span>
              <span className="stat-val mono">{activeJunctionInfo.qMain} vehicles</span>
            </div>
            <div className="focus-stat-item">
              <span className="stat-label">Cross Street Queue</span>
              <span className="stat-val mono">{activeJunctionInfo.qCross} vehicles</span>
            </div>
            <div className="focus-stat-item">
              <span className="stat-label">Downstream Link Occupancy</span>
              <span className="stat-val mono">{activeJunctionInfo.occ.toFixed(1)}%</span>
            </div>
            <div className="focus-stat-item">
              <span className="stat-label">Traffic Condition</span>
              <span className={`stat-val ${activeJunctionInfo.trafficClass} bold`}>
                {activeJunctionInfo.trafficLevel}
              </span>
            </div>
          </div>

          <div className="focus-advisory-box">
            <span className="adv-head">Traffic Advisory:</span>
            <p className="adv-body">{activeJunctionInfo.advisory}</p>
          </div>
        </div>

        {/* Right Table: Complete Corridor Intersections Table */}
        <div className="public-table-container">
          <div className="table-header-row">
            <h3 className="table-title">Intersection Status Table</h3>
            <span className="table-caption mono">Real-time simulation metrics</span>
          </div>

          <table className="public-traffic-table">
            <thead>
              <tr>
                <th>Junction</th>
                <th>Location</th>
                <th>Current Signal</th>
                <th>Time Left</th>
                <th>Next Signal</th>
                <th>Queue</th>
                <th>Condition</th>
              </tr>
            </thead>
            <tbody>
              {junctions.map((j) => (
                <tr
                  key={j.id}
                  className={j.id === selectedJunction ? 'row-active' : ''}
                  onClick={() => setSelectedJunction(j.id)}
                >
                  <td className="bold mono">{j.id}</td>
                  <td>{j.location}</td>
                  <td>
                    <span className={`table-signal-tag tag-${j.signal.toLowerCase()} mono`}>
                      {j.signal}
                    </span>
                  </td>
                  <td className="mono">{j.remainingSec}s</td>
                  <td className="mono text-muted">{j.nextSignal}</td>
                  <td className="mono">{j.qMain} veh</td>
                  <td>
                    <span className={`table-traffic-badge ${j.trafficClass}`}>
                      {j.trafficLevel}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Public Corridor Notice */}
          <div className="public-info-footer">
            <p className="info-text">
              Signal timings and queue measurements are updated dynamically from the Eclipse SUMO simulation model.
              Designed for public passenger and transit advisory services.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
