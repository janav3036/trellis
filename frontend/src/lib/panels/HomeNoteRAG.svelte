<script>
  import { onMount } from 'svelte';

  let totalChunks = 0;
  let displayed   = 0;

  onMount(async () => {
    try {
      const res  = await fetch('/api/noterag/status');
      const data = await res.json();
      totalChunks = data.total_chunks || 0;

      const duration = 1100;
      const start    = performance.now();
      const tick = (now) => {
        const p   = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        displayed = Math.round(eased * totalChunks);
        if (p < 1) requestAnimationFrame(tick);
        else displayed = totalChunks;
      };
      requestAnimationFrame(tick);
    } catch {}
  });

  const HINTS = [
    'What did I dream?',
    'Habits this week',
    'Movies watched',
    'Music lately',
  ];
</script>

<div class="panel">
  <div class="accent-line"></div>

  <div class="hdr">
    <div class="hdr-left">
      <span class="pulse-dot"></span>
      <span class="lbl">NoteRAG</span>
    </div>
    <a href="/#/chat" class="open-link">chat →</a>
  </div>

  <div class="body">
    <div class="stat">
      <span class="num">{displayed.toLocaleString()}</span>
      <span class="unit">memory chunks</span>
    </div>

    <div class="hints">
      {#each HINTS as h, i}
        <span class="hint" style="--d:{i * 90}ms">{h}</span>
      {/each}
    </div>
  </div>

  <div class="wave-wrap">
    <svg width="100%" height="28" preserveAspectRatio="none" viewBox="0 0 300 28">
      <path
        d="M0,14 Q37,2 75,14 Q112,26 150,14 Q187,2 225,14 Q262,26 300,14"
        fill="none" stroke="rgba(200,169,122,0.2)" stroke-width="1.5"
      />
      <path
        d="M0,18 Q50,8 100,18 Q150,28 200,18 Q250,8 300,18"
        fill="none" stroke="rgba(200,169,122,0.07)" stroke-width="1"
      />
    </svg>
  </div>
</div>

<style>
  .panel {
    height: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px 10px;
    display: flex;
    flex-direction: column;
    gap: 0;
    position: relative;
    overflow: hidden;
  }

  .accent-line {
    position: absolute;
    left: 0; top: 18%; bottom: 18%;
    width: 2px;
    background: linear-gradient(to bottom, transparent, var(--accent), transparent);
    opacity: 0.45;
    border-radius: 0 2px 2px 0;
  }

  /* ── header ── */
  .hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
    margin-bottom: 10px;
  }

  .hdr-left { display: flex; align-items: center; gap: 7px; }

  .pulse-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
    opacity: 0.75;
    animation: breathe 2.8s ease-in-out infinite;
  }

  @keyframes breathe {
    0%, 100% { opacity: 0.75; transform: scale(1); }
    50%       { opacity: 1;    transform: scale(1.25); }
  }

  .lbl {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.67rem;
    font-weight: 500;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    color: var(--text-secondary);
  }

  .open-link {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.64rem;
    color: var(--text-secondary);
    text-decoration: none;
    opacity: 0.38;
    letter-spacing: 0.03em;
    transition: opacity 0.15s;
  }
  .open-link:hover { opacity: 0.9; }

  /* ── body ── */
  .body {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
    justify-content: center;
  }

  .stat {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .num {
    font-family: 'Raleway', sans-serif;
    font-weight: 200;
    font-size: 2.5rem;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    line-height: 1;
  }

  .unit {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.61rem;
    color: var(--text-secondary);
    opacity: 0.4;
    letter-spacing: 0.09em;
    text-transform: uppercase;
  }

  .hints {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }

  .hint {
    padding: 3px 9px;
    border-radius: 20px;
    border: 1px solid rgba(200, 169, 122, 0.1);
    background: rgba(200, 169, 122, 0.03);
    color: #504438;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.63rem;
    letter-spacing: 0.01em;
    animation: fadeUp 0.4s ease both;
    animation-delay: var(--d, 0ms);
  }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* ── wave ── */
  .wave-wrap {
    flex-shrink: 0;
    margin-top: 4px;
    opacity: 0.7;
  }
</style>
