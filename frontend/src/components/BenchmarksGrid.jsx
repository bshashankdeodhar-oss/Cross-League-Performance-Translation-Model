import React, { useState, useEffect } from 'react';
import { fetchBenchmarks, fetchPredictionHistory, fetchTestTransfers } from '../api/client';
import { BENCHMARKS_CARDS } from '../data/mockData';

export const BenchmarksGrid = ({ onSelectTransfer }) => {
  const [testTransfers, setTestTransfers] = useState([]);
  const [testSearch, setTestSearch] = useState('');
  const [backtestRows, setBacktestRows] = useState([]);
  const [historyAudits, setHistoryAudits] = useState([]);
  const [activeView, setActiveView] = useState('testset'); // 'testset' | 'benchmarks' | 'audits'
  const [selectedAudit, setSelectedAudit] = useState(null);

  useEffect(() => {
    // Fetch 2026/2027 Season Test Transfers
    fetchTestTransfers(200)
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setTestTransfers(data);
        }
      })
      .catch((err) => console.warn('Test transfers fetch error:', err.message));

    // Fetch verified backtest transfers
    fetchBenchmarks(20)
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setBacktestRows(data);
        }
      })
      .catch((err) => console.warn('Benchmarks fetch error:', err.message));

    // Fetch database prediction audit logs
    fetchPredictionHistory(10)
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setHistoryAudits(data);
        }
      })
      .catch((err) => console.warn('History fetch error:', err.message));
  }, []);

  const filteredTestTransfers = testTransfers.filter((t) => {
    if (!testSearch.trim()) return true;
    const kw = testSearch.toLowerCase();
    return (
      t.player?.toLowerCase().includes(kw) ||
      t.moving_from?.toLowerCase().includes(kw) ||
      t.moving_to?.toLowerCase().includes(kw) ||
      t.source_league?.toLowerCase().includes(kw) ||
      t.target_league?.toLowerCase().includes(kw)
    );
  });

  return (
    <section className="benchmarks-section">
      <div className="shell-prompt">
        <span className="prompt-host">clptm~/engine</span>
        <span className="prompt-symbol">$</span>
        <span className="prompt-cmd">ls -la ~/transfers/2026-2027</span>
        <span className="prompt-comment">
          # 2026/27 empirical test suite ({testTransfers.length} verified future transfers)
        </span>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <div className="section-meta-label">&gt; EMPIRICAL TEST SUITE & ARCHIVES // 2026/2027</div>
          <h3 className="section-heading" style={{ margin: 0 }}>
            Transfer Test Suite & Benchmarks // drwxr-xr-x
          </h3>
        </div>

        {/* Toggle between 26/27 test transfers, historic backtest and live db audits */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button
            className={`nav-link-btn ${activeView === 'testset' ? 'active' : ''}`}
            onClick={() => setActiveView('testset')}
            style={{ fontSize: '11.5px' }}
          >
            [26/27 TEST SET ({testTransfers.length})]
          </button>
          <button
            className={`nav-link-btn ${activeView === 'benchmarks' ? 'active' : ''}`}
            onClick={() => setActiveView('benchmarks')}
            style={{ fontSize: '11.5px' }}
          >
            [HISTORICAL CASE STUDIES]
          </button>
          <button
            className={`nav-link-btn ${activeView === 'audits' ? 'active' : ''}`}
            onClick={() => setActiveView('audits')}
            style={{ fontSize: '11.5px' }}
          >
            [LIVE DB AUDITS ({historyAudits.length})]
          </button>
        </div>
      </div>

      {/* 2026/2027 Season Test Transfers View */}
      {activeView === 'testset' && (
        <div>
          <div style={{ marginBottom: '16px', display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '240px' }}>
              <input
                type="text"
                className="form-input"
                value={testSearch}
                onChange={(e) => setTestSearch(e.target.value)}
                placeholder="Search 191 verified 26/27 transfers (e.g. Diomandé, Real Madrid, Leipzig, Chelsea)..."
                style={{ fontSize: '12px' }}
              />
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Showing {filteredTestTransfers.length} of {testTransfers.length} verified future transfers
            </div>
          </div>

          <div className="benchmarks-grid">
            {filteredTestTransfers.slice(0, 30).map((t, idx) => {
              const isMarquee = t.player?.toLowerCase().includes('diomand');
              return (
                <div
                  key={`${t.player}-${idx}`}
                  className="benchmark-card"
                  style={isMarquee ? {
                    borderColor: 'rgba(255, 176, 0, 0.7)',
                    background: 'radial-gradient(ellipse at top left, rgba(255, 176, 0, 0.08) 0%, var(--panel-bg-subtle) 70%)',
                    boxShadow: '0 0 15px rgba(255, 176, 0, 0.15)'
                  } : undefined}
                >
                  <div className="card-header-baseline">
                    <div className="card-filename" style={{ color: isMarquee ? '#ffb000' : undefined }}>
                      {t.player}
                      <span className="card-filename-slash" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                        {' '}({t.position || 'FW'}, {t.age}y)
                      </span>
                    </div>
                    <div className="card-stats-right">
                      {isMarquee ? (
                        <span className="tag-pill tag-pill-amber" style={{ fontSize: '9px', padding: '1px 5px' }}>
                          MARQUEE TEST
                        </span>
                      ) : (
                        <span className="card-stars">26/27 TEST</span>
                      )}
                    </div>
                  </div>

                  <p className="card-desc" style={{ marginTop: '8px', marginBottom: '8px' }}>
                    <span className="highlight-white">{t.moving_from}</span>{' '}
                    <span style={{ color: 'var(--text-muted)' }}>({t.source_league})</span>
                    {'  ->  '}
                    <span className="highlight-green">{t.moving_to}</span>{' '}
                    <span style={{ color: 'var(--text-muted)' }}>({t.target_league})</span>
                  </p>

                  <div className="tag-pills-row" style={{ marginBottom: '10px' }}>
                    <span className="tag-pill">xG/90: {t.xg_p90}</span>
                    <span className="tag-pill">G/90: {t.goals_p90}</span>
                    <span className="tag-pill">ProgP/90: {t.prog_passes_p90}</span>
                    <span className="tag-pill tag-pill-amber" style={{ fontSize: '10px' }}>
                      {t.fee || 'Summer 2026'}
                    </span>
                  </div>

                  <div className="card-links-row">
                    <button
                      className="nav-link-btn card-link"
                      style={{ color: isMarquee ? '#ffb000' : 'var(--phosphor-green)' }}
                      onClick={() => {
                        if (onSelectTransfer) {
                          onSelectTransfer({
                            player: t.player,
                            source_league: t.source_league,
                            target_league: t.target_league,
                            target_team: t.moving_to,
                            source_team: t.moving_from
                          });
                        }
                      }}
                    >
                      <span className="card-link-arrow">-&gt;</span>
                      <span>[LOAD INTO SCOUT & PREDICT]</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {filteredTestTransfers.length > 30 && (
            <div style={{ textAlign: 'center', marginTop: '14px', fontSize: '11px', color: 'var(--text-muted)' }}>
              Showing top 30 matching transfers. Refine search above to pinpoint any of the 191 dataset transfers.
            </div>
          )}
        </div>
      )}

      {/* Case Studies View */}
      {activeView === 'benchmarks' && (
        <div className="benchmarks-grid">
          {BENCHMARKS_CARDS.map((card) => {
            // Check if there's real backtest data match
            const realMatch = backtestRows.find((r) =>
              card.desc.toLowerCase().includes(r.player.toLowerCase())
            );

            return (
              <div key={card.id} className="benchmark-card">
                {/* Top baseline row: filename left, stars + perms right */}
                <div className="card-header-baseline">
                  <div className="card-filename">
                    {card.name}
                    <span className="card-filename-slash">/</span>
                  </div>
                  <div className="card-stats-right">
                    <span className="card-stars">{card.stars}</span>
                    <span className="card-perms">{card.perms}</span>
                  </div>
                </div>

                {/* Description */}
                <p className="card-desc">
                  {card.desc.split(card.highlight).map((part, idx, arr) => (
                    <React.Fragment key={idx}>
                      {part}
                      {idx < arr.length - 1 && (
                        <span className="highlight-green">{card.highlight}</span>
                      )}
                    </React.Fragment>
                  ))}
                </p>

                {/* Tags row with exactly one amber tag */}
                <div className="tag-pills-row">
                  {card.tags.map((t, idx) => (
                    <span key={idx} className="tag-pill">
                      {t}
                    </span>
                  ))}
                  <span className="tag-pill tag-pill-amber">{card.amberTag}</span>
                  {realMatch && (
                    <span className="tag-pill tag-pill-green">
                      Backtest MAE: {realMatch.error}
                    </span>
                  )}
                </div>

                {/* Links row */}
                <div className="card-links-row">
                  <button
                    className="nav-link-btn card-link"
                    onClick={() => setSelectedAudit({
                      name: card.name,
                      actual_goals: realMatch ? realMatch.actual : card.stats.actual_goals,
                      predicted_goals: realMatch ? realMatch.predicted : card.stats.predicted_goals,
                      mae: realMatch ? realMatch.error : card.stats.mae,
                      source: 'evaluation/backtest_report.csv'
                    })}
                  >
                    <span className="card-link-arrow">-&gt;</span>
                    <span>{card.demoText}</span>
                  </button>
                  <button
                    className="nav-link-btn card-link"
                    style={{ color: 'var(--text-secondary)' }}
                    onClick={() => setSelectedAudit({
                      name: card.name,
                      actual_goals: realMatch ? realMatch.actual : card.stats.actual_goals,
                      predicted_goals: realMatch ? realMatch.predicted : card.stats.predicted_goals,
                      mae: realMatch ? realMatch.error : card.stats.mae,
                      source: 'Database TransferPrediction Audit Table'
                    })}
                  >
                    <span className="card-link-arrow">-&gt;</span>
                    <span>{card.sourceText}</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Live DB Audits View */}
      {activeView === 'audits' && (
        <div className="console-panel" style={{ background: 'var(--panel-bg-inset)' }}>
          {historyAudits.length === 0 ? (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>
              No audit records logged yet. Run a prediction to automatically log an audit in TransferPrediction table.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr 1fr 1.2fr', fontSize: '11px', color: 'var(--phosphor-dim)', paddingBottom: '6px', borderBottom: '1px solid var(--border-dim)' }}>
                <span>PLAYER</span>
                <span>DESTINATION</span>
                <span>PROJECTED G/90</span>
                <span>ADAPTATION</span>
                <span>TIMESTAMP</span>
              </div>
              {historyAudits.map((a, i) => (
                <div
                  key={i}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1.2fr 1fr 1fr 1fr 1.2fr',
                    fontSize: '12px',
                    padding: '6px 0',
                    borderBottom: '1px dashed rgba(20, 54, 20, 0.5)'
                  }}
                >
                  <span className="highlight-white">{a.player}</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{a.target_league}</span>
                  <span className="glow">{a.projected_goals_p90}</span>
                  <span className="glow-amber">{a.adaptation_score_pct}%</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                    {a.created_at ? new Date(a.created_at).toLocaleTimeString() : 'Recent'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Audit inspect modal / panel */}
      {selectedAudit && (
        <div
          className="console-panel"
          style={{
            marginTop: '18px',
            border: '1px solid var(--border-bright)',
            background: 'var(--panel-bg-inset)'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <span className="highlight-green">
              &gt; AUDIT LOG VERIFICATION: {selectedAudit.name}
            </span>
            <button
              className="nav-link-btn"
              onClick={() => setSelectedAudit(null)}
              style={{ border: '1px solid var(--border-dim)' }}
            >
              [ESC / CLOSE]
            </button>
          </div>
          <div style={{ fontSize: '12px', lineHeight: '1.6', color: 'var(--text-secondary)' }}>
            <div>
              <span className="highlight-white">Actual Outcome:</span> {selectedAudit.actual_goals} Goals/90
              {'  |  '}
              <span className="highlight-white">CLPTM Projected:</span> {selectedAudit.predicted_goals} Goals/90
              {'  |  '}
              <span className="glow">Backtest Delta MAE:</span> {selectedAudit.mae}
            </div>
            <div style={{ marginTop: '6px', color: 'var(--text-muted)' }}>
              Source: {selectedAudit.source} // Calibrated against multi-season FBRef Big 5 records.
            </div>
          </div>
        </div>
      )}
    </section>
  );
};
