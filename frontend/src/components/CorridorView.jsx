import React from 'react';
import { RouteIcon } from './Icons';

export default function CorridorView({ selectedJunction, setSelectedJunction }) {
  const junctions = [
    { id: 'J1', status: 'NORMAL', queue: 5, downstream: '31.2%', isCritical: false },
    { id: 'J2', status: 'NORMAL', queue: 8, downstream: '62.1%', isCritical: false },
    { id: 'J3', status: 'CRITICAL', queue: 12, downstream: '88.7%', isCritical: true },
    { id: 'J4', status: 'NORMAL', queue: 6, downstream: '40.3%', isCritical: false },
  ];

  return (
    <div className="corridor-card">
      <div className="corridor-header">
        <div className="corridor-title-group">
          <div className="corridor-icon-badge">
            <RouteIcon />
          </div>
          <div>
            <h2 className="corridor-title">Corridor View</h2>
            <p className="corridor-subtitle">West Entry → J1 → J2 → J3 → J4 → East Exit</p>
          </div>
        </div>
      </div>

      {/* Corridor Visual Canvas */}
      <div className="corridor-graphic-container">
        <svg viewBox="0 0 920 220" className="corridor-schematic-svg" preserveAspectRatio="xMidYMid meet">
          <defs>
            <filter id="shadow-soft" x="-10%" y="-10%" width="120%" height="130%">
              <feDropShadow dx="0" dy="4" stdDeviation="6" floodColor="#0f172a" floodOpacity="0.08" />
            </filter>
            <filter id="badge-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="3" stdDeviation="4" floodColor="#ef4444" floodOpacity="0.3" />
            </filter>
            <linearGradient id="road-grad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#334155" />
              <stop offset="50%" stopColor="#475569" />
              <stop offset="100%" stopColor="#334155" />
            </linearGradient>
            <linearGradient id="congested-grad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.55" />
            </linearGradient>
          </defs>

          {/* Background environment: Subtle Cityscape / Buildings & Foliage */}
          <g className="env-background" opacity="0.6">
            {/* Background buildings */}
            <rect x="30" y="25" width="55" height="40" fill="#e2e8f0" rx="3" />
            <rect x="95" y="15" width="45" height="50" fill="#cbd5e1" rx="3" />
            <rect x="150" y="30" width="60" height="35" fill="#e2e8f0" rx="3" />
            
            <rect x="250" y="20" width="50" height="45" fill="#cbd5e1" rx="3" />
            <rect x="310" y="32" width="70" height="33" fill="#e2e8f0" rx="3" />
            
            <rect x="470" y="18" width="60" height="47" fill="#e2e8f0" rx="3" />
            <rect x="540" y="28" width="55" height="37" fill="#cbd5e1" rx="3" />
            
            <rect x="690" y="22" width="65" height="43" fill="#e2e8f0" rx="3" />
            <rect x="765" y="16" width="50" height="49" fill="#cbd5e1" rx="3" />
            <rect x="825" y="26" width="60" height="39" fill="#e2e8f0" rx="3" />

            {/* Trees & Landscaping */}
            {[50, 130, 230, 360, 450, 580, 670, 790, 870].map((tx, idx) => (
              <g key={`tree-${idx}`} transform={`translate(${tx}, 55)`}>
                <circle cx="0" cy="0" r="10" fill="#86efac" opacity="0.9" />
                <circle cx="5" cy="-2" r="8" fill="#4ade80" opacity="0.95" />
                <circle cx="-4" cy="1" r="7" fill="#22c55e" opacity="0.8" />
              </g>
            ))}
          </g>

          {/* Cross Streets (Vertical Roads) */}
          {[170, 390, 610, 810].map((cx, idx) => (
            <g key={`cross-${idx}`}>
              <rect x={cx - 18} y="55" width="36" height="120" fill="#475569" />
              <line x1={cx} y1="55" x2={cx} y2="85" stroke="#f8fafc" strokeWidth="1.5" strokeDasharray="5,4" />
              <line x1={cx} y1="145" x2={cx} y2="175" stroke="#f8fafc" strokeWidth="1.5" strokeDasharray="5,4" />
            </g>
          ))}

          {/* Main Arterial Roadway (Horizontal) */}
          <rect x="20" y="85" width="880" height="60" fill="url(#road-grad)" rx="6" filter="url(#shadow-soft)" />
          {/* Sidewalk borders */}
          <rect x="20" y="82" width="880" height="4" fill="#cbd5e1" />
          <rect x="20" y="144" width="880" height="4" fill="#cbd5e1" />

          {/* Road Lane Markings */}
          <line x1="20" y1="115" x2="900" y2="115" stroke="#f8fafc" strokeWidth="2" strokeDasharray="14,10" opacity="0.85" />

          {/* Critical Congested Link Highlight between J3 (x=610) and J4 (x=810) */}
          <g className="congested-zone">
            <rect x="628" y="86" width="164" height="58" fill="url(#congested-grad)" />
            <rect x="628" y="86" width="164" height="58" fill="none" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="6,4" />
          </g>

          {/* Moving & Queued Vehicles on the Arterial */}
          {/* Between Entry and J1 */}
          <rect x="55" y="93" width="18" height="9" rx="2" fill="#38bdf8" />
          <rect x="90" y="103" width="19" height="9" rx="2" fill="#ffffff" />
          <rect x="130" y="94" width="18" height="9" rx="2" fill="#38bdf8" />

          {/* Between J1 and J2 */}
          <rect x="210" y="103" width="18" height="9" rx="2" fill="#cbd5e1" />
          <rect x="250" y="93" width="20" height="9" rx="2" fill="#38bdf8" />
          <rect x="295" y="103" width="18" height="9" rx="2" fill="#ffffff" />
          <rect x="345" y="93" width="18" height="9" rx="2" fill="#38bdf8" />

          {/* Between J2 and J3 */}
          <rect x="430" y="93" width="19" height="9" rx="2" fill="#ffffff" />
          <rect x="475" y="103" width="18" height="9" rx="2" fill="#38bdf8" />
          <rect x="520" y="93" width="18" height="9" rx="2" fill="#cbd5e1" />
          <rect x="560" y="103" width="18" height="9" rx="2" fill="#ef4444" />

          {/* Dense Queue between J3 and J4 (HEAVY TRAFFIC) */}
          {[635, 655, 675, 695, 715, 735, 755, 775].map((vx, i) => (
            <React.Fragment key={`veh-${i}`}>
              <rect x={vx} y="93" width="17" height="9" rx="2" fill={i % 2 === 0 ? '#ef4444' : '#f97316'} />
              <rect x={vx - 10} y="103" width="17" height="9" rx="2" fill={i % 3 === 0 ? '#ef4444' : '#fb923c'} />
            </React.Fragment>
          ))}

          {/* Past J4 towards East Exit */}
          <rect x="835" y="93" width="18" height="9" rx="2" fill="#38bdf8" />
          <rect x="865" y="103" width="18" height="9" rx="2" fill="#ffffff" />

          {/* Text Labels: West Entry / East Exit */}
          <text x="35" y="165" fill="#64748b" fontSize="10" fontWeight="600">West Entry</text>
          <text x="850" y="165" fill="#64748b" fontSize="10" fontWeight="600">East Exit</text>

          {/* Intersection Nodes & Traffic Lights */}
          {[
            { id: 'J1', x: 170, color: '#10b981', active: false },
            { id: 'J2', x: 390, color: '#10b981', active: false },
            { id: 'J3', x: 610, color: '#ef4444', active: true },
            { id: 'J4', x: 810, color: '#10b981', active: false },
          ].map((j) => (
            <g
              key={j.id}
              className={`junction-marker ${selectedJunction === j.id ? 'selected' : ''}`}
              onClick={() => setSelectedJunction(j.id)}
              style={{ cursor: 'pointer' }}
            >
              {/* Traffic light post above road */}
              <rect x={j.x - 2} y="56" width="4" height="26" fill="#334155" />
              {/* Traffic light box */}
              <rect x={j.x - 9} y="38" width="18" height="26" rx="4" fill="#1e293b" />
              {/* Signal lights: Red, Yellow, Green */}
              <circle cx={j.x} cy="43" r="3" fill={j.color === '#ef4444' ? '#ef4444' : '#475569'} />
              <circle cx={j.x} cy="51" r="3" fill={j.color === '#f59e0b' ? '#f59e0b' : '#475569'} />
              <circle cx={j.x} cy="59" r="3" fill={j.color === '#10b981' ? '#10b981' : '#475569'} />

              {/* Junction label circle above light */}
              <circle cx={j.x} cy="24" r="12" fill="#ffffff" stroke={j.active ? '#ef4444' : '#cbd5e1'} strokeWidth={j.active ? '2' : '1.5'} filter="url(#shadow-soft)" />
              <text x={j.x} y="28" textAnchor="middle" fill="#1e293b" fontSize="11" fontWeight="700">
                {j.id}
              </text>
            </g>
          ))}

          {/* CRITICAL CALLOUT BADGE pointing down to Link J3_J4 */}
          <g transform="translate(710, 52)" filter="url(#badge-glow)">
            {/* Red Pill */}
            <rect x="-70" y="-18" width="140" height="30" rx="15" fill="#ef4444" />
            <text x="0" y="-3" textAnchor="middle" fill="#ffffff" fontSize="12" fontWeight="800">
              88.7%
            </text>
            <text x="0" y="8" textAnchor="middle" fill="#fee2e2" fontSize="9" fontWeight="600" letterSpacing="0.02em">
              Downstream Occupancy
            </text>
            {/* Pin pointer triangle */}
            <polygon points="-6,12 6,12 0,22" fill="#ef4444" />
            <circle cx="0" cy="24" r="3" fill="#ef4444" />
          </g>
        </svg>
      </div>

      {/* Floating 4 Junction Status Cards underneath */}
      <div className="junction-cards-row">
        {junctions.map((j) => {
          const isSelected = selectedJunction === j.id;
          return (
            <div
              key={j.id}
              className={`j-card ${j.isCritical ? 'critical-card' : ''} ${isSelected ? 'selected-card' : ''}`}
              onClick={() => setSelectedJunction(j.id)}
            >
              <div className="j-card-header">
                <span className="j-card-id">{j.id}</span>
                <span className={`j-card-status ${j.isCritical ? 'status-critical' : 'status-normal'}`}>
                  <span className={`status-dot ${j.isCritical ? 'dot-red' : 'dot-green'}`}></span>
                  {j.status}
                </span>
              </div>
              <div className="j-card-data">
                <div className="j-data-item">
                  <span className="j-data-label">Queue:</span>
                  <span className={`j-data-val ${j.isCritical ? 'val-crit' : ''}`}>{j.queue}</span>
                </div>
                <div className="j-data-item">
                  <span className="j-data-label">Downstream:</span>
                  <span className="j-data-val">{j.downstream}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
