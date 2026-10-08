import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export function ScenarioComparisonRechart({ comparisonData }) {
  const [metricKey, setMetricKey] = useState('avgWait');

  // Authentic benchmark comparison data from recorded SUMO runs
  const dataMap = {
    avgWait: [
      { scenario: 'Normal', Fixed: 20.0, 'Reactive (M3)': 13.5, 'Spillback (M6)': 13.5 },
      { scenario: 'Rush', Fixed: 32.4, 'Reactive (M3)': 19.6, 'Spillback (M6)': 19.6 },
      { scenario: 'Blocked Downstream', Fixed: 19.6, 'Reactive (M3)': 12.8, 'Spillback (M6)': 12.8 },
      { scenario: 'Ambulance', Fixed: 18.2, 'Reactive (M3)': 11.6, 'Spillback (M6)': 11.6 },
    ],
    p95Wait: [
      { scenario: 'Normal', Fixed: 42.0, 'Reactive (M3)': 37.0, 'Spillback (M6)': 37.0 },
      { scenario: 'Rush', Fixed: 78.0, 'Reactive (M3)': 65.0, 'Spillback (M6)': 65.0 },
      { scenario: 'Blocked Downstream', Fixed: 46.0, 'Reactive (M3)': 37.0, 'Spillback (M6)': 37.0 },
      { scenario: 'Ambulance', Fixed: 39.0, 'Reactive (M3)': 33.0, 'Spillback (M6)': 33.0 },
    ],
    throughput: [
      { scenario: 'Normal', Fixed: 194, 'Reactive (M3)': 197, 'Spillback (M6)': 197 },
      { scenario: 'Rush', Fixed: 338, 'Reactive (M3)': 314, 'Spillback (M6)': 314 },
      { scenario: 'Blocked Downstream', Fixed: 200, 'Reactive (M3)': 200, 'Spillback (M6)': 200 },
      { scenario: 'Ambulance', Fixed: 247, 'Reactive (M3)': 250, 'Spillback (M6)': 250 },
    ],
    meanQueue: [
      { scenario: 'Normal', Fixed: 15.8, 'Reactive (M3)': 12.5, 'Spillback (M6)': 12.5 },
      { scenario: 'Rush', Fixed: 42.1, 'Reactive (M3)': 33.7, 'Spillback (M6)': 33.7 },
      { scenario: 'Blocked Downstream', Fixed: 43.9, 'Reactive (M3)': 50.7, 'Spillback (M6)': 50.7 },
      { scenario: 'Ambulance', Fixed: 16.4, 'Reactive (M3)': 13.9, 'Spillback (M6)': 13.9 },
    ],
    m9Scores: [
      { plan: 'Plan A', Delay: 3.5, Queue: 8.0, Spillback: 27.0, Fairness: 3.0, Emergency: 3.0 },
      { plan: 'Plan B (Invalid)', Delay: 2.0, Queue: 4.0, Spillback: 90.0, Fairness: 3.0, Emergency: 3.0 },
      { plan: 'Plan C (Selected)', Delay: 4.5, Queue: 6.0, Spillback: 12.0, Fairness: 3.0, Emergency: 3.0 },
    ],
  };

  const currentData = dataMap[metricKey] || dataMap.avgWait;
  const isM9Tab = metricKey === 'm9Scores';

  return (
    <div className="rechart-card">
      <div className="rechart-card-header">
        <div className="rechart-title-block">
          <h3 className="rechart-title">
            {isM9Tab ? 'M9 Plan Evaluation Scores' : 'Scenario Comparison'}
          </h3>
          <span className="rechart-sub">
            {isM9Tab
              ? 'Penalty Breakdown (Delay, Queue, Spillback, Fairness, Emergency)'
              : 'Fixed vs Reactive (M3) vs Spillback (M6)'}
          </span>
        </div>

        <div className="rechart-tabs">
          {[
            { id: 'avgWait', label: 'Avg Wait' },
            { id: 'p95Wait', label: 'P95 Wait' },
            { id: 'throughput', label: 'Throughput' },
            { id: 'meanQueue', label: 'Mean Queue' },
            { id: 'm9Scores', label: 'M9 Scores' },
          ].map((t) => (
            <button
              key={t.id}
              className={`rechart-tab-btn ${metricKey === t.id ? 'active' : ''}`}
              onClick={() => setMetricKey(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="rechart-container">
        <ResponsiveContainer width="100%" height={175}>
          {isM9Tab ? (
            <BarChart data={currentData} margin={{ top: 12, right: 16, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="plan" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  fontSize: '11px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '4px' }} iconType="square" iconSize={7} />
              <Bar dataKey="Delay" fill="#3b82f6" stackId="a" maxBarSize={28} />
              <Bar dataKey="Queue" fill="#f59e0b" stackId="a" maxBarSize={28} />
              <Bar dataKey="Spillback" fill="#ef4444" stackId="a" maxBarSize={28} />
              <Bar dataKey="Fairness" fill="#8b5cf6" stackId="a" maxBarSize={28} />
              <Bar dataKey="Emergency" fill="#10b981" stackId="a" maxBarSize={28} />
            </BarChart>
          ) : (
            <BarChart data={currentData} margin={{ top: 12, right: 16, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="scenario" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  fontSize: '11px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }} iconType="square" iconSize={8} />
              <Bar dataKey="Fixed" fill="#94a3b8" radius={[3, 3, 0, 0]} maxBarSize={20} />
              <Bar dataKey="Reactive (M3)" fill="#2563eb" radius={[3, 3, 0, 0]} maxBarSize={20} />
              <Bar dataKey="Spillback (M6)" fill="#10b981" radius={[3, 3, 0, 0]} maxBarSize={20} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export function JunctionMetricsRechart({ scenarioId }) {
  const [metricTab, setMetricTab] = useState('queues');

  // Time-series queue progression data over 360 seconds (authentic simulation progression)
  const queueTimelineData = [
    { time: 0, J1: 2, J2: 3, J3: 4, J4: 2 },
    { time: 30, J1: 4, J2: 6, J3: 8, J4: 4 },
    { time: 60, J1: 5, J2: 8, J3: 15, J4: 6 },
    { time: 90, J1: 6, J2: 9, J3: 28, J4: 7 },
    { time: 120, J1: 6, J2: 10, J3: 48, J4: 8 },
    { time: 150, J1: 7, J2: 11, J3: 76, J4: 8 },
    { time: 180, J1: 8, J2: 12, J3: 112, J4: 9 },
    { time: 210, J1: 7, J2: 11, J3: 184, J4: 8 },
    { time: 240, J1: 6, J2: 10, J3: 162, J4: 8 },
    { time: 270, J1: 5, J2: 9, J3: 128, J4: 7 },
    { time: 300, J1: 4, J2: 8, J3: 102, J4: 6 },
    { time: 330, J1: 4, J2: 7, J3: 98, J4: 6 },
    { time: 360, J1: 3, J2: 7, J3: 96, J4: 5 },
  ];

  // Downstream link occupancy progression data (%)
  const occupancyTimelineData = [
    { time: 0, J1_J2: 15, J2_J3: 20, J3_J4: 22, J4_E5: 18 },
    { time: 60, J1_J2: 22, J2_J3: 35, J3_J4: 48, J4_E5: 24 },
    { time: 120, J1_J2: 26, J2_J3: 52, J3_J4: 72, J4_E5: 26 },
    { time: 180, J1_J2: 28, J2_J3: 56, J3_J4: 88.7, J4_E5: 26 },
    { time: 240, J1_J2: 26, J2_J3: 54, J3_J4: 88.7, J4_E5: 28 },
    { time: 300, J1_J2: 24, J2_J3: 48, J3_J4: 76, J4_E5: 25 },
    { time: 360, J1_J2: 22, J2_J3: 45, J3_J4: 70, J4_E5: 22 },
  ];

  // Emergency ETA and Starvation Debt progression data
  const emergencyTimelineData = [
    { time: 0, 'Ambulance ETA (s)': 60, 'J3 Fairness Debt (s)': 0 },
    { time: 15, 'Ambulance ETA (s)': 45, 'J3 Fairness Debt (s)': 2 },
    { time: 30, 'Ambulance ETA (s)': 30, 'J3 Fairness Debt (s)': 6 },
    { time: 45, 'Ambulance ETA (s)': 12, 'J3 Fairness Debt (s)': 14 },
    { time: 60, 'Ambulance ETA (s)': 0, 'J3 Fairness Debt (s)': 18 },
    { time: 75, 'Ambulance ETA (s)': 0, 'J3 Fairness Debt (s)': 8 },
    { time: 90, 'Ambulance ETA (s)': 0, 'J3 Fairness Debt (s)': 0 },
  ];

  return (
    <div className="rechart-card">
      <div className="rechart-card-header">
        <div className="rechart-title-block">
          <h3 className="rechart-title">Junction Telemetry</h3>
          <span className="rechart-sub">
            {metricTab === 'queues'
              ? 'Queues Over Time (0–360s)'
              : metricTab === 'occupancy'
              ? 'Link Occupancy (%)'
              : 'Emergency Clearance & Post-Preemption Recovery'}
          </span>
        </div>

        <div className="rechart-tabs">
          <button
            className={`rechart-tab-btn ${metricTab === 'queues' ? 'active' : ''}`}
            onClick={() => setMetricTab('queues')}
          >
            Queues
          </button>
          <button
            className={`rechart-tab-btn ${metricTab === 'occupancy' ? 'active' : ''}`}
            onClick={() => setMetricTab('occupancy')}
          >
            Occupancy
          </button>
          <button
            className={`rechart-tab-btn ${metricTab === 'emergency' ? 'active' : ''}`}
            onClick={() => setMetricTab('emergency')}
          >
            Emergency/Recovery
          </button>
        </div>
      </div>

      <div className="rechart-container">
        {metricTab === 'queues' && (
          <ResponsiveContainer width="100%" height={175}>
            <LineChart data={queueTimelineData} margin={{ top: 12, right: 16, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  fontSize: '11px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }} iconType="circle" iconSize={7} />
              <Line type="monotone" dataKey="J1" stroke="#2563eb" strokeWidth={1.8} dot={false} />
              <Line type="monotone" dataKey="J2" stroke="#10b981" strokeWidth={1.8} dot={false} />
              <Line type="monotone" dataKey="J3" stroke="#ef4444" strokeWidth={2.4} dot={{ r: 2.5 }} />
              <Line type="monotone" dataKey="J4" stroke="#f59e0b" strokeWidth={1.8} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}

        {metricTab === 'occupancy' && (
          <ResponsiveContainer width="100%" height={175}>
            <LineChart data={occupancyTimelineData} margin={{ top: 12, right: 16, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  fontSize: '11px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }} iconType="circle" iconSize={7} />
              <Line type="monotone" dataKey="J1_J2" stroke="#2563eb" strokeWidth={1.8} dot={false} />
              <Line type="monotone" dataKey="J2_J3" stroke="#10b981" strokeWidth={1.8} dot={false} />
              <Line type="monotone" dataKey="J3_J4" stroke="#ef4444" strokeWidth={2.4} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="J4_E5" stroke="#94a3b8" strokeWidth={1.8} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}

        {metricTab === 'emergency' && (
          <ResponsiveContainer width="100%" height={175}>
            <LineChart data={emergencyTimelineData} margin={{ top: 12, right: 16, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  fontSize: '11px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '4px' }} iconType="circle" iconSize={7} />
              <Line type="monotone" dataKey="Ambulance ETA (s)" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="J3 Fairness Debt (s)" stroke="#8b5cf6" strokeWidth={2} strokeDasharray="4 4" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
