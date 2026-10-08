import React from 'react';

export default function CorridorSchematic({
  scenarioData,
  selectedJunction,
  setSelectedJunction,
  replayStep,
}) {
  const junctions = ['J1', 'J2', 'J3', 'J4'];

  const links = [
    { id: 'W0_J1', from: 'W0', to: 'J1', len: '200m', occ: 18.0, vehs: 9, cap: 53, risk: 'NORMAL' },
    {
      id: 'J1_J2',
      from: 'J1',
      to: 'J2',
      len: '200m',
      occ: scenarioData.junctions.J1.downstreamOcc,
      vehs: scenarioData.junctions.J1.downstreamVehs,
      cap: scenarioData.junctions.J1.downstreamCap,
      risk: scenarioData.junctions.J1.risk,
    },
    {
      id: 'J2_J3',
      from: 'J2',
      to: 'J3',
      len: '200m',
      occ: scenarioData.junctions.J2.downstreamOcc,
      vehs: scenarioData.junctions.J2.downstreamVehs,
      cap: scenarioData.junctions.J2.downstreamCap,
      risk: scenarioData.junctions.J2.risk,
    },
    {
      id: 'J3_J4',
      from: 'J3',
      to: 'J4',
      len: '200m',
      occ: scenarioData.junctions.J3.downstreamOcc,
      vehs: scenarioData.junctions.J3.downstreamVehs,
      cap: scenarioData.junctions.J3.downstreamCap,
      risk: scenarioData.junctions.J3.risk,
      isBottleneckLink: scenarioData.id === 'blocked_downstream',
    },
    {
      id: 'J4_E5',
      from: 'J4',
      to: 'E5',
      len: '200m',
      occ: scenarioData.junctions.J4.downstreamOcc,
      vehs: scenarioData.junctions.J4.downstreamVehs,
      cap: scenarioData.junctions.J4.downstreamCap,
      risk: scenarioData.junctions.J4.risk,
      hasIncident: scenarioData.id === 'blocked_downstream',
    },
  ];

  return (
    <div className="corridor-hero-container">
      {/* Engineering Header / Ruler Bar */}
      <div className="corridor-meta-bar">
        <div className="corridor-meta-left">
          <span className="section-title">CORRIDOR SCHEMATIC</span>
          <span className="corridor-axis-label mono">EAST-WEST ARTERIAL // 1,000m DUAL-CARRIAGEWAY (2 LANES / DIR)</span>
        </div>
        <div className="corridor-meta-right">
          <span className="flow-badge">
            PRIMARY ARTERIAL FLOW <span className="flow-arrow">→ → →</span> EASTBOUND
          </span>
          <span className="legend-chip normal">NORMAL (&lt;75%)</span>
          <span className="legend-chip warning">WARNING (75-85%)</span>
          <span className="legend-chip critical">CRITICAL (&gt;85%)</span>
        </div>
      </div>

      {/* SVG Engineering Schematic */}
      <div className="corridor-viewport">
        <svg
          viewBox="0 0 1100 240"
          className="corridor-svg"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            {/* Critical Link Hazard Hatch Pattern */}
            <pattern id="hazardHatch" width="10" height="10" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="10" stroke="#D85C55" strokeWidth="2.5" strokeOpacity="0.45" />
            </pattern>
            {/* Warning Hatch */}
            <pattern id="warningHatch" width="10" height="10" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="10" stroke="#D7A640" strokeWidth="2.5" strokeOpacity="0.35" />
            </pattern>
          </defs>

          {/* Background grid guides */}
          <line x1="40" y1="120" x2="1060" y2="120" stroke="#1E272D" strokeWidth="1" strokeDasharray="3 3" />

          {/* Distance Ruler */}
          <g className="ruler-group" opacity="0.7">
            <text x="60" y="24" className="ruler-text mono">W0 [0m]</text>
            <text x="270" y="24" className="ruler-text mono">J1 [200m]</text>
            <text x="500" y="24" className="ruler-text mono">J2 [400m]</text>
            <text x="730" y="24" className="ruler-text mono">J3 [600m]</text>
            <text x="960" y="24" className="ruler-text mono">J4 [800m]</text>
            <text x="1045" y="24" className="ruler-text mono">E5 [1000m]</text>
            <line x1="60" y1="30" x2="1060" y2="30" stroke="#283238" strokeWidth="1" />
            <circle cx="60" cy="30" r="2.5" fill="#69757A" />
            <circle cx="270" cy="30" r="2.5" fill="#69757A" />
            <circle cx="500" cy="30" r="2.5" fill="#69757A" />
            <circle cx="730" cy="30" r="2.5" fill="#69757A" />
            <circle cx="960" cy="30" r="2.5" fill="#69757A" />
            <circle cx="1060" cy="30" r="2.5" fill="#69757A" />
          </g>

          {/* Perpendicular Cross Streets */}
          {[270, 500, 730, 960].map((x, idx) => (
            <g key={`cross-${idx}`} className="cross-street">
              {/* North side */}
              <rect x={x - 16} y="42" width="32" height="42" fill="#151C20" stroke="#283238" strokeWidth="1" />
              <line x1={x} y1="42" x2={x} y2="84" stroke="#283238" strokeWidth="1" strokeDasharray="3 2" />
              <text x={x} y="38" textAnchor="middle" className="cross-label mono">N{idx + 1}</text>
              {/* South side */}
              <rect x={x - 16} y="156" width="32" height="42" fill="#151C20" stroke="#283238" strokeWidth="1" />
              <line x1={x} y1="156" x2={x} y2="198" stroke="#283238" strokeWidth="1" strokeDasharray="3 2" />
              <text x={x} y="210" textAnchor="middle" className="cross-label mono">S{idx + 1}</text>
            </g>
          ))}

          {/* Main Arterial Roadway Structure */}
          {/* Outer road boundary */}
          <rect x="50" y="84" width="1010" height="72" fill="#11171B" stroke="#283238" strokeWidth="1.5" rx="3" />

          {/* Directional Divider (Center) */}
          <line x1="50" y1="120" x2="1060" y2="120" stroke="#3A474F" strokeWidth="1.5" strokeDasharray="8 6" />

          {/* Lane Sub-dividers (Eastbound Top Lane, Westbound Bottom Lane) */}
          <line x1="50" y1="102" x2="1060" y2="102" stroke="#1E272D" strokeWidth="1" strokeDasharray="4 4" />
          <line x1="50" y1="138" x2="1060" y2="138" stroke="#1E272D" strokeWidth="1" strokeDasharray="4 4" />

          {/* Direction Labels */}
          <text x="56" y="96" className="lane-dir-label mono">EB L1</text>
          <text x="56" y="114" className="lane-dir-label mono">EB L0</text>
          <text x="56" y="132" className="lane-dir-label mono">WB L0</text>
          <text x="56" y="150" className="lane-dir-label mono">WB L1</text>

          {/* Link Segments Between Junctions */}
          {/* Segment J1_J2: x = 290 to 480 */}
          {/* Segment J2_J3: x = 520 to 710 */}
          {/* Segment J3_J4: x = 750 to 940 (CRITICAL BOTTLENECK LINK) */}
          {/* Segment J4_E5: x = 980 to 1050 */}

          {/* Highlight link J3_J4 in Blocked scenario */}
          {scenarioData.id === 'blocked_downstream' && (
            <g className="bottleneck-highlight">
              <rect
                x="750"
                y="85"
                width="190"
                height="34"
                fill="url(#hazardHatch)"
                stroke="#D85C55"
                strokeWidth="1.5"
                opacity="0.9"
              />
              <rect x="750" y="85" width="190" height="34" fill="rgba(216, 92, 85, 0.15)" />
            </g>
          )}

          {/* Incident on J4_E5 in Blocked scenario */}
          {scenarioData.id === 'blocked_downstream' && (
            <g className="incident-marker">
              <rect x="1000" y="87" width="16" height="12" fill="#D85C55" rx="2" />
              <text x="1008" y="96" textAnchor="middle" fill="#FFFFFF" fontSize="8" fontWeight="bold">X</text>
              <rect x="1020" y="103" width="16" height="12" fill="#D85C55" rx="2" />
              <text x="1028" y="112" textAnchor="middle" fill="#FFFFFF" fontSize="8" fontWeight="bold">X</text>
              <text x="1020" y="76" textAnchor="middle" className="incident-label mono" fill="#D85C55">
                INCIDENT (STOP 280s)
              </text>
            </g>
          )}

          {/* Restrained Vehicle Queues on Eastbound Arterial (Physical markers) */}
          {/* J1 Approach Queue (3 vehs) */}
          <rect x="230" y="89" width="10" height="8" fill="#4FA9C8" rx="1" />
          <rect x="244" y="89" width="10" height="8" fill="#4FA9C8" rx="1" />
          <rect x="238" y="105" width="10" height="8" fill="#4FA9C8" rx="1" />

          {/* J2 Approach Queue (4 vehs) */}
          <rect x="445" y="89" width="10" height="8" fill="#4FA9C8" rx="1" />
          <rect x="460" y="89" width="10" height="8" fill="#4FA9C8" rx="1" />
          <rect x="475" y="89" width="10" height="8" fill="#4FA9C8" rx="1" />
          <rect x="470" y="105" width="10" height="8" fill="#4FA9C8" rx="1" />

          {/* J3 Approach Queue (12 vehs queued on main arterial) */}
          {scenarioData.id === 'blocked_downstream' && (
            <g className="j3-approach-queue">
              <rect x="625" y="89" width="9" height="7" fill="#4FA9C8" rx="1" />
              <rect x="637" y="89" width="9" height="7" fill="#4FA9C8" rx="1" />
              <rect x="649" y="89" width="9" height="7" fill="#4FA9C8" rx="1" />
              <rect x="661" y="89" width="9" height="7" fill="#4FA9C8" rx="1" />
              <rect x="673" y="89" width="9" height="7" fill="#4FA9C8" rx="1" />
              <rect x="685" y="89" width="9" height="7" fill="#4FA9C8" rx="1" />
              <rect x="697" y="89" width="9" height="7" fill="#4FA9C8" rx="1" />
              <rect x="655" y="105" width="9" height="7" fill="#4FA9C8" rx="1" />
              <rect x="667" y="105" width="9" height="7" fill="#4FA9C8" rx="1" />
              <rect x="679" y="105" width="9" height="7" fill="#4FA9C8" rx="1" />
              <rect x="691" y="105" width="9" height="7" fill="#4FA9C8" rx="1" />
              <rect x="703" y="105" width="9" height="7" fill="#4FA9C8" rx="1" />
              <text x="665" y="78" textAnchor="middle" className="queue-tag-text mono" fill="#4FA9C8">
                J3 QUEUE: 12 VEH
              </text>
            </g>
          )}

          {/* J3 -> J4 Link Saturated Queue (47 vehicles packed on link) */}
          {scenarioData.id === 'blocked_downstream' && (
            <g className="link-saturated-queue">
              {[755, 770, 785, 800, 815, 830, 845, 860, 875, 890, 905, 920, 935].map((vx, i) => (
                <React.Fragment key={`sat-${i}`}>
                  <rect x={vx} y="89" width="11" height="8" fill="#D85C55" rx="1" opacity="0.9" />
                  <rect x={vx - 5} y="105" width="11" height="8" fill="#D85C55" rx="1" opacity="0.9" />
                </React.Fragment>
              ))}
            </g>
          )}

          {/* Link Data Annotations (Occupancy & Vehicles) */}
          {/* Link W0_J1 */}
          <g transform="translate(130, 175)" className="link-annotation">
            <rect x="-35" y="-12" width="70" height="20" fill="#151C20" stroke="#283238" rx="2" />
            <text x="0" y="2" textAnchor="middle" className="link-data-text mono">18% | 9/53</text>
          </g>

          {/* Link J1_J2 */}
          <g transform="translate(385, 175)" className="link-annotation">
            <rect x="-45" y="-12" width="90" height="20" fill="#151C20" stroke="#283238" rx="2" />
            <text x="0" y="2" textAnchor="middle" className="link-data-text mono">
              {scenarioData.junctions.J1.downstreamOcc}% | {scenarioData.junctions.J1.downstreamVehs}/53
            </text>
          </g>

          {/* Link J2_J3 */}
          <g transform="translate(615, 175)" className="link-annotation">
            <rect x="-45" y="-12" width="90" height="20" fill="#151C20" stroke="#283238" rx="2" />
            <text x="0" y="2" textAnchor="middle" className="link-data-text mono">
              {scenarioData.junctions.J2.downstreamOcc}% | {scenarioData.junctions.J2.downstreamVehs}/53
            </text>
          </g>

          {/* Link J3_J4 (THE CRITICAL FOCUS) */}
          <g transform="translate(845, 175)" className="link-annotation">
            <rect
              x="-60"
              y="-14"
              width="120"
              height="24"
              fill={scenarioData.junctions.J3.risk === 'CRITICAL' ? '#241416' : '#151C20'}
              stroke={scenarioData.junctions.J3.risk === 'CRITICAL' ? '#D85C55' : '#283238'}
              strokeWidth={scenarioData.junctions.J3.risk === 'CRITICAL' ? 1.5 : 1}
              rx="3"
            />
            <text
              x="0"
              y="2"
              textAnchor="middle"
              className="link-data-text mono"
              fill={scenarioData.junctions.J3.risk === 'CRITICAL' ? '#D85C55' : '#A7B0B4'}
              fontWeight="bold"
            >
              J3_J4: {scenarioData.junctions.J3.downstreamOcc}% [CRITICAL]
            </text>
          </g>

          {/* Corridor Junction Nodes (J1, J2, J3, J4) */}
          {[
            { id: 'J1', x: 270, j: scenarioData.junctions.J1 },
            { id: 'J2', x: 500, j: scenarioData.junctions.J2 },
            { id: 'J3', x: 730, j: scenarioData.junctions.J3 },
            { id: 'J4', x: 960, j: scenarioData.junctions.J4 },
          ].map(({ id, x, j }) => {
            const isSelected = selectedJunction === id;
            const isCritical = j.risk === 'CRITICAL';
            const isSpillbackTarget = id === 'J3' && scenarioData.id === 'blocked_downstream';

            // Signal Color:
            // J3 at step 6 transitions to yellow (phase 1)
            let signalColor = '#4FB286'; // Green
            if (id === 'J4') signalColor = '#D7A640'; // Yellow
            if (id === 'J3' && replayStep >= 6) signalColor = '#D7A640'; // Transitioned to yellow

            return (
              <g
                key={id}
                className={`junction-node-group ${isSelected ? 'selected' : ''}`}
                onClick={() => setSelectedJunction(id)}
                style={{ cursor: 'pointer' }}
              >
                {/* Selection Ring */}
                {isSelected && (
                  <rect
                    x={x - 28}
                    y="74"
                    width="56"
                    height="92"
                    fill="none"
                    stroke="#4FA9C8"
                    strokeWidth="2"
                    strokeDasharray="4 2"
                    rx="4"
                  />
                )}

                {/* Junction Box */}
                <rect
                  x={x - 22}
                  y="80"
                  width="44"
                  height="80"
                  fill="#151C20"
                  stroke={isSpillbackTarget ? '#D85C55' : isSelected ? '#4FA9C8' : '#283238'}
                  strokeWidth={isSpillbackTarget || isSelected ? 2 : 1}
                  rx="3"
                />

                {/* Node Label */}
                <text x={x} y="98" textAnchor="middle" className="node-id-text mono">
                  {id}
                </text>

                {/* Signal Aspect Indicator */}
                <circle cx={x} cy="114" r="6" fill={signalColor} />
                <circle cx={x} cy="114" r="8" fill="none" stroke={signalColor} strokeWidth="1" opacity="0.4" />

                {/* Phase Number */}
                <text x={x} y="134" textAnchor="middle" className="node-phase-text mono">
                  {id === 'J3' && replayStep >= 6 ? 'P: 1' : `P: ${j.phase}`}
                </text>

                {/* Status indicator tag */}
                <rect
                  x={x - 18}
                  y="142"
                  width="36"
                  height="12"
                  fill={isCritical ? 'rgba(216,92,85,0.2)' : 'rgba(79,178,134,0.1)'}
                  stroke={isCritical ? '#D85C55' : '#4FB286'}
                  strokeWidth="0.5"
                  rx="2"
                />
                <text
                  x={x}
                  y="151"
                  textAnchor="middle"
                  fontSize="7"
                  fontWeight="bold"
                  fill={isCritical ? '#D85C55' : '#4FB286'}
                >
                  {isCritical ? 'CRIT' : 'OK'}
                </text>
              </g>
            );
          })}

          {/* West Entry Marker */}
          <g transform="translate(60, 120)">
            <rect x="-15" y="-18" width="30" height="36" fill="#151C20" stroke="#283238" rx="2" />
            <text x="0" y="3" textAnchor="middle" className="entry-exit-text mono">W0</text>
            <text x="0" y="28" textAnchor="middle" className="entry-exit-sub mono">ENTRY</text>
          </g>

          {/* East Exit Marker */}
          <g transform="translate(1055, 120)">
            <rect x="-15" y="-18" width="30" height="36" fill="#151C20" stroke="#283238" rx="2" />
            <text x="0" y="3" textAnchor="middle" className="entry-exit-text mono">E5</text>
            <text x="0" y="28" textAnchor="middle" className="entry-exit-sub mono">EXIT</text>
          </g>
        </svg>
      </div>

      {/* Schematic Footer / Operational Status Bar */}
      <div className="corridor-status-strip">
        <div className="strip-item">
          <span className="strip-label">NETWORK:</span>
          <span className="strip-val mono">4-JUNCTION ARTERIAL (J1, J2, J3, J4)</span>
        </div>
        <div className="strip-item">
          <span className="strip-label">ACTIVE BOTTLENECK:</span>
          <span className="strip-val mono highlight-crit">
            {scenarioData.id === 'blocked_downstream' ? 'J3 → J4 LINK (88.7% CAPACITY)' : 'NONE (NORMAL SINK FLOW)'}
          </span>
        </div>
        <div className="strip-item">
          <span className="strip-label">SELECTED INTERSECTION:</span>
          <span className="strip-val mono highlight-active">{selectedJunction} (CLICK TO INSPECT)</span>
        </div>
      </div>
    </div>
  );
}
