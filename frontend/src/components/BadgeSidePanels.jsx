import React, { useState, useEffect } from 'react';
import { getTeamCrest, getTeamLeague } from '../data/teamCrestMap';

/**
 * BadgeSidePanels
 *
 * Fixed-position floating telemetry panels on the left and right gutters of the viewport.
 * Left = source team crest & stats, Right = destination team crest & stats.
 * Appears with a CRT glitch-in animation after a prediction is made.
 *
 * @param {{ transferContext: { sourceTeam: string, targetTeam: string, sourceLeague: string, targetLeague: string } | null }} props
 */
export const BadgeSidePanels = ({ transferContext }) => {
  const [visible, setVisible] = useState(false);
  const [animKey, setAnimKey] = useState(0);

  // When transfer context changes, trigger the glitch-in animation
  useEffect(() => {
    if (transferContext?.sourceTeam || transferContext?.targetTeam) {
      setVisible(false);
      const timer = setTimeout(() => {
        setAnimKey((k) => k + 1);
        setVisible(true);
      }, 150);
      return () => clearTimeout(timer);
    } else {
      setVisible(false);
    }
  }, [transferContext?.sourceTeam, transferContext?.targetTeam]);

  const source = transferContext?.sourceTeam
    ? getTeamCrest(transferContext.sourceTeam)
    : null;
  const target = transferContext?.targetTeam
    ? getTeamCrest(transferContext.targetTeam)
    : null;

  // Resolve true canonical leagues for display
  const sourceLeague = (source?.displayName && getTeamLeague(source.displayName)) || transferContext?.sourceLeague;
  const targetLeague = (target?.displayName && getTeamLeague(target.displayName)) || transferContext?.targetLeague;

  return (
    <>
      {/* Left Panel — Source Team */}
      <aside
        className={`badge-side-panel badge-side-left ${visible && source?.url ? 'badge-visible' : ''}`}
        key={`src-${animKey}`}
        aria-label="Source Club Badge"
      >
        <div className="badge-corner badge-corner-tl" />
        <div className="badge-corner badge-corner-tr" />
        <div className="badge-corner badge-corner-bl" />
        <div className="badge-corner badge-corner-br" />

        {source?.url ? (
          <>
            <div className="badge-label-top">
              <span className="badge-dot badge-dot-origin" />
              ORIGIN CLUB
            </div>

            <div className="badge-crest-wrapper">
              <img
                className="badge-crest-img"
                src={source.url}
                alt={source.displayName}
                loading="eager"
                onError={(e) => {
                  if (source.urlLight && e.target.src !== source.urlLight) {
                    e.target.src = source.urlLight;
                  } else {
                    e.target.style.display = 'none';
                  }
                }}
              />
              <div className="badge-crest-glow" />
            </div>

            <div className="badge-team-name">{source.displayName}</div>

            {sourceLeague && (
              <div className="badge-league-chip">
                {sourceLeague}
              </div>
            )}

            <div className="badge-status-row">
              <span className="badge-status-text">TRANSLATION ORIGIN</span>
              <span className="badge-direction-arrow badge-arrow-right">→</span>
            </div>
          </>
        ) : (
          <div className="badge-ghost-shield">
            <svg viewBox="0 0 100 120" className="badge-ghost-svg">
              <path
                d="M50 5 L90 25 L90 65 Q90 100 50 115 Q10 100 10 65 L10 25 Z"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeDasharray="4 3"
              />
            </svg>
            <div className="badge-ghost-text">AWAITING INPUT</div>
          </div>
        )}
      </aside>

      {/* Right Panel — Target Team */}
      <aside
        className={`badge-side-panel badge-side-right ${visible && target?.url ? 'badge-visible' : ''}`}
        key={`tgt-${animKey}`}
        aria-label="Target Club Badge"
      >
        <div className="badge-corner badge-corner-tl" />
        <div className="badge-corner badge-corner-tr" />
        <div className="badge-corner badge-corner-bl" />
        <div className="badge-corner badge-corner-br" />

        {target?.url ? (
          <>
            <div className="badge-label-top">
              <span className="badge-dot badge-dot-target" />
              DESTINATION CLUB
            </div>

            <div className="badge-crest-wrapper">
              <img
                className="badge-crest-img"
                src={target.url}
                alt={target.displayName}
                loading="eager"
                onError={(e) => {
                  if (target.urlLight && e.target.src !== target.urlLight) {
                    e.target.src = target.urlLight;
                  } else {
                    e.target.style.display = 'none';
                  }
                }}
              />
              <div className="badge-crest-glow" />
            </div>

            <div className="badge-team-name">{target.displayName}</div>

            {targetLeague && (
              <div className="badge-league-chip">
                {targetLeague}
              </div>
            )}

            <div className="badge-status-row">
              <span className="badge-direction-arrow badge-arrow-left">←</span>
              <span className="badge-status-text">TARGET SECTOR</span>
            </div>
          </>
        ) : (
          <div className="badge-ghost-shield">
            <svg viewBox="0 0 100 120" className="badge-ghost-svg">
              <path
                d="M50 5 L90 25 L90 65 Q90 100 50 115 Q10 100 10 65 L10 25 Z"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeDasharray="4 3"
              />
            </svg>
            <div className="badge-ghost-text">AWAITING INFERENCE</div>
          </div>
        )}
      </aside>
    </>
  );
};
