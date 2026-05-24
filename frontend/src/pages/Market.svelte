<script>
  import { onMount, onDestroy } from "svelte";

  let heartbeat = {};
  let fearScore = null, vix = null;
  let sectors = {};
  let crypto = {};
  let now = new Date();
  let clockInterval;

  const INDEX_COLORS = {
    "S&P 500": "#c8813a",
    "Nikkei":  "#4dabf7",
    "DAX":     "#69db7c",
    "FTSE":    "#f783ac",
  };

  function toPolyline(pcts, w = 600, h = 160, pad = 12) {
    if (!pcts || pcts.length < 2) return "";
    const minV = Math.min(...pcts), maxV = Math.max(...pcts), range = maxV - minV || 1;
    return pcts.map((v, i) => {
      const x = pad + (i / (pcts.length - 1)) * (w - pad * 2);
      const y = (h - pad) - ((v - minV) / range) * (h - pad * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");
  }

  function toAreaD(pcts, w = 600, h = 160, pad = 12) {
    if (!pcts || pcts.length < 2) return "";
    const minV = Math.min(...pcts), maxV = Math.max(...pcts), range = maxV - minV || 1;
    const pts = pcts.map((v, i) => {
      const x = pad + (i / (pcts.length - 1)) * (w - pad * 2);
      const y = (h - pad) - ((v - minV) / range) * (h - pad * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    const first = pts[0].split(","), last = pts[pts.length - 1].split(",");
    return `M ${pts[0]} ` + pts.slice(1).map(p => `L ${p}`).join(" ") +
      ` L ${last[0]},${h - pad} L ${first[0]},${h - pad} Z`;
  }

  function lastDot(pcts, w = 600, h = 160, pad = 12) {
    if (!pcts?.length) return null;
    const minV = Math.min(...pcts), maxV = Math.max(...pcts), range = maxV - minV || 1;
    const i = pcts.length - 1, v = pcts[i];
    const x = pad + (i / (pcts.length - 1)) * (w - pad * 2);
    const y = (h - pad) - ((v - minV) / range) * (h - pad * 2);
    return { x: x.toFixed(1), y: y.toFixed(1) };
  }

  function buildArcPath(cx, cy, r, startDeg, endDeg) {
    const s = startDeg * Math.PI / 180;
    const e = endDeg * Math.PI / 180;
    const x1 = cx + r * Math.cos(s), y1 = cy + r * Math.sin(s);
    const x2 = cx + r * Math.cos(e), y2 = cy + r * Math.sin(e);
    const sweep = ((endDeg - startDeg) % 360 + 360) % 360;
    const large = sweep > 180 ? 1 : 0;
    return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${r} ${r} 0 ${large} 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
  }

  $: gaugeTrack = buildArcPath(110, 90, 65, 135, 405);
  $: gaugeFill = (fearScore !== null && fearScore > 0)
    ? buildArcPath(110, 90, 65, 135, 135 + (fearScore / 100) * 270)
    : "";
  $: gaugeColor = fearScore === null ? "#3a3530"
    : fearScore > 50
      ? `rgba(200,129,58,${0.6 + (fearScore - 50) / 100})`
      : `rgba(77,171,247,${0.6 + (50 - fearScore) / 100})`;
  $: fearLabel = fearScore === null ? "—"
    : fearScore > 80 ? "Extreme Greed"
    : fearScore > 60 ? "Greed"
    : fearScore > 40 ? "Neutral"
    : fearScore > 20 ? "Fear"
    : "Extreme Fear";

  $: sectorBars = (() => {
    const entries = Object.entries(sectors);
    if (!entries.length) return [];
    const maxAbs = Math.max(...entries.map(([, v]) => Math.abs(v))) || 1;
    return entries
      .sort((a, b) => b[1] - a[1])
      .map(([name, pct]) => ({ name, pct, w: Math.abs(pct) / maxAbs, pos: pct >= 0 }));
  })();

  $: cryptoArcs = (() => {
    if (!crypto.btc) return [];
    const slices = [
      { label: "BTC", value: crypto.btc, color: "#f7931a" },
      { label: "ETH", value: crypto.eth, color: "#627eea" },
      { label: "Other", value: crypto.other, color: "#2d2820" },
    ];
    const cx = 90, cy = 90, r = 62, sw = 20;
    let angle = -Math.PI / 2;
    return slices.map(s => {
      const sweep = (s.value / 100) * 2 * Math.PI;
      const x1 = cx + r * Math.cos(angle), y1 = cy + r * Math.sin(angle);
      const x2 = cx + r * Math.cos(angle + sweep - 0.01), y2 = cy + r * Math.sin(angle + sweep - 0.01);
      const d = `M ${x1.toFixed(1)} ${y1.toFixed(1)} A ${r} ${r} 0 ${sweep > Math.PI ? 1 : 0} 1 ${x2.toFixed(1)} ${y2.toFixed(1)}`;
      angle += sweep;
      return { ...s, d, sw };
    });
  })();

  function fmtPct(n) {
    if (n == null) return "—";
    return `${n >= 0 ? "+" : ""}${n.toFixed(1)}%`;
  }

  function fmtTime(d) {
    return new Intl.DateTimeFormat("en-US", {
      hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false
    }).format(d);
  }

  onMount(async () => {
    const [hbRes, fgRes, srRes, crRes] = await Promise.all([
      fetch("/api/market/heartbeat"),
      fetch("/api/market/fear-greed"),
      fetch("/api/market/sector-rotation"),
      fetch("/api/market/crypto"),
    ]);
    heartbeat = await hbRes.json();
    const fg = await fgRes.json();
    fearScore = fg.score;
    vix = fg.vix ?? null;
    sectors = await srRes.json();
    crypto = await crRes.json();
    clockInterval = setInterval(() => now = new Date(), 1000);
  });

  onDestroy(() => { if (clockInterval) clearInterval(clockInterval); });
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="" />
  <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
</svelte:head>

<main class="mkt-page p-6 min-h-screen">

  <div class="flex items-baseline justify-between mb-6">
    <div class="flex items-baseline gap-4">
      <h1 class="mkt-h1">Markets</h1>
      <span class="mkt-live">LIVE</span>
    </div>
    <div class="mkt-clock">{fmtTime(now)}</div>
  </div>

  <div class="grid gap-4" style="grid-template-columns:repeat(10,1fr); grid-template-rows:280px 500px">

    <!-- Heartbeat: cols 1-7, row 1 -->
    <div class="panel" style="grid-column:1/8; grid-row:1; display:flex; flex-direction:column">
      <div class="panel-label">Heartbeat · 30d</div>
      {#if Object.keys(heartbeat).length}
        <div class="flex-1 relative min-h-0 mt-3">
          <svg viewBox="0 0 600 160" class="w-full h-full" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              {#each Object.entries(heartbeat) as [name]}
                {@const id = name.replace(/[^a-zA-Z0-9]/g, "")}
                <linearGradient id="ag-{id}" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color={INDEX_COLORS[name] ?? "#888"} stop-opacity="0.18" />
                  <stop offset="100%" stop-color={INDEX_COLORS[name] ?? "#888"} stop-opacity="0" />
                </linearGradient>
              {/each}
            </defs>
            {#each [0.25, 0.5, 0.75] as t}
              <line x1="12" x2="588" y1={12 + t * 136} y2={12 + t * 136} stroke="#1e1b17" stroke-width="1" />
            {/each}
            {#each Object.entries(heartbeat) as [name, d]}
              {@const id = name.replace(/[^a-zA-Z0-9]/g, "")}
              {@const col = INDEX_COLORS[name] ?? "#888"}
              {@const dot = lastDot(d.pct)}
              <path d={toAreaD(d.pct)} fill="url(#ag-{id})" />
              <polyline
                points={toPolyline(d.pct)}
                fill="none"
                stroke={col}
                stroke-width="1.8"
                stroke-linejoin="round"
                stroke-linecap="round"
                opacity="0.9"
              />
              {#if dot}
                <circle cx={dot.x} cy={dot.y} r="3" fill={col} />
                <circle cx={dot.x} cy={dot.y} r="3" fill={col} opacity="0.45">
                  <animate attributeName="r" values="3;10;3" dur="2.5s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.45;0;0.45" dur="2.5s" repeatCount="indefinite" />
                </circle>
              {/if}
            {/each}
          </svg>
        </div>
        <div class="flex gap-6 mt-3 shrink-0">
          {#each Object.entries(heartbeat) as [name, d]}
            {@const change = d.pct?.at(-1) ?? 0}
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full shrink-0" style="background:{INDEX_COLORS[name]}"></div>
              <span class="idx-name">{name}</span>
              <span class="idx-val" style="color:{change >= 0 ? '#5db870' : '#d06050'}">{fmtPct(change)}</span>
            </div>
          {/each}
        </div>
      {:else}
        <div class="flex-1 flex items-center justify-center mkt-loading">Loading…</div>
      {/if}
    </div>

    <!-- Sentiment: cols 8-10, row 1 -->
    <div class="panel" style="grid-column:8/11; grid-row:1; display:flex; flex-direction:column; align-items:center; justify-content:center">
      <div class="panel-label mb-1">Sentiment</div>
      {#if fearScore !== null}
        <svg viewBox="0 0 220 155" class="w-full" xmlns="http://www.w3.org/2000/svg">
          <path d={gaugeTrack} fill="none" stroke="#1e1b17" stroke-width="13" stroke-linecap="round" />
          {#if gaugeFill}
            <path d={gaugeFill} fill="none" stroke={gaugeColor} stroke-width="13" stroke-linecap="round" />
          {/if}
          <text x="110" y="85" text-anchor="middle" dominant-baseline="middle"
            font-family="JetBrains Mono, monospace" font-size="40" font-weight="600"
            fill="#e8dcc8">{fearScore}</text>
          <text x="110" y="110" text-anchor="middle"
            font-family="Barlow Condensed, sans-serif" font-size="9.5" font-weight="600" letter-spacing="2.5"
            fill="#6a6058">{fearLabel.toUpperCase()}</text>
          {#if vix !== null}
            <text x="110" y="126" text-anchor="middle"
              font-family="JetBrains Mono, monospace" font-size="8"
              fill="#3a3530">VIX · {vix}</text>
          {/if}
          <text x="48" y="148" text-anchor="middle"
            font-family="Barlow Condensed, sans-serif" font-size="8" letter-spacing="1.5"
            fill="#2e2c28">FEAR</text>
          <text x="172" y="148" text-anchor="middle"
            font-family="Barlow Condensed, sans-serif" font-size="8" letter-spacing="1.5"
            fill="#2e2c28">GREED</text>
        </svg>
      {:else}
        <div class="gauge-skeleton"></div>
      {/if}
    </div>

    <!-- Sector Rotation: cols 1-5, row 2 -->
    <div class="panel" style="grid-column:1/6; grid-row:2; display:flex; flex-direction:column">
      <div class="panel-label mb-5">Sector Rotation · 30d</div>
      {#if sectorBars.length}
        <div class="flex-1 flex flex-col justify-center gap-2 overflow-hidden">
          {#each sectorBars as bar}
            <div class="s-row">
              <div class="s-name">{bar.name}</div>
              <div class="s-track">
                <div class="s-zero"></div>
                {#if bar.pos}
                  <div class="s-bar" style="left:50%; width:{bar.w * 47}%; background:#5db870"></div>
                {:else}
                  <div class="s-bar" style="right:50%; width:{bar.w * 47}%; background:#d06050"></div>
                {/if}
              </div>
              <div class="s-val" style="color:{bar.pos ? '#5db870' : '#d06050'}">{fmtPct(bar.pct)}</div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="flex-1 flex items-center justify-center mkt-loading">Loading…</div>
      {/if}
    </div>

    <!-- Crypto Dominance: cols 6-10, row 2 -->
    <div class="panel" style="grid-column:6/11; grid-row:2; display:flex; flex-direction:column">
      <div class="panel-label mb-5">Crypto Dominance</div>
      {#if crypto.btc}
        <div class="flex-1 flex items-center justify-around">
          <svg viewBox="0 0 180 180" class="w-44 shrink-0" xmlns="http://www.w3.org/2000/svg">
            {#each cryptoArcs as arc}
              <path d={arc.d} fill="none" stroke={arc.color} stroke-width={arc.sw} stroke-linecap="butt" />
            {/each}
            <text x="90" y="79" text-anchor="middle"
              font-family="Barlow Condensed, sans-serif" font-size="8" font-weight="600" letter-spacing="3"
              fill="#4a4540">BTC DOMINANCE</text>
            <text x="90" y="104" text-anchor="middle"
              font-family="JetBrains Mono, monospace" font-size="28" font-weight="600"
              fill="#f7931a">{crypto.btc}</text>
            <text x="90" y="120" text-anchor="middle"
              font-family="JetBrains Mono, monospace" font-size="10"
              fill="#6a6058">%</text>
          </svg>
          <div class="flex flex-col gap-7">
            {#each [["BTC", "#f7931a", crypto.btc], ["ETH", "#627eea", crypto.eth], ["Other", "#4a4540", crypto.other]] as [lbl, col, val]}
              <div>
                <div class="flex items-center gap-2 mb-1">
                  <div class="w-1.5 h-1.5 rounded-full shrink-0" style="background:{col}"></div>
                  <span class="cr-label">{lbl}</span>
                </div>
                <div class="cr-val" style="color:{col}">{val}<span class="cr-pct">%</span></div>
              </div>
            {/each}
          </div>
        </div>
      {:else}
        <div class="flex-1 flex items-center justify-center mkt-loading">Loading…</div>
      {/if}
    </div>

  </div>
</main>

<style>
  .mkt-page {
    background: radial-gradient(ellipse at 25% 15%, #1a1714 0%, #0f0d0b 70%);
    color: #e8dcc8;
    font-family: 'Barlow Condensed', sans-serif;
  }

  .mkt-h1 {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 2.25rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #e8dcc8;
  }

  .mkt-live {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    font-weight: 500;
    letter-spacing: 0.15em;
    color: #5db870;
    border: 1px solid rgba(93, 184, 112, 0.35);
    padding: 2px 7px;
    border-radius: 3px;
    animation: blink 2.5s step-end infinite;
  }

  .mkt-clock {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #3a3530;
    letter-spacing: 0.05em;
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.2; }
  }

  .panel {
    background: #161411;
    border: 1px solid #201e1a;
    border-radius: 16px;
    padding: 20px;
    overflow: hidden;
    position: relative;
  }

  .panel::after {
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 3px,
      rgba(0, 0, 0, 0.007) 3px,
      rgba(0, 0, 0, 0.007) 6px
    );
    pointer-events: none;
    border-radius: inherit;
  }

  .panel-label {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #3a3530;
    flex-shrink: 0;
  }

  .mkt-loading {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #3a3530;
    letter-spacing: 0.1em;
    animation: fadeload 1.8s ease-in-out infinite;
  }

  @keyframes fadeload {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.9; }
  }

  /* Heartbeat legend */
  .idx-name {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 0.78rem;
    letter-spacing: 0.04em;
    color: #6a6058;
  }

  .idx-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
  }

  /* Sentiment gauge skeleton */
  .gauge-skeleton {
    width: 130px;
    height: 130px;
    border-radius: 50%;
    background: #1e1b17;
    animation: fadeload 2s ease-in-out infinite;
  }

  /* Sector bars */
  .s-row {
    display: flex;
    align-items: center;
    gap: 10px;
    height: 28px;
    flex-shrink: 0;
  }

  .s-name {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #6a6058;
    width: 105px;
    flex-shrink: 0;
    text-align: right;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .s-track {
    flex: 1;
    height: 5px;
    background: #1a1814;
    border-radius: 3px;
    position: relative;
  }

  .s-zero {
    position: absolute;
    left: 50%;
    top: 0;
    bottom: 0;
    width: 1px;
    background: #2a2822;
  }

  .s-bar {
    position: absolute;
    height: 100%;
    border-radius: 2px;
    top: 0;
    min-width: 2px;
    transition: width 0.9s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .s-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    font-weight: 600;
    width: 52px;
    flex-shrink: 0;
    text-align: right;
  }

  /* Crypto */
  .cr-label {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 0.62rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #4a4540;
  }

  .cr-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.9rem;
    font-weight: 600;
    line-height: 1;
    margin-left: 14px;
  }

  .cr-pct {
    font-size: 0.85rem;
    font-weight: 400;
    opacity: 0.5;
  }
</style>
