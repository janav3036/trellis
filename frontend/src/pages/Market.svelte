<script>
  import { onMount } from "svelte";

  let heartbeat = {};
  let fearScore = null;
  let sectors = {};
  let crypto = {};

  const INDEX_COLORS = {
    "S&P 500": "#c8813a",
    "Nikkei":  "#4dabf7",
    "DAX":     "#69db7c",
    "FTSE":    "#f783ac",
  };

  function toPolyline(pcts, w, h, pad = 12) {
    if (!pcts || pcts.length < 2) return "";
    const minV = Math.min(...pcts);
    const maxV = Math.max(...pcts);
    const range = maxV - minV || 1;
    return pcts
      .map((v, i) => {
        const x = pad + (i / (pcts.length - 1)) * (w - pad * 2);
        const y = (h - pad) - ((v - minV) / range) * (h - pad * 2);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  }

  $: orbColor = fearScore === null
    ? "#333"
    : fearScore > 50
      ? `rgba(200, 129, 58, ${0.5 + (fearScore - 50) / 100})`
      : `rgba(77, 171, 247, ${0.5 + (50 - fearScore) / 100})`;

  $: orbGlow = fearScore === null
    ? "none"
    : fearScore > 50
      ? `0 0 ${25 + fearScore * 0.4}px rgba(200,129,58,0.8), 0 0 ${55 + fearScore}px rgba(200,129,58,0.3)`
      : `0 0 ${25 + (100 - fearScore) * 0.4}px rgba(77,171,247,0.8), 0 0 ${55 + (100 - fearScore)}px rgba(77,171,247,0.3)`;

  $: sectorPetals = (() => {
    const entries = Object.entries(sectors);
    if (!entries.length) return [];
    const maxAbs = Math.max(...entries.map(([, v]) => Math.abs(v)));
    const cx = 130, cy = 130, maxR = 100;
    return entries.map(([name, pct], i) => {
      const angle = (i / entries.length) * 2 * Math.PI - Math.PI / 2;
      const len = maxAbs > 0 ? (Math.abs(pct) / maxAbs) * maxR + 16 : 16;
      const hw = 0.20;
      const tx = cx + Math.cos(angle) * len;
      const ty = cy + Math.sin(angle) * len;
      const lx = cx + Math.cos(angle - hw) * len * 0.45;
      const ly = cy + Math.sin(angle - hw) * len * 0.45;
      const rx = cx + Math.cos(angle + hw) * len * 0.45;
      const ry = cy + Math.sin(angle + hw) * len * 0.45;
      const path = `M ${cx} ${cy} Q ${lx.toFixed(1)} ${ly.toFixed(1)} ${tx.toFixed(1)} ${ty.toFixed(1)} Q ${rx.toFixed(1)} ${ry.toFixed(1)} ${cx} ${cy} Z`;
      const lblR = len + 13;
      return {
        name,
        pct,
        path,
        color: pct >= 0 ? "#69db7c" : "#ff6b6b",
        lblX: cx + Math.cos(angle) * lblR,
        lblY: cy + Math.sin(angle) * lblR,
      };
    });
  })();

  $: cryptoArcs = (() => {
    if (!crypto.btc) return [];
    const slices = [
      { label: "BTC", value: crypto.btc, color: "#f7931a" },
      { label: "ETH", value: crypto.eth, color: "#627eea" },
      { label: "Other", value: crypto.other, color: "#2d2822" },
    ];
    const cx = 90, cy = 90, r = 60, sw = 18;
    let angle = -Math.PI / 2;
    return slices.map(s => {
      const sweep = (s.value / 100) * 2 * Math.PI;
      const x1 = cx + r * Math.cos(angle);
      const y1 = cy + r * Math.sin(angle);
      const x2 = cx + r * Math.cos(angle + sweep - 0.01);
      const y2 = cy + r * Math.sin(angle + sweep - 0.01);
      const large = sweep > Math.PI ? 1 : 0;
      const d = `M ${x1.toFixed(1)} ${y1.toFixed(1)} A ${r} ${r} 0 ${large} 1 ${x2.toFixed(1)} ${y2.toFixed(1)}`;
      angle += sweep;
      return { ...s, d, sw };
    });
  })();

  onMount(async () => {
    const [hbRes, fgRes, srRes, crRes] = await Promise.all([
      fetch("/api/market/heartbeat"),
      fetch("/api/market/fear-greed"),
      fetch("/api/market/sector-rotation"),
      fetch("/api/market/crypto"),
    ]);
    heartbeat = await hbRes.json();
    fearScore = (await fgRes.json()).score;
    sectors = await srRes.json();
    crypto = await crRes.json();
  });
</script>

<main class="p-8 bg-[#1a1714] min-h-screen text-[#e8e0d0]">

  <h1 class="text-3xl font-semibold mb-8">Markets</h1>

  <!-- Heartbeat + Sentiment -->
  <div class="grid grid-cols-3 gap-6 mb-6">

    <!-- Heartbeat -->
    <div class="col-span-2 bg-[#242019] rounded-xl p-4">
      <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Heartbeat · 30d</h2>
      {#if Object.keys(heartbeat).length}
        <svg viewBox="0 0 600 130" class="w-full" xmlns="http://www.w3.org/2000/svg">
          {#each Object.entries(heartbeat) as [name, d]}
            <polyline
              points={toPolyline(d.pct, 600, 130)}
              fill="none"
              stroke={INDEX_COLORS[name] ?? "#888"}
              stroke-width="1.6"
              stroke-linejoin="round"
              opacity="0.85"
            />
          {/each}
        </svg>
        <div class="flex gap-5 mt-2">
          {#each Object.entries(INDEX_COLORS) as [name, color]}
            <div class="flex items-center gap-1.5">
              <div class="w-2 h-2 rounded-full" style="background:{color}"></div>
              <span class="text-xs text-[#9a9080]">{name}</span>
            </div>
          {/each}
        </div>
      {:else}
        <div class="h-32 flex items-center justify-center text-[#9a9080] text-sm">Loading…</div>
      {/if}
    </div>

    <!-- Fear & Greed orb -->
    <div class="bg-[#242019] rounded-xl p-4 flex flex-col items-center justify-center gap-6">
      <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider">Sentiment</h2>
      {#if fearScore !== null}
        <div
          class="w-28 h-28 rounded-full transition-all duration-1000"
          style="background:{orbColor}; box-shadow:{orbGlow};"
        ></div>
      {:else}
        <div class="w-28 h-28 rounded-full bg-[#2a2520] animate-pulse"></div>
      {/if}
    </div>

  </div>

  <!-- Sector Rotation + Crypto Dominance -->
  <div class="grid grid-cols-2 gap-6">

    <!-- Sector Rotation -->
    <div class="bg-[#242019] rounded-xl p-4">
      <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-2">Sector Rotation · 30d</h2>
      {#if sectorPetals.length}
        <svg viewBox="0 0 260 260" class="w-full max-w-xs mx-auto" xmlns="http://www.w3.org/2000/svg">
          <circle cx="130" cy="130" r="3" fill="#3a3530" />
          {#each sectorPetals as p}
            <path d={p.path} fill={p.color} opacity="0.72" />
            <text
              x={p.lblX}
              y={p.lblY}
              text-anchor="middle"
              dominant-baseline="middle"
              font-size="6.5"
              fill="#9a9080"
            >{p.name}</text>
          {/each}
        </svg>
      {:else}
        <div class="h-64 flex items-center justify-center text-[#9a9080] text-sm">Loading…</div>
      {/if}
    </div>

    <!-- Crypto Dominance -->
    <div class="bg-[#242019] rounded-xl p-4">
      <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-2">Crypto Dominance</h2>
      {#if crypto.btc}
        <div class="flex items-center justify-around mt-4">
          <svg viewBox="0 0 180 180" class="w-44" xmlns="http://www.w3.org/2000/svg">
            {#each cryptoArcs as arc}
              <path
                d={arc.d}
                fill="none"
                stroke={arc.color}
                stroke-width={arc.sw}
                stroke-linecap="butt"
              />
            {/each}
            <text x="90" y="86" text-anchor="middle" font-size="13" font-weight="600" fill="#f7931a">BTC</text>
            <text x="90" y="103" text-anchor="middle" font-size="10" fill="#9a9080">{crypto.btc}%</text>
          </svg>
          <div class="flex flex-col gap-3">
            {#each [["BTC", "#f7931a", crypto.btc], ["ETH", "#627eea", crypto.eth], ["Other", "#9a9080", crypto.other]] as [label, color, val]}
              <div class="flex items-center gap-2">
                <div class="w-2.5 h-2.5 rounded-full" style="background:{color}"></div>
                <span class="text-xs text-[#9a9080]">{label}</span>
                <span class="text-xs font-medium tabular-nums ml-1">{val}%</span>
              </div>
            {/each}
          </div>
        </div>
      {:else}
        <div class="h-64 flex items-center justify-center text-[#9a9080] text-sm">Loading…</div>
      {/if}
    </div>

  </div>

</main>
