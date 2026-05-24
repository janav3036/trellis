<script>
  import { onMount } from 'svelte';
  let crypto = {};

  $: dominant = crypto.btc >= (crypto.eth || 0)
    ? { label: 'BTC', pct: crypto.btc }
    : { label: 'ETH', pct: crypto.eth };

  $: arcs = (() => {
    if (!crypto.btc) return [];
    const slices = [
      { label: 'BTC',   value: crypto.btc,   color: '#f7931a' },
      { label: 'ETH',   value: crypto.eth,   color: '#627eea' },
      { label: 'Other', value: crypto.other, color: 'rgba(255,255,255,0.08)' },
    ];
    const cx = 80, cy = 80, r = 54, sw = 13;
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
    crypto = await (await fetch('/api/market/crypto')).json();
  });
</script>

<div class="panel" on:click={() => window.location.hash = '/market'}>
  <span class="eyebrow">Crypto Dominance</span>

  {#if crypto.btc}
    <div class="chart-wrap">
      <svg viewBox="0 0 160 160" class="donut" xmlns="http://www.w3.org/2000/svg">
        <!-- Track -->
        <circle cx="80" cy="80" r="54" fill="none"
                stroke="rgba(255,255,255,0.05)" stroke-width="13" />
        {#each arcs as arc}
          <path d={arc.d} fill="none" stroke={arc.color}
                stroke-width={arc.sw} stroke-linecap="butt" />
        {/each}
        <text x="80" y="76" text-anchor="middle"
              font-size="13" font-weight="700" fill="var(--text-primary)">{dominant.label}</text>
        <text x="80" y="93" text-anchor="middle"
              font-size="11" fill="var(--text-secondary)">{dominant.pct}%</text>
      </svg>
    </div>

    <div class="legend">
      {#each [['BTC','#f7931a',crypto.btc],['ETH','#627eea',crypto.eth],['Other','rgba(255,255,255,0.2)',crypto.other]] as [lbl,color,val]}
        <div class="legend-item">
          <div class="legend-dot" style="background:{color}" />
          <span class="legend-label">{lbl}</span>
          <span class="legend-val">{val}%</span>
        </div>
      {/each}
    </div>
  {:else}
    <div class="loading">Loading…</div>
  {/if}
</div>

<style>
  .panel {
    background: var(--surface);
    border-radius: 14px;
    padding: 14px;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    cursor: pointer;
    transition: filter 0.2s ease;
    box-sizing: border-box;
  }
  .panel:hover { filter: brightness(1.06); }

  .eyebrow {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--text-secondary);
    flex-shrink: 0;
    margin-bottom: 4px;
  }

  .chart-wrap {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 0;
  }
  .donut {
    width: 100%;
    max-width: 220px;
  }

  .legend {
    display: flex;
    justify-content: center;
    gap: 14px;
    flex-shrink: 0;
    padding-top: 4px;
  }
  .legend-item {
    display: flex;
    align-items: center;
    gap: 5px;
  }
  .legend-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .legend-label {
    font-size: 0.68rem;
    color: var(--text-secondary);
  }
  .legend-val {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-primary);
    font-variant-numeric: tabular-nums;
  }

  .loading {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    color: var(--text-secondary);
  }
</style>
