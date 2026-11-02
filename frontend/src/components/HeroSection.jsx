import React from 'react';

export const HeroSection = ({ onPredictClick, onScenarioClick }) => {
  return (
    <section className="hero-section">
      {/* Shell prompt prefix */}
      <div className="shell-prompt">
        <span className="prompt-host">clptm~/engine</span>
        <span className="prompt-symbol">$</span>
        <span className="prompt-cmd">whoami --full</span>
        <span className="prompt-comment"># system identity & model purpose</span>
      </div>

      {/* Main Name Banner scoped to class with explicit font-size */}
      <h1 className="hero-name-banner">
        TRANSFER_WORTH // CLPTM
        <span className="cursor-underscore">_</span>
      </h1>

      {/* Role line */}
      <div className="hero-role">
        &gt; Cross-League Performance Translation &amp; Tactical Transfer Intelligence
      </div>

      {/* Intro narrative */}
      <p className="hero-desc">
        A production-grade machine learning system solving the{' '}
        <span className="highlight-green">Haaland vs. Werner paradox</span>. When football
        players move between European leagues, naive carry-over fails due to defensive compactness,
        referee whistling, and teammate service. CLPTM predicts true output across Europe&apos;s
        Top 5 leagues using <span className="highlight-green">Tactical TRC club strength</span>,{' '}
        <span className="highlight-white">LightGBM regression</span>, and{' '}
        <span className="highlight-green">Bayesian 95% credible intervals</span>.
      </p>

      {/* ASCII bracket meta checks */}
      <div className="ascii-checks-wrap">
        <div className="ascii-check-item">
          <span className="ascii-bracket">[x]</span>
          <span>24,413 Standardized Player-Seasons</span>
        </div>
        <div className="ascii-check-item">
          <span className="ascii-bracket">[x]</span>
          <span>955 Calibrated Longitudinal Transfer Pairs</span>
        </div>
        <div className="ascii-check-item">
          <span className="ascii-bracket">[x]</span>
          <span>Big 5 Leagues (EPL, LaLiga, SerieA, Bundesliga, Ligue1)</span>
        </div>
        <div className="ascii-check-item">
          <span className="ascii-bracket">[x]</span>
          <span>Bayesian 95% Credible Bounds</span>
        </div>
        <div className="ascii-check-item">
          <span className="ascii-bracket">[x]</span>
          <span>Anti-Leakage Feature Pipeline</span>
        </div>
      </div>

      {/* Command CTA buttons */}
      <div className="cta-row">
        <button
          className="btn-command-solid"
          onClick={onPredictClick}
          title="Launch Live Player Translation Engine"
        >
          <span>$ ./predict --interactive</span>
          <span>-&gt;</span>
        </button>

        <button
          className="btn-command-ghost"
          onClick={onScenarioClick}
          title="Launch Counterfactual Sandbox"
        >
          <span>./run --scenario-sim</span>
        </button>
      </div>
    </section>
  );
};
