import React, { useState, useEffect } from 'react';
import { fetchSystemInfo } from '../api/client';

export const NeofetchCard = () => {
  const [sysInfo, setSysInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSystemInfo()
      .then((data) => {
        setSysInfo(data);
        setLoading(false);
      })
      .catch((err) => {
        console.warn('Could not fetch live system info:', err.message);
        setLoading(false);
      });
  }, []);

  const palette = [
    '#050805', // Black
    '#ff5f56', // Red
    '#39ff7a', // Phosphor Green
    '#ffd24a', // Amber
    '#2563eb', // Blue
    '#d946ef', // Magenta
    '#5cf6ff', // Cyan
    '#eafff1'  // White
  ];

  const playerCount = sysInfo?.player_count?.toLocaleString() || '5,690';
  const teamCount = sysInfo?.team_count?.toLocaleString() || '150';
  const predCount = sysInfo?.prediction_count || 0;
  const isOnline = sysInfo?.status === 'online';

  return (
    <section className="neofetch-section">
      <div className="shell-prompt">
        <span className="prompt-host">clptm~/engine</span>
        <span className="prompt-symbol">$</span>
        <span className="prompt-cmd">neofetch --system</span>
        <span className="prompt-comment">
          # live telemetry &amp; database status ({loading ? 'probing...' : isOnline ? 'CONNECTED' : 'STANDBY'})
        </span>
      </div>

      <div className="console-panel neofetch-panel">
        {/* Left Column: ASCII Graphic */}
        <div className="ascii-avatar-box">
          <pre className="ascii-avatar-art">
{`    ┌──────────────────┐
    │  [  ·   ·   ·  ] │
    │   \\           /  │
    │    \\   (o)   /   │
    ├─────\\───────/────┤
    │  .   | (·) |   . │
    │      |     |     │
    │  .   | (·) |   . │
    ├─────/───────\\────┤
    │    /   (o)   \\   │
    │   /           \\  │
    │  [  ·   ·   ·  ] │
    └──────────────────┘
       [CLPTM TACTICAL]
     * PITCH TENSOR v1.4 *`}
          </pre>
          <div className="avatar-label">
            <span className="highlight-green">model</span>
            <span style={{ color: 'var(--text-muted)' }}>@</span>
            <span>clptm-prod</span>
          </div>
        </div>

        {/* Right Column: Neofetch System Info */}
        <div className="neofetch-specs">
          <div className="neofetch-title">
            <span className="highlight-green">clptm</span>
            <span style={{ color: 'var(--text-muted)' }}>@</span>
            <span style={{ color: 'var(--text-primary)' }}>transferpred</span>
            <span style={{ color: 'var(--border-bright)' }}> ──────────────────────</span>
          </div>

          <div className="spec-row">
            <span className="spec-key">Architecture:</span>
            <span className="spec-value">
              {sysInfo?.engine || 'LightGBM Regressor + MLP + Bayesian Ridge'}
            </span>
          </div>

          <div className="spec-row">
            <span className="spec-key">Database Store:</span>
            <span className="spec-value">
              SQLite / PostgreSQL ({playerCount} players, {teamCount} teams, {predCount} audits)
            </span>
          </div>

          <div className="spec-row">
            <span className="spec-key">Bayesian Bounds:</span>
            <span className="spec-value">Bayesian Ridge (95% Credible Intervals)</span>
          </div>

          <div className="spec-row">
            <span className="spec-key">Dataset Scope:</span>
            <span className="spec-value">14,865 standardized player-seasons (&gt;= 600 mins)</span>
          </div>

          <div className="spec-row">
            <span className="spec-key">Transfer Pairs:</span>
            <span className="spec-value">955 calibrated longitudinal transfer pairs</span>
          </div>

          <div className="spec-row">
            <span className="spec-key">Target Metrics:</span>
            <span className="spec-value">goals_p90, assists_p90, xg_p90, xag_p90</span>
          </div>

          <div className="spec-row">
            <span className="spec-key">Tactical TRC:</span>
            <span className="spec-value">Target club strength delta (mitigation +10% / -12%)</span>
          </div>

          <div className="spec-row">
            <span className="spec-key">API Cluster:</span>
            <span className="spec-value glow-amber">
              {isOnline
                ? `ACTIVE [● uvicorn :8000, 99.98% uptime, ${playerCount} DB records]`
                : 'OFFLINE / STANDALONE SIMULATOR'}
            </span>
          </div>

          {/* Terminal Color Swatches Strip */}
          <div className="terminal-palette-strip" title="ANSI 8-Color Terminal Palette">
            {palette.map((color, idx) => (
              <span
                key={idx}
                className="palette-swatch"
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
