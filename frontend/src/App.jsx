import React, { useState } from 'react';
import { TerminalFrame } from './components/TerminalFrame';
import { HeroSection } from './components/HeroSection';
import { NeofetchCard } from './components/NeofetchCard';
import { PredictorSection } from './components/PredictorSection';
import { BenchmarksGrid } from './components/BenchmarksGrid';
import { MetricsMeter } from './components/MetricsMeter';
import { ScenarioSandbox } from './components/ScenarioSandbox';
import { InteractiveRepl } from './components/InteractiveRepl';
import { ContactPanel } from './components/ContactPanel';
import { TerminalFooter } from './components/TerminalFooter';
import { BadgeSidePanels } from './components/BadgeSidePanels';

export function App() {
  const [activeTab, setActiveTab] = useState('session');
  const [crtScanlines, setCrtScanlines] = useState(true);
  const [transferContext, setTransferContext] = useState(null);
  const [selectedTransfer, setSelectedTransfer] = useState(null);

  return (
    <div className="app-root">
      {/* Fixed CRT Scanlines Overlay */}
      {crtScanlines && <div className="crt-overlay" />}
      {/* CRT Corner Vignette */}
      <div className="crt-vignette" />

      {/* Floating Club Badge Side Panels (outside terminal, in the gutters) */}
      <BadgeSidePanels transferContext={transferContext} />

      {/* Main Terminal Shell Viewport */}
      <main className="crt-viewport">
        <TerminalFrame
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          crtScanlines={crtScanlines}
          setCrtScanlines={setCrtScanlines}
        >
          {/* Tab 1: Full Continuous Session */}
          {activeTab === 'session' && (
            <div className="terminal-body">
              <HeroSection
                onPredictClick={() => setActiveTab('translate')}
                onScenarioClick={() => setActiveTab('sandbox')}
              />

              <hr className="terminal-rule" />

              <NeofetchCard />

              <hr className="terminal-rule" />

              <PredictorSection
                onTransferContext={setTransferContext}
                selectedTransfer={selectedTransfer}
              />

              <hr className="terminal-rule" />

              <BenchmarksGrid onSelectTransfer={setSelectedTransfer} />

              <hr className="terminal-rule" />

              <MetricsMeter />

              <hr className="terminal-rule" />

              <ContactPanel />
            </div>
          )}

          {/* Tab 2: Dedicated Live Transfer Predictor */}
          {activeTab === 'translate' && (
            <div className="terminal-body">
              <PredictorSection
                onTransferContext={setTransferContext}
                selectedTransfer={selectedTransfer}
              />
              <hr className="terminal-rule" />
              <BenchmarksGrid onSelectTransfer={setSelectedTransfer} />
            </div>
          )}

          {/* Tab 3: Empirical Transfer Archive */}
          {activeTab === 'benchmarks' && (
            <div className="terminal-body">
              <BenchmarksGrid
                onSelectTransfer={(t) => {
                  setSelectedTransfer(t);
                  setActiveTab('translate');
                }}
              />
              <hr className="terminal-rule" />
              <MetricsMeter />
            </div>
          )}

          {/* Tab 4: Counterfactual Scenario Sandbox */}
          {activeTab === 'sandbox' && (
            <div className="terminal-body">
              <ScenarioSandbox />
            </div>
          )}

          {/* Tab 5: Live Interactive Terminal Shell / REPL */}
          {activeTab === 'interactive-cli' && (
            <div className="terminal-body">
              <InteractiveRepl />
              <hr className="terminal-rule" />
              <NeofetchCard />
            </div>
          )}

          {/* Terminal Footer */}
          <TerminalFooter />
        </TerminalFrame>
      </main>
    </div>
  );
}

export default App;

