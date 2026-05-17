<script>
  import { onMount } from 'svelte';
  let heartbeat = {};

  const INDEX_COLORS = {
    'S&P 500': '#c8813a',
    'Nikkei':  '#4dabf7',
    'DAX':     '#69db7c',
    'FTSE':    '#f783ac',
  };

  function toPolyline(pcts, w=600, h=130, pad=12) {
    if (!pcts || pcts.length < 2) return '';
    const minV = Math.min(...pcts), maxV = Math.max(...pcts), range = maxV-minV||1;
    return pcts.map((v,i) => {
      const x = pad + (i/(pcts.length-1))*(w-pad*2);
      const y = (h-pad) - ((v-minV)/range)*(h-pad*2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ');
  }

  onMount(async () => {
    heartbeat = await (await fetch('/api/market/heartbeat')).json();
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Heartbeat · 30d</div>
  {#if Object.keys(heartbeat).length}
    <svg viewBox="0 0 600 130" class="w-full" xmlns="http://www.w3.org/2000/svg">
      {#each Object.entries(heartbeat) as [name, d]}
        <polyline
          points={toPolyline(d.pct)}
          fill="none"
          stroke={INDEX_COLORS[name] ?? '#888'}
          stroke-width="1.6"
          stroke-linejoin="round"
          opacity="0.85"
        />
      {/each}
    </svg>
    <div class="flex gap-4 mt-2">
      {#each Object.entries(INDEX_COLORS) as [name, color]}
        <div class="flex items-center gap-1.5">
          <div class="w-2 h-2 rounded-full" style="background:{color}"></div>
          <span class="text-xs text-[#9a9080]">{name}</span>
        </div>
      {/each}
    </div>
  {:else}
    <div class="h-32 flex items-center justify-center text-[#9a9080] text-sm animate-pulse">Loading…</div>
  {/if}
</div>
