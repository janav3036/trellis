<script>
  import { onMount } from 'svelte';
  let crypto = {};

  $: dominant = crypto.btc >= (crypto.eth || 0) ? { label: 'BTC', pct: crypto.btc } : { label: 'ETH', pct: crypto.eth };

  $: arcs = (() => {
    if (!crypto.btc) return [];
    const slices = [
      { label: 'BTC',   value: crypto.btc,   color: '#f7931a' },
      { label: 'ETH',   value: crypto.eth,   color: '#627eea' },
      { label: 'Other', value: crypto.other, color: '#5a5248' },
    ];
    const cx = 80, cy = 80, r = 55, sw = 14;
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

<div class="bg-[#242019] rounded-xl p-4 h-full flex flex-col cursor-pointer"
     on:click={() => window.location.hash = '/market'}>
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-2 shrink-0">Crypto Dominance</div>
  {#if crypto.btc}
    <div class="flex-1 flex flex-col items-center justify-center gap-3 min-h-0">
      <svg viewBox="0 0 160 160" class="w-full max-w-[260px] shrink-0" xmlns="http://www.w3.org/2000/svg">
        {#each arcs as arc}
          <path d={arc.d} fill="none" stroke={arc.color} stroke-width={arc.sw} stroke-linecap="butt" />
        {/each}
        <text x="80" y="75" text-anchor="middle" font-size="14" font-weight="700" fill="#e8e0d0">{dominant.label}</text>
        <text x="80" y="93" text-anchor="middle" font-size="11" fill="#9a9080">{dominant.pct}%</text>
      </svg>
      <div class="flex gap-4 shrink-0">
        {#each [['BTC','#f7931a',crypto.btc],['ETH','#627eea',crypto.eth],['Other','#5a5248',crypto.other]] as [label,color,val]}
          <div class="flex items-center gap-1.5">
            <div class="w-2 h-2 rounded-full shrink-0" style="background:{color}"></div>
            <span class="text-xs text-[#9a9080]">{label}</span>
            <span class="text-xs font-medium tabular-nums">{val}%</span>
          </div>
        {/each}
      </div>
    </div>
  {:else}
    <div class="flex-1 flex items-center justify-center text-[#9a9080] text-sm animate-pulse">Loading…</div>
  {/if}
</div>
