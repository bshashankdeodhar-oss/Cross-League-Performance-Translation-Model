import React from 'react';

export const TerminalFooter = () => {
  return (
    <footer className="terminal-footer">
      <div className="footer-left">
        <span style={{ color: 'var(--phosphor-green)', fontWeight: 700 }}>$</span>
        <span>
          echo &quot;(c) 2026 CLPTM TransferWorth // Cross-League Machine Learning Engine, shipped fast&quot;
        </span>
        <span className="cursor-block" style={{ width: '6px', height: '12px' }} />
      </div>

      <div className="footer-right">
        <span>last commit: 2h ago, main@a1f9e2c, uptime 99.98%</span>
      </div>
    </footer>
  );
};
