import React, { useState } from 'react';
import { ChartIcon } from './Icons';

export const ScenarioChart = () => {
  const [activeTab, setActiveTab] = useState('Avg Wait Time');

  const scenarios = [
    { name: 'Normal', fixed: 20.0, reactive: 13.5, spillback: 13.5 },
    { name: 'Rush', fixed: 32.4, reactive: 19.6, spillback: 19.6 },
    { name: 'Blocked Downstream', fixed: 19.6, reactive: 12.8, spillback: 12.8 },
    { name: 'Ambulance', fixed: 18.2, reactive: 11.6, spillback: 11.6 },
  ];

  const yMax = 80;
  const chartHeight = 130;
  const chartWidth = 380;

  return (
    <div className="bottom-chart-card">
      <div className="chart-card-header">
        <div className="chart-title-group">
          <div className="chart-icon-badge">
            <ChartIcon />
          </div>
          <h3 className="chart-title">Scenario Comparison</h3>
        </div>
        <div className="chart-tabs">
          {['Avg Wait Time', 'P95 Wait', 'Max Queue', 'Throughput'].map((tab) => (
            <button
              key={tab}
              className={`chart-tab-btn ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="chart-body">
        <svg viewBox="0 0 440 180" className="chart-svg" preserveAspectRatio="xMidYMid meet">
          {/* Y Axis Grid lines */}
          {[0, 20, 40, 60, 80].map((val) => {
            const y = 140 - (val / yMax) * chartHeight;
            return (
              <g key={val}>
                <line x1="45" y1={y} x2="420" y2={y} stroke="#f1f5f9" strokeWidth="1" />
                <text x="38" y={y + 3} textAnchor="end" fontSize="9" fill="#94a3b8">
                  {val}
                </text>
              </g>
            );
          })}

          {/* Y Axis Label */}
          <text
            x="-70"
            y="14"
            transform="rotate(-90)"
            fontSize="8"
            fill="#94a3b8"
            textAnchor="middle"
          >
            Waiting Time (seconds)
          </text>

          {/* Scenario Bar Groups */}
          {scenarios.map((s, idx) => {
            const groupX = 65 + idx * 90;
            const barWidth = 16;
            const fixedH = (s.fixed / yMax) * chartHeight;
            const reactH = (s.reactive / yMax) * chartHeight;
            const spillH = (s.spillback / yMax) * chartHeight;

            return (
              <g key={s.name} transform={`translate(${groupX}, 0)`}>
                {/* Fixed bar */}
                <rect
                  x="0"
                  y={140 - fixedH}
                  width={barWidth}
                  height={fixedH}
                  fill="#94a3b8"
                  rx="2"
                />
                <text x={barWidth / 2} y={135 - fixedH} fontSize="8" fill="#64748b" textAnchor="middle">
                  {s.fixed}
                </text>

                {/* Reactive bar */}
                <rect
                  x="20"
                  y={140 - reactH}
                  width={barWidth}
                  height={reactH}
                  fill="#2563eb"
                  rx="2"
                />
                <text x={20 + barWidth / 2} y={135 - reactH} fontSize="8" fill="#2563eb" textAnchor="middle">
                  {s.reactive}
                </text>

                {/* Spillback bar */}
                <rect
                  x="40"
                  y={140 - spillH}
                  width={barWidth}
                  height={spillH}
                  fill="#10b981"
                  rx="2"
                />
                <text x={40 + barWidth / 2} y={135 - spillH} fontSize="8" fill="#10b981" textAnchor="middle">
                  {s.spillback}
                </text>

                {/* Scenario X label */}
                <text x="28" y="156" fontSize="9" fill="#64748b" textAnchor="middle" fontWeight="500">
                  {s.name}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Legend */}
        <div className="chart-legend">
          <div className="legend-item">
            <span className="legend-box" style={{ background: '#94a3b8' }}></span>
            <span>Fixed</span>
          </div>
          <div className="legend-item">
            <span className="legend-box" style={{ background: '#2563eb' }}></span>
            <span>Reactive (M3)</span>
          </div>
          <div className="legend-item">
            <span className="legend-box" style={{ background: '#10b981' }}></span>
            <span>Spillback (M6)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export const JunctionMetricsChart = () => {
  const [activeTab, setActiveTab] = useState('Queue Length');

  const timePoints = [0, 60, 120, 180, 240, 300, 360];
  const maxVal = 200;
  const chartHeight = 120;
  const chartWidth = 360;

  // Points for 4 lines over time [t=0 to 360]
  // J1: blue (stable low 20-30)
  // J2: green (moderate 40-60)
  // J3: red (shoots up to 190 at t=200, then descends to 100)
  // J4: yellow (moderate 40-50)
  const linePoints = {
    J1: [[0, 20], [60, 25], [120, 28], [180, 30], [240, 32], [300, 24], [360, 22]],
    J2: [[0, 25], [60, 35], [120, 52], [180, 68], [240, 50], [300, 42], [360, 38]],
    J3: [[0, 28], [60, 48], [120, 105], [180, 188], [240, 155], [300, 102], [360, 100]],
    J4: [[0, 22], [60, 30], [120, 42], [180, 58], [240, 52], [300, 46], [360, 45]],
  };

  const getPath = (pts) => {
    return pts
      .map((pt, i) => {
        const x = 50 + (pt[0] / 360) * chartWidth;
        const y = 140 - (pt[1] / maxVal) * chartHeight;
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
  };

  return (
    <div className="bottom-chart-card">
      <div className="chart-card-header">
        <div className="chart-title-group">
          <div className="chart-icon-badge">
            <ChartIcon />
          </div>
          <h3 className="chart-title">Junction Metrics</h3>
        </div>
        <div className="chart-tabs">
          {['Queue Length', 'Downstream Occupancy', 'Flow'].map((tab) => (
            <button
              key={tab}
              className={`chart-tab-btn ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="chart-body">
        <svg viewBox="0 0 440 180" className="chart-svg" preserveAspectRatio="xMidYMid meet">
          {/* Y Axis Grid lines */}
          {[0, 50, 100, 150, 200].map((val) => {
            const y = 140 - (val / maxVal) * chartHeight;
            return (
              <g key={val}>
                <line x1="50" y1={y} x2="420" y2={y} stroke="#f1f5f9" strokeWidth="1" />
                <text x="42" y={y + 3} textAnchor="end" fontSize="9" fill="#94a3b8">
                  {val}
                </text>
              </g>
            );
          })}

          {/* Y Axis Label */}
          <text
            x="-70"
            y="14"
            transform="rotate(-90)"
            fontSize="8"
            fill="#94a3b8"
            textAnchor="middle"
          >
            Vehicles
          </text>

          {/* X Axis Time Marks */}
          {timePoints.map((t) => {
            const x = 50 + (t / 360) * chartWidth;
            return (
              <text key={t} x={x} y="156" fontSize="8" fill="#94a3b8" textAnchor="middle">
                {t}
              </text>
            );
          })}

          {/* X Axis Label */}
          <text x="230" y="170" fontSize="8" fill="#94a3b8" textAnchor="middle">
            Simulation Time (seconds)
          </text>

          {/* Lines */}
          <path d={getPath(linePoints.J1)} fill="none" stroke="#2563eb" strokeWidth="2" />
          <path d={getPath(linePoints.J2)} fill="none" stroke="#10b981" strokeWidth="2" />
          <path d={getPath(linePoints.J4)} fill="none" stroke="#f59e0b" strokeWidth="2" />
          <path d={getPath(linePoints.J3)} fill="none" stroke="#ef4444" strokeWidth="2.5" />

          {/* Dots on points */}
          {Object.entries(linePoints).map(([name, pts]) => {
            const color =
              name === 'J1' ? '#2563eb' : name === 'J2' ? '#10b981' : name === 'J3' ? '#ef4444' : '#f59e0b';
            return pts.map((pt, i) => {
              const x = 50 + (pt[0] / 360) * chartWidth;
              const y = 140 - (pt[1] / maxVal) * chartHeight;
              return <circle key={`${name}-${i}`} cx={x} cy={y} r="2.5" fill={color} />;
            });
          })}
        </svg>

        {/* Legend */}
        <div className="chart-legend">
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#2563eb' }}></span>
            <span>J1</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#10b981' }}></span>
            <span>J2</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#ef4444' }}></span>
            <span>J3</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot" style={{ background: '#f59e0b' }}></span>
            <span>J4</span>
          </div>
        </div>
      </div>
    </div>
  );
};
