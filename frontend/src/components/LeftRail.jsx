import React from 'react';

export default function LeftRail({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'corridor', label: 'CORRIDOR', code: '01' },
    { id: 'decisions', label: 'DECISIONS', code: '02' },
    { id: 'runs', label: 'RUNS', code: '03' },
  ];

  return (
    <aside className="left-rail">
      <div className="rail-header">
        <div className="rail-sys-code mono">SYS // TT-04</div>
        <div className="rail-title">CONTROL ROOM</div>
      </div>

      <nav className="rail-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`rail-nav-btn ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            <span className="nav-code mono">{item.code}</span>
            <span className="nav-label">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="rail-footer">
        <div className="micro-label">SUBSYSTEMS</div>
        <div className="rail-stat-row">
          <span className="stat-name">FIREWALL</span>
          <span className="badge badge-normal">M5 ACTIVE</span>
        </div>
        <div className="rail-stat-row">
          <span className="stat-name">SPILLBACK</span>
          <span className="badge badge-active">M6 ARMED</span>
        </div>
        <div className="rail-stat-row">
          <span className="stat-name">CORRIDOR</span>
          <span className="mono stat-val">4-JUNCTION</span>
        </div>
        <div className="rail-stat-row">
          <span className="stat-name">HORIZON</span>
          <span className="mono stat-val">180s</span>
        </div>
      </div>
    </aside>
  );
}
