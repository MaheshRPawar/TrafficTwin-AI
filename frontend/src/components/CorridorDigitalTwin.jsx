import React, { useState, useRef, useEffect } from 'react';

export default function CorridorDigitalTwin({
  scenarioData,
  selectedJunction,
  setSelectedJunction,
  replayStep,
}) {
  const containerRef = useRef(null);
  const [rotate, setRotate] = useState({ x: 8, y: -2 });
  const [hoveredJunction, setHoveredJunction] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // Handle subtle cursor-based parallax
  const handleMouseMove = (e) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const xRel = (e.clientX - rect.left) / rect.width - 0.5; // -0.5 to 0.5
    const yRel = (e.clientY - rect.top) / rect.height - 0.5; // -0.5 to 0.5

    // Subtle restrained tilt (±5 degrees max)
    setRotate({
      x: 8 - yRel * 8,
      y: -2 + xRel * 10,
    });
  };

  const handleMouseLeave = () => {
    setRotate({ x: 8, y: -2 });
    setHoveredJunction(null);
  };

  const junctions = [
    { id: 'J1', x: 230, label: 'J1' },
    { id: 'J2', x: 440, label: 'J2' },
    { id: 'J3', x: 650, label: 'J3' },
    { id: 'J4', x: 860, label: 'J4' },
  ];

  const isBlocked = scenarioData.id === 'blocked_downstream';
  const isRush = scenarioData.id === 'rush';

  // Vehicles state for continuous animation
  const [animTick, setAnimTick] = useState(0);
  useEffect(() => {
    let frameId;
    const animate = () => {
      setAnimTick((t) => (t + 0.5) % 1000);
      frameId = requestAnimationFrame(animate);
    };
    frameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameId);
  }, []);

  return (
    <div
      className="twin-card"
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Top Header */}
      <div className="twin-header">
        <div className="twin-header-left">
          <div className="twin-icon-badge">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="12 2 2 7 12 12 22 7 12 2" />
              <polyline points="2 17 12 22 22 17" />
              <polyline points="2 12 12 17 22 12" />
            </svg>
          </div>
          <div>
            <h2 className="twin-title">Corridor Digital Twin</h2>
            <p className="twin-subtitle">West Entry → J1 → J2 → J3 → J4 → East Exit (1,000m Arterial)</p>
          </div>
        </div>

        <div className="twin-header-right">
          <span className="flow-direction-badge">
            FLOW: EASTBOUND <span className="direction-arrows">→ → →</span>
          </span>
          <span className="twin-status-chip">
            {isBlocked ? 'CONGESTION AT J3_J4' : 'NORMAL UNCONSTRAINED'}
          </span>
        </div>
      </div>

      {/* 3D Perspective Canvas Viewport */}
      <div className="twin-viewport-3d">
        <div
          className="twin-stage-3d"
          style={{
            transform: `perspective(1100px) rotateX(${rotate.x}deg) rotateY(${rotate.y}deg)`,
          }}
        >
          <svg viewBox="0 0 1080 250" className="twin-svg" preserveAspectRatio="xMidYMid meet">
            <defs>
              <filter id="shadow-3d" x="-10%" y="-10%" width="120%" height="130%">
                <feDropShadow dx="0" dy="6" stdDeviation="8" floodColor="#0f172a" floodOpacity="0.1" />
              </filter>
              <filter id="node-lift-shadow" x="-30%" y="-30%" width="160%" height="160%">
                <feDropShadow dx="0" dy="8" stdDeviation="6" floodColor="#2563eb" floodOpacity="0.25" />
              </filter>
              <linearGradient id="road-surface" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#334155" />
                <stop offset="50%" stopColor="#475569" />
                <stop offset="100%" stopColor="#334155" />
              </linearGradient>
              <pattern id="spillback-stripes" width="12" height="12" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                <line x1="0" y1="0" x2="0" y2="12" stroke="#ef4444" strokeWidth="3" strokeOpacity="0.4" />
              </pattern>
            </defs>

            {/* Ground Plane & Environment Details */}
            <rect x="10" y="20" width="1060" height="210" fill="#f8fafc" rx="12" stroke="#e2e8f0" strokeWidth="1" />
            
            {/* Subtle Distance Grid Guides */}
            <g opacity="0.6">
              {[80, 230, 440, 650, 860, 1000].map((gx, idx) => (
                <g key={`guide-${idx}`}>
                  <line x1={gx} y1="35" x2={gx} y2="215" stroke="#edf2f7" strokeWidth="1" strokeDasharray="3 3" />
                  <text x={gx} y="32" textAnchor="middle" fontSize="9" fill="#94a3b8" fontFamily="monospace">
                    {idx === 0 ? '0m' : `${idx * 200}m`}
                  </text>
                </g>
              ))}
            </g>

            {/* Perpendicular Cross Streets (N1-S1 to N4-S4) */}
            {junctions.map((j, idx) => (
              <g key={`cross-${idx}`}>
                <rect x={j.x - 22} y="45" width="44" height="160" fill="#475569" rx="4" />
                <line x1={j.x} y1="45" x2={j.x} y2="85" stroke="#f1f5f9" strokeWidth="1.5" strokeDasharray="6 4" />
                <line x1={j.x} y1="165" x2={j.x} y2="205" stroke="#f1f5f9" strokeWidth="1.5" strokeDasharray="6 4" />
                <text x={j.x} y="42" textAnchor="middle" fontSize="8" fill="#64748b" fontWeight="600">N{idx + 1}</text>
                <text x={j.x} y="218" textAnchor="middle" fontSize="8" fill="#64748b" fontWeight="600">S{idx + 1}</text>
              </g>
            ))}

            {/* Main Arterial Roadway (Dual-Carriageway, 4 Lanes) */}
            <g filter="url(#shadow-3d)">
              {/* Outer Curb */}
              <rect x="40" y="86" width="1000" height="78" fill="#cbd5e1" rx="6" />
              {/* Asphalt Road Bed */}
              <rect x="42" y="88" width="996" height="74" fill="url(#road-surface)" rx="4" />
            </g>

            {/* Directional Divider (Center Double Dashed Line) */}
            <line x1="42" y1="125" x2="1038" y2="125" stroke="#e2e8f0" strokeWidth="2" strokeDasharray="10 8" opacity="0.9" />

            {/* Sub-Lane Dividers (EB Top, WB Bottom) */}
            <line x1="42" y1="106" x2="1038" y2="106" stroke="#94a3b8" strokeWidth="1" strokeDasharray="5 5" opacity="0.7" />
            <line x1="42" y1="144" x2="1038" y2="144" stroke="#94a3b8" strokeWidth="1" strokeDasharray="5 5" opacity="0.7" />

            {/* Directional Lane Indicators */}
            <text x="50" y="101" fill="#cbd5e1" fontSize="7" fontFamily="monospace">EB L1</text>
            <text x="50" y="119" fill="#cbd5e1" fontSize="7" fontFamily="monospace">EB L0</text>
            <text x="50" y="138" fill="#cbd5e1" fontSize="7" fontFamily="monospace">WB L0</text>
            <text x="50" y="156" fill="#cbd5e1" fontSize="7" fontFamily="monospace">WB L1</text>

            {/* CRITICAL CONSTRAINED LINK: J3 -> J4 (x: 672 to 838) */}
            {isBlocked && (
              <g className="bottleneck-zone">
                <rect x="672" y="89" width="166" height="35" fill="url(#spillback-stripes)" />
                <rect x="672" y="89" width="166" height="35" fill="rgba(239, 68, 68, 0.15)" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="6 4" rx="3" />
                
                {/* 3D Floating Callout Bubble */}
                <g transform="translate(755, 68)">
                  <rect x="-65" y="-16" width="130" height="28" rx="14" fill="#ef4444" />
                  <text x="0" y="-3" textAnchor="middle" fill="#ffffff" fontSize="11" fontWeight="800">
                    88.7%
                  </text>
                  <text x="0" y="7" textAnchor="middle" fill="#fee2e2" fontSize="8" fontWeight="600">
                    Downstream Occupancy
                  </text>
                  {/* Pin Pointer */}
                  <polygon points="-5,12 5,12 0,19" fill="#ef4444" />
                </g>
              </g>
            )}

            {/* Warning link highlight in Rush */}
            {isRush && (
              <rect x="672" y="89" width="166" height="35" fill="rgba(245, 158, 11, 0.15)" stroke="#f59e0b" strokeWidth="1" strokeDasharray="4 4" rx="3" />
            )}

            {/* ANIMATED VEHICLES (Deterministic flowing markers) */}
            {/* 1. Free-flow Eastbound vehicles */}
            {[
              { base: 60, speed: 1.2, lane: 98, color: '#38bdf8' },
              { base: 140, speed: 1.4, lane: 114, color: '#ffffff' },
              { base: 280, speed: 1.3, lane: 98, color: '#38bdf8' },
              { base: 370, speed: 1.1, lane: 114, color: '#ffffff' },
              { base: 490, speed: 1.2, lane: 98, color: '#38bdf8' },
            ].map((v, i) => {
              const xPos = (v.base + animTick * v.speed) % 1000 + 40;
              // Don't show inside congested zone if blocked
              if (isBlocked && xPos >= 670 && xPos <= 830) return null;
              return (
                <rect
                  key={`eb-${i}`}
                  x={xPos}
                  y={v.lane}
                  width="16"
                  height="8"
                  rx="2"
                  fill={v.color}
                  stroke="#1e293b"
                  strokeWidth="0.5"
                />
              );
            })}

            {/* 2. Congested Packed Vehicles on J3 -> J4 link (when Blocked) */}
            {isBlocked && (
              <g className="congested-vehicles-group">
                {[680, 698, 716, 734, 752, 770, 788, 806, 824].map((vx, i) => (
                  <React.Fragment key={`cong-${i}`}>
                    <rect x={vx} y="98" width="14" height="8" rx="2" fill={i % 2 === 0 ? '#ef4444' : '#f97316'} stroke="#7f1d1d" strokeWidth="0.5" />
                    <rect x={vx - 8} y="114" width="14" height="8" rx="2" fill={i % 3 === 0 ? '#ef4444' : '#ea580c'} stroke="#7f1d1d" strokeWidth="0.5" />
                  </React.Fragment>
                ))}
              </g>
            )}

            {/* 3. J3 Approach Queue (12 queued vehicles before J3) */}
            {isBlocked && (
              <g className="j3-queue-pack">
                {[570, 586, 602, 618].map((qx, i) => (
                  <React.Fragment key={`jq-${i}`}>
                    <rect x={qx} y="98" width="13" height="8" rx="2" fill="#2563eb" stroke="#1e3a8a" strokeWidth="0.5" />
                    <rect x={qx} y="114" width="13" height="8" rx="2" fill="#2563eb" stroke="#1e3a8a" strokeWidth="0.5" />
                  </React.Fragment>
                ))}
              </g>
            )}

            {/* 4. Westbound vehicles (Right to Left flow) */}
            {[
              { base: 950, speed: 1.3, lane: 133, color: '#ffffff' },
              { base: 780, speed: 1.2, lane: 151, color: '#38bdf8' },
              { base: 560, speed: 1.4, lane: 133, color: '#ffffff' },
              { base: 340, speed: 1.1, lane: 151, color: '#38bdf8' },
              { base: 120, speed: 1.3, lane: 133, color: '#ffffff' },
            ].map((v, i) => {
              const xPos = 1000 - ((v.base + animTick * v.speed) % 1000) + 40;
              return (
                <rect
                  key={`wb-${i}`}
                  x={xPos}
                  y={v.lane}
                  width="16"
                  height="8"
                  rx="2"
                  fill={v.color}
                  stroke="#1e293b"
                  strokeWidth="0.5"
                />
              );
            })}

            {/* 4 INTERSECTION NODES (J1, J2, J3, J4) */}
            {junctions.map((j) => {
              const isSelected = selectedJunction === j.id;
              const isJ3 = j.id === 'J3';
              const jData = scenarioData.junctions[j.id];

              // Signal Color:
              // J3: If replayStep >= 6 => Yellow transition, else Green
              let signalAspect = '#10b981'; // Green
              if (j.id === 'J4') signalAspect = '#f59e0b';
              if (isJ3 && isBlocked && replayStep >= 6) signalAspect = '#f59e0b'; // Yellow transition

              const nodeClass = `junction-3d-node ${isSelected ? 'selected' : ''}`;

              return (
                <g
                  key={j.id}
                  className={nodeClass}
                  onClick={() => setSelectedJunction(j.id)}
                  onMouseEnter={(e) => {
                    const rect = containerRef.current.getBoundingClientRect();
                    setHoveredJunction(j.id);
                    setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
                  }}
                  onMouseLeave={() => setHoveredJunction(null)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Selection Elevation Highlight */}
                  {isSelected && (
                    <circle
                      cx={j.x}
                      cy="125"
                      r="26"
                      fill="none"
                      stroke="#2563eb"
                      strokeWidth="2.5"
                      strokeDasharray="6 4"
                      filter="url(#node-lift-shadow)"
                    />
                  )}

                  {/* Junction Box / Intersection Ring */}
                  <circle
                    cx={j.x}
                    cy="125"
                    r="19"
                    fill="#ffffff"
                    stroke={isJ3 && isBlocked ? '#ef4444' : isSelected ? '#2563eb' : '#cbd5e1'}
                    strokeWidth={isJ3 && isBlocked || isSelected ? 2.5 : 1.5}
                  />

                  {/* Node Label */}
                  <text
                    x={j.x}
                    y="129"
                    textAnchor="middle"
                    fill="#0f172a"
                    fontSize="11"
                    fontWeight="700"
                    fontFamily="monospace"
                  >
                    {j.id}
                  </text>

                  {/* Traffic Light Head on Post */}
                  <g transform={`translate(${j.x}, 72)`}>
                    {/* Post */}
                    <line x1="0" y1="0" x2="0" y2="34" stroke="#475569" strokeWidth="2.5" />
                    {/* Signal Box */}
                    <rect x="-8" y="-18" width="16" height="26" rx="3" fill="#1e293b" />
                    {/* Signal Aspect Light */}
                    <circle cx="0" cy="-5" r="5" fill={signalAspect} />
                    <circle cx="0" cy="-5" r="7" fill="none" stroke={signalAspect} strokeWidth="1" opacity="0.4" />
                  </g>

                  {/* Phase Label under Node */}
                  <text
                    x={j.x}
                    y="156"
                    textAnchor="middle"
                    fill="#64748b"
                    fontSize="9"
                    fontWeight="600"
                    fontFamily="monospace"
                  >
                    {isJ3 && isBlocked && replayStep >= 6 ? 'P1 YELLOW' : `P${jData.phase} GREEN`}
                  </text>
                </g>
              );
            })}

            {/* West Entry / East Exit Badges */}
            <g transform="translate(42, 125)">
              <rect x="-18" y="-14" width="36" height="28" rx="4" fill="#ffffff" stroke="#cbd5e1" strokeWidth="1" />
              <text x="0" y="3" textAnchor="middle" fontSize="9" fontWeight="700" fill="#64748b" fontFamily="monospace">W0</text>
              <text x="0" y="24" textAnchor="middle" fontSize="7" fontWeight="600" fill="#94a3b8">ENTRY</text>
            </g>

            <g transform="translate(1036, 125)">
              <rect x="-18" y="-14" width="36" height="28" rx="4" fill="#ffffff" stroke="#cbd5e1" strokeWidth="1" />
              <text x="0" y="3" textAnchor="middle" fontSize="9" fontWeight="700" fill="#64748b" fontFamily="monospace">E5</text>
              <text x="0" y="24" textAnchor="middle" fontSize="7" fontWeight="600" fill="#94a3b8">EXIT</text>
            </g>
          </svg>
        </div>

        {/* Hover Tooltip */}
        {hoveredJunction && (
          <div
            className="junction-hover-tooltip"
            style={{
              left: `${tooltipPos.x + 12}px`,
              top: `${tooltipPos.y - 45}px`,
            }}
          >
            <div className="tooltip-title">
              {hoveredJunction} // Eastbound
              <span className={`tooltip-badge ${scenarioData.junctions[hoveredJunction].risk === 'CRITICAL' ? 'crit' : 'norm'}`}>
                {scenarioData.junctions[hoveredJunction].risk}
              </span>
            </div>
            <div className="tooltip-row">
              <span>Main Queue:</span>
              <strong className="mono">{scenarioData.junctions[hoveredJunction].queueMain} veh</strong>
            </div>
            <div className="tooltip-row">
              <span>Downstream Occ:</span>
              <strong className="mono">{scenarioData.junctions[hoveredJunction].downstreamOcc}%</strong>
            </div>
            <div className="tooltip-row">
              <span>Risk State:</span>
              <strong className={`mono ${scenarioData.junctions[hoveredJunction].risk === 'CRITICAL' ? 'text-crit' : ''}`}>
                {scenarioData.junctions[hoveredJunction].risk}
              </strong>
            </div>
          </div>
        )}
      </div>

      {/* 4 Interactive Junction Status Cards Row Beneath the Corridor */}
      <div className="twin-cards-grid">
        {junctions.map((j) => {
          const isSelected = selectedJunction === j.id;
          const jData = scenarioData.junctions[j.id];
          const isCrit = jData.risk === 'CRITICAL';

          return (
            <div
              key={j.id}
              className={`twin-j-card ${isCrit ? 'card-critical' : ''} ${isSelected ? 'card-selected' : ''}`}
              onClick={() => setSelectedJunction(j.id)}
            >
              <div className="j-card-top">
                <span className="j-card-name mono">{j.id}</span>
                <span className={`j-card-pill ${isCrit ? 'pill-crit' : 'pill-norm'}`}>
                  <span className={`pill-dot ${isCrit ? 'dot-crit' : 'dot-norm'}`}></span>
                  {jData.risk}
                </span>
              </div>
              <div className="j-card-metrics">
                <div className="metric-line">
                  <span className="metric-dim">Queue:</span>
                  <span className={`metric-num mono ${isCrit ? 'text-crit' : ''}`}>{jData.queueMain} veh</span>
                </div>
                <div className="metric-line">
                  <span className="metric-dim">Downstream:</span>
                  <span className="metric-num mono">{jData.downstreamOcc}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
