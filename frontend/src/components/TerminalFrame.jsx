import React, { useState, useEffect } from 'react';
import { fetchSystemInfo, loginApi } from '../api/client';

export const TerminalFrame = ({
  activeTab,
  setActiveTab,
  crtScanlines,
  setCrtScanlines,
  children
}) => {
  const [backendOnline, setBackendOnline] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState('viewer');
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authUsername, setAuthUsername] = useState('admin');
  const [authPassword, setAuthPassword] = useState('admin123');
  const [authMsg, setAuthMsg] = useState('');

  useEffect(() => {
    fetchSystemInfo()
      .then((data) => {
        if (data?.status === 'online') {
          setBackendOnline(true);
        }
      })
      .catch(() => setBackendOnline(false));
  }, []);

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = await loginApi(authUsername, authPassword);
      if (data?.access_token) {
        setCurrentUserRole(authUsername === 'admin' ? 'admin' : 'viewer');
        setAuthMsg(`Authenticated as ${authUsername.toUpperCase()}`);
        setTimeout(() => {
          setShowAuthModal(false);
          setAuthMsg('');
        }, 1200);
      }
    } catch {
      setAuthMsg('Login failed: Invalid credentials');
    }
  };

  const tabs = [
    { id: 'session', num: '01', label: '~/session.sh', title: 'Full Scout Session' },
    { id: 'translate', num: '02', label: '~/translate', title: 'Live Transfer Predictor' },
    { id: 'benchmarks', num: '03', label: '~/benchmarks', title: 'Empirical Transfer Archive' },
    { id: 'sandbox', num: '04', label: '~/sandbox', title: 'Counterfactual Simulator' },
    { id: 'interactive-cli', num: '05', label: '~/interactive-cli', title: 'Terminal REPL Shell' }
  ];

  return (
    <div className="terminal-window">
      {/* Title bar */}
      <div className="terminal-titlebar">
        <div className="titlebar-left">
          <div className="traffic-dots" title="Terminal Window Controls">
            <span className="dot dot-red" />
            <span className="dot dot-amber" />
            <span className="dot dot-green" />
          </div>

          <div className="terminal-path">
            <span className="path-user">scout@clptm</span>
            <span className="path-sep">:</span>
            <span className="path-dir">~/transfer-worth [PROD]</span>
          </div>
        </div>

        <div className="titlebar-right">
          {/* Quick Nav Links */}
          <div className="titlebar-nav">
            <button
              className={`nav-link-btn ${activeTab === 'translate' ? 'active' : ''}`}
              onClick={() => setActiveTab('translate')}
            >
              ~/translate
            </button>
            <button
              className={`nav-link-btn ${activeTab === 'benchmarks' ? 'active' : ''}`}
              onClick={() => setActiveTab('benchmarks')}
            >
              ~/benchmarks
            </button>
            <button
              className={`nav-link-btn ${activeTab === 'sandbox' ? 'active' : ''}`}
              onClick={() => setActiveTab('sandbox')}
            >
              ~/sandbox
            </button>
            <button
              className={`nav-link-btn ${activeTab === 'interactive-cli' ? 'active' : ''}`}
              onClick={() => setActiveTab('interactive-cli')}
            >
              ~/cli
            </button>
          </div>

          {/* User Role Badge */}
          <button
            className="nav-link-btn"
            style={{ fontSize: '11px', border: '1px solid var(--border-dim)' }}
            onClick={() => setShowAuthModal(true)}
            title="Switch User Role (viewer / admin)"
          >
            [{currentUserRole.toUpperCase()}]
          </button>

          {/* CRT scanlines toggle */}
          <button
            className="nav-link-btn"
            style={{ fontSize: '11px', border: '1px solid var(--border-dim)' }}
            onClick={() => setCrtScanlines(!crtScanlines)}
            title="Toggle CRT Scanline Overlay"
          >
            [CRT: {crtScanlines ? 'ON' : 'OFF'}]
          </button>

          {/* Online status indicator */}
          <div className="status-indicator" title={backendOnline ? "Connected to FastAPI @ :8000" : "Local Standalone Mode"}>
            <span className="status-blip" style={{ backgroundColor: backendOnline ? 'var(--phosphor-green)' : 'var(--amber-accent)' }} />
            <span>{backendOnline ? 'API CLUSTER ONLINE' : 'ML ENGINE ONLINE'}</span>
          </div>
        </div>
      </div>

      {/* Auth Modal */}
      {showAuthModal && (
        <div
          style={{
            background: 'var(--panel-bg-inset)',
            borderBottom: '1px solid var(--border-bright)',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '12px',
            gap: '12px',
            flexWrap: 'wrap'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="highlight-green">&gt; AUTH CONSOLE:</span>
            <span style={{ color: 'var(--text-secondary)' }}>
              Demo accounts: <code>viewer / viewer123</code> or <code>admin / admin123</code>
            </span>
          </div>

          <form onSubmit={handleAuthSubmit} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="text"
              className="form-input"
              style={{ width: '90px', padding: '4px 6px', fontSize: '11px' }}
              value={authUsername}
              onChange={(e) => setAuthUsername(e.target.value)}
              placeholder="user"
            />
            <input
              type="password"
              className="form-input"
              style={{ width: '90px', padding: '4px 6px', fontSize: '11px' }}
              value={authPassword}
              onChange={(e) => setAuthPassword(e.target.value)}
              placeholder="pass"
            />
            <button type="submit" className="btn-command-solid" style={{ padding: '4px 10px', fontSize: '11px' }}>
              LOGIN
            </button>
            <button
              type="button"
              className="nav-link-btn"
              onClick={() => setShowAuthModal(false)}
              style={{ border: '1px solid var(--border-dim)' }}
            >
              [X]
            </button>
          </form>

          {authMsg && <div className="glow" style={{ fontSize: '11px' }}>{authMsg}</div>}
        </div>
      )}

      {/* Terminal tab bar */}
      <div className="terminal-tabs-bar">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
            title={t.title}
          >
            <span className="tab-num">[{t.num}]</span>
            <span>{t.label}</span>
          </button>
        ))}
      </div>

      {/* Main Terminal Body */}
      {children}
    </div>
  );
};
