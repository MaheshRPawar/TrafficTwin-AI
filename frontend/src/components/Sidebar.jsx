import React from 'react';
import {
  LogoIcon,
  OverviewIcon,
  CorridorIcon,
  JunctionsIcon,
  DecisionsIcon,
  SimulationIcon,
  ResultsIcon,
} from './Icons';

export default function Sidebar({ activeNav = 'Overview', setActiveNav }) {
  const navItems = [
    { id: 'Overview', label: 'Overview', icon: <OverviewIcon /> },
    { id: 'Corridor', label: 'Corridor', icon: <CorridorIcon /> },
    { id: 'Junctions', label: 'Junctions', icon: <JunctionsIcon /> },
    { id: 'Decisions', label: 'Decisions', icon: <DecisionsIcon /> },
    { id: 'Simulation', label: 'Simulation', icon: <SimulationIcon /> },
    { id: 'Results', label: 'Results', icon: <ResultsIcon /> },
  ];

  return (
    <aside className="app-sidebar">
      {/* Brand Header */}
      <div className="sidebar-brand">
        <LogoIcon />
        <div className="brand-text">
          <h1 className="brand-title">TrafficTwin</h1>
          <p className="brand-subtitle">Corridor Operations</p>
        </div>
      </div>

      {/* Navigation Items */}
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const isActive = activeNav === item.id;
          return (
            <button
              key={item.id}
              className={`sidebar-nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setActiveNav && setActiveNav(item.id)}
            >
              <span className="nav-item-icon">{item.icon}</span>
              <span className="nav-item-label">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Bottom SUMO Simulation Info Badge */}
      <div className="sidebar-bottom-badge">
        <div className="sumo-indicator">
          <span className="sumo-dot"></span>
          <span className="sumo-version">SUMO 1.27.1</span>
        </div>
        <p className="sumo-desc">Recorded Simulation</p>
        <p className="sumo-seed">Seed: 42</p>
      </div>
    </aside>
  );
}
