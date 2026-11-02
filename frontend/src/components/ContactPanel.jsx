import React, { useState } from 'react';

export const ContactPanel = () => {
  const [copied, setCopied] = useState(false);
  const emailText = 'scout@transferworth.ai';

  const handleCopy = () => {
    navigator.clipboard?.writeText(emailText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };

  return (
    <section className="contact-section">
      <div className="shell-prompt">
        <span className="prompt-host">clptm~/engine</span>
        <span className="prompt-symbol">$</span>
        <span className="prompt-cmd">./contact --scout-desk</span>
        <span className="prompt-comment"># quantitative football research inquiry</span>
      </div>

      <div
        className="console-panel"
        style={{
          textAlign: 'center',
          padding: '36px 20px',
          background: 'linear-gradient(180deg, rgba(7, 11, 7, 0.9) 0%, rgba(3, 5, 3, 0.95) 100%)',
          border: '1px solid var(--border-bright)'
        }}
      >
        <h2
          style={{
            fontSize: 'clamp(1.5rem, 3.2vw, 28px)',
            color: 'var(--text-primary)',
            fontWeight: 700,
            marginBottom: '10px',
            letterSpacing: '-0.02em'
          }}
        >
          Let&apos;s translate <span className="glow">player potential together.</span>
        </h2>

        <p
          style={{
            maxWidth: '560px',
            margin: '0 auto 24px auto',
            color: 'var(--text-secondary)',
            fontSize: '13.5px',
            lineHeight: 1.6
          }}
        >
          Open for collaborative football analytics, club data integration, API licensing,
          and bespoke tactical carry-over models.
        </p>

        {/* Copyable Command Box with live blinking green block caret */}
        <div style={{ marginBottom: '26px' }}>
          <div
            className="command-box-copyable"
            onClick={handleCopy}
            title="Click to copy email address"
          >
            <span style={{ color: 'var(--phosphor-green)', fontWeight: 700 }}>$</span>
            <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
              mail {emailText}
            </span>
            <span className="cursor-block" />
            <span style={{ fontSize: '11px', color: copied ? 'var(--phosphor-green)' : 'var(--text-muted)', marginLeft: '8px' }}>
              {copied ? '[COPIED TO CLIPBOARD!]' : '[CLICK TO COPY]'}
            </span>
          </div>
        </div>

        {/* Social / Link Pills */}
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '12px',
            flexWrap: 'wrap'
          }}
        >
          <a
            href="https://github.com/bshashankdeodhar-oss/Cross-League-Performance-Translation-Model"
            target="_blank"
            rel="noreferrer"
            className="tag-pill tag-pill-green"
            style={{ textDecoration: 'none', padding: '6px 12px', fontSize: '12px' }}
          >
            -&gt; github/clptm
          </a>
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="tag-pill"
            style={{ textDecoration: 'none', padding: '6px 12px', fontSize: '12px' }}
          >
            -&gt; api-docs (/docs)
          </a>
          <span
            className="tag-pill"
            style={{ padding: '6px 12px', fontSize: '12px', color: 'var(--text-secondary)' }}
          >
            -&gt; presentation.pptx
          </span>
          <span
            className="tag-pill tag-pill-amber"
            style={{ padding: '6px 12px', fontSize: '12px' }}
          >
            -&gt; CLPTM_Whitepaper.pdf
          </span>
        </div>
      </div>
    </section>
  );
};
