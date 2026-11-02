import React, { useState, useEffect, useRef } from 'react';
import {
  autoAuthenticate,
  fetchLeagues,
  fetchTeams,
  searchPlayers,
  predictTransfer
} from '../api/client';
import { simulatePrediction } from '../data/mockData';
import { getTeamCrest, getTeamLeague, LEAGUE_DEFAULT_TEAMS } from '../data/teamCrestMap';

export const PredictorSection = ({ onTransferContext, selectedTransfer }) => {
  const [leagues, setLeagues] = useState({});
  const [teams, setTeams] = useState([]);
  const [playerInput, setPlayerInput] = useState('Yan Diomandé');
  const [sourceLeague, setSourceLeague] = useState('Bundesliga');
  const [targetLeague, setTargetLeague] = useState('La Liga');
  const [targetTeam, setTargetTeam] = useState('Real Madrid');
  const [sourceTeam, setSourceTeam] = useState('RB Leipzig');

  const [searchResults, setSearchResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [predictionError, setPredictionError] = useState(null);
  const [apiOnline, setApiOnline] = useState(false);
  const [inferenceSource, setInferenceSource] = useState('connecting...');

  const searchTimerRef = useRef(null);

  // Sync when an external transfer is selected (e.g. from 2026/2027 Test Transfers tab)
  useEffect(() => {
    if (selectedTransfer) {
      setPlayerInput(selectedTransfer.player);
      if (selectedTransfer.source_league) setSourceLeague(selectedTransfer.source_league);
      if (selectedTransfer.target_league) setTargetLeague(selectedTransfer.target_league);
      if (selectedTransfer.target_team) setTargetTeam(selectedTransfer.target_team);
      if (selectedTransfer.source_team) setSourceTeam(selectedTransfer.source_team);
      runInference(
        selectedTransfer.player,
        selectedTransfer.source_league,
        selectedTransfer.target_league,
        selectedTransfer.target_team,
        selectedTransfer.source_team
      );
      const el = document.getElementById('predictor-section-anchor');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  }, [selectedTransfer]);

  // Authenticate and load leagues on mount
  useEffect(() => {
    autoAuthenticate().catch(() => {});

    fetchLeagues()
      .then((data) => {
        if (data && Object.keys(data).length > 0) {
          setLeagues(data);
          setApiOnline(true);
        }
      })
      .catch((err) => {
        console.warn('Leagues fetch fallback:', err.message);
        setLeagues({
          'Premier League': 1.0,
          'Bundesliga': 0.88,
          'La Liga': 0.93,
          'Serie A': 0.88,
          'Ligue 1': 0.82
        });
      });
  }, []);

  // Fetch teams whenever targetLeague changes
  useEffect(() => {
    if (!targetLeague) return;
    fetchTeams(targetLeague)
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setTeams(data);
          if (!data.some((t) => t.team === targetTeam)) {
            setTargetTeam(data[0].team);
          }
        }
      })
      .catch(() => {
        setTeams([
          { team: 'Manchester City', team_strength_ratio: 1.28 },
          { team: 'Arsenal', team_strength_ratio: 1.19 },
          { team: 'Liverpool', team_strength_ratio: 1.22 }
        ]);
      });
  }, [targetLeague]);

  // Live player search from database
  const handlePlayerInputChange = (e) => {
    const val = e.target.value;
    setPlayerInput(val);

    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    if (val.trim().length >= 2) {
      searchTimerRef.current = setTimeout(async () => {
        try {
          const results = await searchPlayers(val.trim(), '', 8);
          setSearchResults(results || []);
          setShowDropdown(true);
        } catch {
          setSearchResults([]);
        }
      }, 200);
    } else {
      setSearchResults([]);
      setShowDropdown(false);
    }
  };

  const handleSelectPlayer = (p) => {
    setPlayerInput(p.player);
    if (p.league) setSourceLeague(p.league);
    if (p.team) setSourceTeam(p.team);
    setShowDropdown(false);
    runInference(p.player, p.league || sourceLeague, targetLeague, targetTeam, p.team || sourceTeam);
  };

  // Run Inference against real backend
  const runInference = async (
    player = playerInput,
    src = sourceLeague,
    tgt = targetLeague,
    team = targetTeam,
    srcTeam = sourceTeam
  ) => {
    setLoading(true);
    setPredictionError(null);
    try {
      const data = await predictTransfer({
        player,
        source_league: src,
        target_league: tgt,
        target_team: team
      });

      if (data && data.projected_goals_p90 !== undefined) {
        setPredictionResult(data);
        setInferenceSource('FastAPI ML Engine (LightGBM + Bayesian Ridge)');
        setApiOnline(true);
        setLoading(false);
        // Emit transfer context for badge side panels
        if (onTransferContext) {
          onTransferContext({
            sourceTeam: data.source_team || srcTeam,
            targetTeam: data.target_team || team,
            sourceLeague: data.source_league || src,
            targetLeague: data.target_league || tgt,
          });
        }
        return;
      }
    } catch (err) {
      // Distinguish validation errors (400) from backend-offline errors
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;

      if (status === 400 && detail) {
        // Backend explicitly rejected: player not found, wrong league, etc.
        // NEVER fall through to mock data — show the real error.
        setPredictionResult(null);
        setPredictionError(detail);
        setInferenceSource('FastAPI ML Engine (LightGBM + Bayesian Ridge)');
        setLoading(false);
        return;
      }

      if (status && status >= 400 && status < 500) {
        // Other client errors (401 auth, 422 validation, etc.)
        setPredictionResult(null);
        setPredictionError(detail || `Request rejected (HTTP ${status}).`);
        setLoading(false);
        return;
      }

      // Only reach here on genuine network failure / backend offline / 5xx
      console.warn('Backend offline or server error:', err.message);
    }

    // Offline fallback: ONLY for verified preset players whose stats we know
    const fallbackData = simulatePrediction({
      player,
      source_league: src,
      target_league: tgt,
      target_team: team,
      team_strength: teams.find((t) => t.team === team)?.team_strength_ratio || 1.15
    });

    if (fallbackData) {
      setPredictionResult(fallbackData);
      setPredictionError(null);
      setInferenceSource('Offline Fallback (Verified Presets Only)');
      // Emit transfer context for badge side panels
      if (onTransferContext) {
        onTransferContext({
          sourceTeam: srcTeam,
          targetTeam: team,
          sourceLeague: src,
          targetLeague: tgt,
        });
      }
    } else {
      // Unknown player + backend offline = no data at all
      setPredictionResult(null);
      setPredictionError(
        `Cannot generate prediction for "${player}". ` +
        `The player was not found in the Big 5 European leagues dataset, ` +
        `and the backend ML engine is currently unreachable. ` +
        `Please try a verified player profile or ensure the backend is running.`
      );
      setInferenceSource('Disconnected');
    }
    setLoading(false);
  };

  // Run initial prediction on mount
  useEffect(() => {
    runInference();
  }, []);

  const starPresets = [
    { player: 'Yan Diomandé', team: 'RB Leipzig', src: 'Bundesliga', tgt: 'La Liga', club: 'Real Madrid', is2627: true },
    { player: 'Florian Wirtz', team: 'Leverkusen', src: 'Bundesliga', tgt: 'Premier League', club: 'Manchester City' },
    { player: 'Erling Haaland', team: 'Manchester City', src: 'Bundesliga', tgt: 'Premier League', club: 'Manchester City' },
    { player: 'Khvicha Kvaratskhelia', team: 'Napoli', src: 'Serie A', tgt: 'Premier League', club: 'Arsenal' },
    { player: 'Ciro Immobile', team: 'Lazio', src: 'Serie A', tgt: 'La Liga', club: 'Real Madrid' },
    { player: 'Jude Bellingham', team: 'Dortmund', src: 'Bundesliga', tgt: 'La Liga', club: 'Real Madrid' },
    { player: 'Victor Osimhen', team: 'Napoli', src: 'Serie A', tgt: 'Premier League', club: 'Chelsea' },
    { player: 'Michael Olise', team: 'Crystal Palace', src: 'Premier League', tgt: 'Bundesliga', club: 'Bayern Munich' }
  ];

  return (
    <section className="predictor-section" id="predictor-section-anchor">
      <div className="shell-prompt">
        <span className="prompt-host">clptm~/engine</span>
        <span className="prompt-symbol">$</span>
        <span className="prompt-cmd">./predict --target-eval</span>
        <span className="prompt-comment">
          # live model inference ({apiOnline ? 'BACKEND ONLINE' : 'STANDBY'})
        </span>
      </div>

      <div className="console-panel">
        <div className="section-meta-label">&gt; SCOUT INPUT FORM // PARAMETERS</div>
        <h3 className="section-heading">Cross-League Translation Configuration</h3>

        {/* Quick presets pills */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px' }}>
            VERIFIED PROFILES (REAL SAMPLES & 2026/2027 TEST CASES):
          </div>
          <div className="tag-pills-row">
            {starPresets.map((p) => (
              <button
                key={p.player}
                className={`tag-pill ${playerInput === p.player ? 'tag-pill-green' : ''}`}
                style={{
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                  borderColor: p.is2627 ? 'rgba(255, 176, 0, 0.6)' : undefined,
                  color: p.is2627 ? '#ffb000' : undefined
                }}
                onClick={() => {
                  setPlayerInput(p.player);
                  setSourceLeague(p.src);
                  setTargetLeague(p.tgt);
                  setTargetTeam(p.club);
                  setSourceTeam(p.team);
                  runInference(p.player, p.src, p.tgt, p.club, p.team);
                }}
              >
                {p.is2627 && (
                  <span style={{
                    background: 'rgba(255, 176, 0, 0.2)',
                    color: '#ffb000',
                    fontSize: '9px',
                    padding: '1px 5px',
                    borderRadius: '2px',
                    marginRight: '6px',
                    fontWeight: 700
                  }}>26/27 TEST</span>
                )}
                {playerInput === p.player ? '> ' : ''}{p.player} ({p.team})
              </button>
            ))}
          </div>
        </div>

        {/* Form Inputs Grid */}
        <div className="predictor-form-grid" style={{ position: 'relative' }}>
          {/* Player name with live database autocomplete */}
          <div className="form-group" style={{ position: 'relative' }}>
            <label className="form-label">Player Identity (Database Search)</label>
            <input
              type="text"
              className="form-input"
              value={playerInput}
              onChange={handlePlayerInputChange}
              onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
              placeholder="Search 5,690 players..."
            />

            {/* Autocomplete Dropdown */}
            {showDropdown && searchResults.length > 0 && (
              <div
                style={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  zIndex: 50,
                  background: 'var(--panel-bg-inset)',
                  border: '1px solid var(--border-bright)',
                  borderRadius: 'var(--radius-sm)',
                  boxShadow: '0 8px 24px rgba(0,0,0,0.8)',
                  maxHeight: '220px',
                  overflowY: 'auto'
                }}
              >
                {searchResults.map((p, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleSelectPlayer(p)}
                    style={{
                      padding: '8px 10px',
                      cursor: 'pointer',
                      borderBottom: '1px solid var(--border-dim)',
                      fontSize: '12px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(57, 255, 122, 0.08)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    <span className="highlight-white">{p.player}</span>
                    <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>
                      {p.team} | {p.league} ({p.position})
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Source League */}
          <div className="form-group">
            <label className="form-label">Source League (LSC)</label>
            <select
              className="form-select"
              value={sourceLeague}
              onChange={(e) => {
                const newLg = e.target.value;
                setSourceLeague(newLg);
                // Ensure sourceTeam belongs to this league
                const currentLg = getTeamLeague(sourceTeam);
                if (currentLg !== newLg) {
                  const defClub = LEAGUE_DEFAULT_TEAMS[newLg] || 'Napoli';
                  setSourceTeam(defClub);
                }
              }}
            >
              {Object.entries(leagues).map(([name, lsc]) => (
                <option key={name} value={name}>
                  {name} (LSC: {typeof lsc === 'number' ? lsc.toFixed(2) : lsc})
                </option>
              ))}
            </select>
          </div>

          {/* Target League */}
          <div className="form-group">
            <label className="form-label">Target League (LSC)</label>
            <select
              className="form-select"
              value={targetLeague}
              onChange={(e) => setTargetLeague(e.target.value)}
            >
              {Object.entries(leagues).map(([name, lsc]) => (
                <option key={name} value={name}>
                  {name} (LSC: {typeof lsc === 'number' ? lsc.toFixed(2) : lsc})
                </option>
              ))}
            </select>
          </div>

          {/* Target Team */}
          <div className="form-group">
            <label className="form-label">Destination Club (TRC)</label>
            <select
              className="form-select"
              value={targetTeam}
              onChange={(e) => setTargetTeam(e.target.value)}
            >
              {teams.map((t, idx) => (
                <option key={idx} value={t.team}>
                  {t.team} ({t.team_strength_ratio || 1.0}x strength)
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Action Button */}
        <div style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          <button
            className="btn-command-solid"
            onClick={() => runInference()}
            disabled={loading}
          >
            <span>{loading ? 'COMPUTING BACKEND INFERENCE...' : '$ RUN INFERENCE'}</span>
            <span>-&gt;</span>
          </button>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            [ENGINE: {inferenceSource}]
          </span>
        </div>

        {/* Error Banner */}
        {predictionError && !predictionResult && (
          <div
            className="output-deck"
            style={{
              borderColor: 'rgba(255, 70, 70, 0.4)',
              background: 'rgba(255, 30, 30, 0.06)',
            }}
          >
            <div className="output-banner" style={{ borderColor: 'rgba(255, 70, 70, 0.3)' }}>
              <div>
                <span style={{ color: '#ff4646', fontWeight: 700 }}>[INFERENCE REJECTED]</span>
                <span style={{ marginLeft: '10px', color: 'var(--text-primary)', fontWeight: 600 }}>
                  Player Not Found
                </span>
              </div>
              <div style={{ color: '#ff4646', fontSize: '11px' }}>
                STATUS: 400 BAD REQUEST
              </div>
            </div>
            <div style={{ padding: '16px 14px' }}>
              <div style={{
                fontSize: '13px',
                color: 'var(--text-secondary)',
                lineHeight: '1.7',
                padding: '12px 14px',
                background: 'rgba(255, 30, 30, 0.04)',
                border: '1px solid rgba(255, 70, 70, 0.15)',
                borderRadius: 'var(--radius-sm)',
              }}>
                <span style={{ color: '#ff6b6b', fontFamily: 'var(--font-mono, monospace)', fontSize: '11px' }}>
                  &gt; ERROR_DETAIL:
                </span>
                <p style={{ margin: '8px 0 0 0', color: 'var(--text-primary)' }}>
                  {predictionError}
                </p>
              </div>
              <div style={{ marginTop: '12px', fontSize: '11px', color: 'var(--text-muted)' }}>
                TIP: Use the database search above or select a verified player profile to run a valid prediction.
              </div>
            </div>
          </div>
        )}

        {/* Real Output Deck */}
        {predictionResult && (
          <div className="output-deck">
            {/* Banner */}
            <div className="output-banner">
              <div>
                <span className="highlight-green">[INFERENCE CONVERGED]</span>
                <span style={{ marginLeft: '10px', color: 'var(--text-primary)', fontWeight: 600 }}>
                  {predictionResult.player}
                </span>
                <span style={{ color: 'var(--text-muted)' }}>
                  {' '}({predictionResult.source_league} -&gt; {predictionResult.target_team || targetTeam} [{predictionResult.target_league}])
                </span>
              </div>
              <div style={{ color: 'var(--phosphor-dim)', fontSize: '11px' }}>
                LSC DELTA: {( (predictionResult.target_lsc || 1.0) - (predictionResult.source_lsc || 0.88) ).toFixed(3)}
              </div>
            </div>

            {/* Transfer Match-Up Vector Deck (Utilizes space with prominent, properly matched club crests) */}
            {(() => {
              const srcTeamDisplay = predictionResult.source_team || sourceTeam;
              const tgtTeamDisplay = predictionResult.target_team || targetTeam;
              const srcCrest = getTeamCrest(srcTeamDisplay);
              const tgtCrest = getTeamCrest(tgtTeamDisplay);
              const srcLgDisplay = getTeamLeague(srcCrest?.displayName) || predictionResult.source_league || sourceLeague;
              const tgtLgDisplay = getTeamLeague(tgtCrest?.displayName) || predictionResult.target_league || targetLeague;
              const deltaLsc = (predictionResult.target_lsc || 1.0) - (predictionResult.source_lsc || 0.88);

              return (
                <div className="transfer-matchup-deck">
                  {/* Origin Club */}
                  <div className="matchup-club-card matchup-origin-card">
                    <div className="matchup-role-tag">&gt; ORIGIN CLUB</div>
                    <div className="matchup-crest-frame">
                      {srcCrest?.url && (
                        <img
                          src={srcCrest.url}
                          alt={srcCrest.displayName}
                          className="matchup-crest-image"
                          onError={(e) => {
                            if (srcCrest.urlLight && e.target.src !== srcCrest.urlLight) {
                              e.target.src = srcCrest.urlLight;
                            }
                          }}
                        />
                      )}
                      <div className="matchup-crest-halo" />
                    </div>
                    <div className="matchup-club-details">
                      <span className="matchup-club-name">{srcCrest?.displayName || srcTeamDisplay}</span>
                      <span className="matchup-league-tag">{srcLgDisplay}</span>
                      <span className="matchup-coeff">
                        LSC: {typeof predictionResult.source_lsc === 'number' ? predictionResult.source_lsc.toFixed(2) : '0.88'}
                      </span>
                    </div>
                  </div>

                  {/* Direction & Metrics Vector */}
                  <div className="matchup-vector-column">
                    <div className="vector-hud-title">PERFORMANCE TRANSLATION VECTOR</div>
                    <div className="vector-stream-graphic">
                      <span className="vector-stream-dot" />
                      <div className="vector-stream-bar" />
                      <span className="vector-stream-arrow">►</span>
                    </div>
                    <div className="vector-badges-row">
                      <span className="vector-delta-pill">
                        DIFFICULTY {deltaLsc >= 0 ? `+${deltaLsc.toFixed(3)}` : deltaLsc.toFixed(3)}
                      </span>
                      <span className="vector-engine-pill">
                        {inferenceSource}
                      </span>
                    </div>
                  </div>

                  {/* Destination Club */}
                  <div className="matchup-club-card matchup-target-card">
                    <div className="matchup-role-tag">&gt; DESTINATION CLUB</div>
                    <div className="matchup-crest-frame">
                      {tgtCrest?.url && (
                        <img
                          src={tgtCrest.url}
                          alt={tgtCrest.displayName}
                          className="matchup-crest-image"
                          onError={(e) => {
                            if (tgtCrest.urlLight && e.target.src !== tgtCrest.urlLight) {
                              e.target.src = tgtCrest.urlLight;
                            }
                          }}
                        />
                      )}
                      <div className="matchup-crest-halo" />
                    </div>
                    <div className="matchup-club-details">
                      <span className="matchup-club-name">{tgtCrest?.displayName || tgtTeamDisplay}</span>
                      <span className="matchup-league-tag">{tgtLgDisplay}</span>
                      <span className="matchup-coeff">
                        TRC: {typeof predictionResult.target_team_strength_ratio === 'number' ? `${predictionResult.target_team_strength_ratio.toFixed(2)}x` : '1.19x'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Main Stats Grid */}
            <div className="stat-pills-grid">
              <div className="stat-box">
                <span className="stat-box-title">PROJECTED GOALS / 90</span>
                <span className="stat-box-value glow">
                  {typeof predictionResult.projected_goals_p90 === 'number'
                    ? predictionResult.projected_goals_p90.toFixed(3)
                    : 'N/A'}
                </span>
                <span className="stat-box-sub">
                  95% CI: [{predictionResult.ci_low_goals ?? 'N/A'} - {predictionResult.ci_high_goals ?? 'N/A'}]
                </span>
              </div>

              <div className="stat-box">
                <span className="stat-box-title">PROJECTED ASSISTS / 90</span>
                <span className="stat-box-value glow">
                  {typeof predictionResult.projected_assists_p90 === 'number'
                    ? predictionResult.projected_assists_p90.toFixed(3)
                    : 'N/A'}
                </span>
                <span className="stat-box-sub">Creation carry-over</span>
              </div>

              <div className="stat-box">
                <span className="stat-box-title">EXPECTED xG / 90</span>
                <span className="stat-box-value glow-white">
                  {typeof predictionResult.projected_xg_p90 === 'number'
                    ? predictionResult.projected_xg_p90.toFixed(3)
                    : 'N/A'}
                </span>
                <span className="stat-box-sub">Direct shot volume</span>
              </div>

              <div className="stat-box">
                <span className="stat-box-title">EXPECTED xAG / 90</span>
                <span className="stat-box-value glow-white">
                  {typeof predictionResult.projected_xag_p90 === 'number'
                    ? predictionResult.projected_xag_p90.toFixed(3)
                    : 'N/A'}
                </span>
                <span className="stat-box-sub">Expected assisted goals</span>
              </div>
            </div>

            {/* Secondary Advanced Tactical Stats Grid */}
            <div className="stat-pills-grid">
              <div className="stat-box">
                <span className="stat-box-title">ADAPTATION PROBABILITY</span>
                <span className={`stat-box-value ${predictionResult.adaptation_score_pct >= 60 ? 'glow' : 'glow-amber'}`}>
                  {predictionResult.adaptation_score_pct}%
                </span>
                <span className="stat-box-sub">
                  {predictionResult.adaptation_score_pct >= 60 ? 'High output retention' : 'Moderate adjustment curve'}
                </span>
              </div>

              <div className="stat-box">
                <span className="stat-box-title">DOWNSIDE RISK SCORE</span>
                <span className={`stat-box-value ${predictionResult.risk_score_pct <= 35 ? 'glow' : 'glow-amber'}`}>
                  {predictionResult.risk_score_pct}%
                </span>
                <span className="stat-box-sub">
                  {predictionResult.risk_score_pct <= 35 ? 'Low transfer risk' : 'Tactical scrutiny advised'}
                </span>
              </div>

              <div className="stat-box">
                <span className="stat-box-title">PROG PASSES / 90</span>
                <span className="stat-box-value glow-cyan">
                  {typeof predictionResult.projected_prog_passes_p90 === 'number'
                    ? Number(predictionResult.projected_prog_passes_p90).toFixed(2)
                    : 'N/A'}
                </span>
                <span className="stat-box-sub">Ball progression impact</span>
              </div>

              <div className="stat-box">
                <span className="stat-box-title">EXPECTED MINUTES</span>
                <span className="stat-box-value glow-white">
                  {typeof predictionResult.minutes_expectation === 'number'
                    ? Math.round(predictionResult.minutes_expectation)
                    : 'N/A'}
                </span>
                <span className="stat-box-sub">Projected playing time</span>
              </div>
            </div>

            {/* Real SHAP Feature Factors */}
            {predictionResult.top_5_factors && predictionResult.top_5_factors.length > 0 && (
              <div style={{ marginTop: '8px' }}>
                <div style={{ fontSize: '11px', color: 'var(--phosphor-dim)', marginBottom: '8px', textTransform: 'uppercase' }}>
                  &gt; SHAP IMPACT VECTORS // TOP 5 MODEL DRIVERS:
                </div>
                <div className="factors-list">
                  {predictionResult.top_5_factors.map((f, i) => {
                    const impactVal = f.shap_value !== undefined ? f.shap_value : f.impact;
                    const isPos = f.direction === 'positive' || (impactVal >= 0);
                    const label = f.label || f.feature;
                    return (
                      <div key={i} className="factor-item">
                        <span style={{ color: 'var(--text-secondary)' }}>
                          <span className="highlight-green">{i + 1}.</span> {label}
                        </span>
                        <span className={isPos ? 'factor-impact-pos' : 'factor-impact-neg'}>
                          {isPos ? `+${Number(impactVal).toFixed(4)}` : Number(impactVal).toFixed(4)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Real Tactical Fit & Archetype */}
            {predictionResult.tactical_fit && (
              <div
                style={{
                  marginTop: '12px',
                  padding: '12px 14px',
                  background: 'rgba(7, 11, 7, 0.8)',
                  border: '1px solid var(--border-bright)',
                  borderRadius: 'var(--radius-sm)'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span className="highlight-green">
                    &gt; TACTICAL ARCHETYPE: {predictionResult.tactical_fit.tactical_archetype || 'Dynamic Wide Playmaker'}
                  </span>
                  <span className="glow-amber" style={{ fontSize: '11px' }}>
                    FIT: {predictionResult.tactical_fit.compatibility_rating || '88.5% High Synergy'}
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                  {predictionResult.tactical_fit.compatibility_summary ||
                    'High tactical alignment with destination club attacking tempo and counter-pressing structure.'}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
};
