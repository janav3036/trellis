<script>
  import { onMount } from 'svelte';
  let sectors = {};

  $: petals = (() => {
    const entries = Object.entries(sectors);
    if (!entries.length) return [];
    const maxAbs = Math.max(...entries.map(([,v]) => Math.abs(v)));
    const cx=130, cy=130, maxR=100;
    return entries.map(([name,pct],i) => {
      const angle = (i/entries.length)*2*Math.PI - Math.PI/2;
      const len = maxAbs>0 ? (Math.abs(pct)/maxAbs)*maxR+16 : 16;
      const hw = 0.20;
      const tx = cx+Math.cos(angle)*len, ty = cy+Math.sin(angle)*len;
      const lx = cx+Math.cos(angle-hw)*len*0.45, ly = cy+Math.sin(angle-hw)*len*0.45;
      const rx = cx+Math.cos(angle+hw)*len*0.45, ry = cy+Math.sin(angle+hw)*len*0.45;
      const path = `M ${cx} ${cy} Q ${lx.toFixed(1)} ${ly.toFixed(1)} ${tx.toFixed(1)} ${ty.toFixed(1)} Q ${rx.toFixed(1)} ${ry.toFixed(1)} ${cx} ${cy} Z`;
      const lblR = len+13;
      return {
        name, pct, path,
        color: pct>=0?'#69db7c':'#ff6b6b',
        lblX: cx+Math.cos(angle)*lblR, lblY: cy+Math.sin(angle)*lblR,
      };
    });
  })();

  onMount(async () => {
    sectors = await (await fetch('/api/market/sector-rotation')).json();
  });
</script>

<div class="bg-[#242019] rounded-xl p-4">
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-2">Sector Rotation · 30d</div>
  {#if petals.length}
    <svg viewBox="0 0 260 260" class="w-full max-w-[260px] mx-auto" xmlns="http://www.w3.org/2000/svg">
      <circle cx="130" cy="130" r="3" fill="#3a3530" />
      {#each petals as p}
        <path d={p.path} fill={p.color} opacity="0.72" />
        <text x={p.lblX} y={p.lblY} text-anchor="middle" dominant-baseline="middle"
          font-size="6.5" fill="#9a9080">{p.name}</text>
      {/each}
    </svg>
  {:else}
    <div class="h-64 flex items-center justify-center text-[#9a9080] text-sm animate-pulse">Loading…</div>
  {/if}
</div>
