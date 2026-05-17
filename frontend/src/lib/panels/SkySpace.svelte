<script>
  import { onMount, onDestroy } from 'svelte';
  let iss = null, neos = [], issTimer;

  async function pollISS() {
    try { const r=await fetch('/api/sky/iss'); if(r.ok) iss=await r.json(); } catch {}
    issTimer = setTimeout(pollISS, 15000);
  }

  function fmtNum(n) { return n?.toLocaleString() ?? '—'; }

  onMount(async () => {
    neos = await (await fetch('/api/sky/neo')).json();
    pollISS();
  });
  onDestroy(() => clearTimeout(issTimer));
</script>

<div class="flex flex-col gap-4 min-w-[280px]">
  <!-- ISS -->
  <div class="bg-[#242019] rounded-xl p-4">
    <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">ISS · Live</div>
    {#if iss}
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div><div class="text-[#9a9080] text-xs">Position</div>
          <div class="font-mono tabular-nums">{iss.lat.toFixed(2)}° {iss.lon.toFixed(2)}°</div></div>
        <div><div class="text-[#9a9080] text-xs">Altitude</div>
          <div class="font-mono tabular-nums">{iss.altitude_km} km</div></div>
        <div><div class="text-[#9a9080] text-xs">Speed</div>
          <div class="font-mono tabular-nums">{fmtNum(iss.velocity_kmh)} km/h</div></div>
        <div><div class="text-[#9a9080] text-xs">Visibility</div>
          <div class="capitalize">{iss.visibility||'—'}</div></div>
      </div>
    {:else}
      <div class="h-16 flex items-center justify-center text-[#9a9080] text-sm animate-pulse">Loading…</div>
    {/if}
  </div>

  <!-- NEOs -->
  <div class="bg-[#242019] rounded-xl p-4">
    <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Near-Earth Objects · 7 Days</div>
    {#if neos.length}
      <div class="space-y-2">
        {#each neos.slice(0,6) as neo}
          <div class="flex items-center gap-2 text-xs">
            {#if neo.hazardous}<span class="text-[#ff6b6b]">⚠</span>{:else}<span class="text-[#9a9080]">·</span>{/if}
            <span class="flex-1 truncate">{neo.name}</span>
            <span class="text-[#9a9080] shrink-0">{neo.date}</span>
            <span class="text-[#9a9080] tabular-nums shrink-0">{(neo.miss_km/1e6).toFixed(1)}M km</span>
          </div>
        {/each}
      </div>
    {:else}
      <div class="h-16 flex items-center justify-center text-[#9a9080] text-sm animate-pulse">Loading…</div>
    {/if}
  </div>
</div>
