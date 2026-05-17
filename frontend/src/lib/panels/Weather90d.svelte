<script>
  import { onMount } from 'svelte';
  let days = [];

  function tempColor(t) {
    const v = Math.max(0, Math.min(35, t)) / 35;
    return `rgb(${Math.round(60+v*160)},${Math.round(80+v*60)},${Math.round(160-v*120)})`;
  }
  function tempColorAlpha(t, a) {
    const v = Math.max(0, Math.min(35, t)) / 35;
    return `rgba(${Math.round(60+v*160)},${Math.round(80+v*60)},${Math.round(160-v*120)},${a})`;
  }
  function weatherLabel(code) {
    if (code === 0) return 'Clear sky';
    if (code <= 3) return 'Partly cloudy';
    if (code <= 48) return 'Fog';
    if (code <= 57) return 'Drizzle';
    if (code <= 67) return 'Rain';
    if (code <= 77) return 'Snow';
    return 'Storm';
  }
  function daysAgo(n) {
    const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().split('T')[0];
  }

  onMount(async () => {
    days = (await (await fetch(`/api/events?source=weather&event_type=daily&date_from=${daysAgo(89)}`)).json()).reverse();
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Last 90 Days</div>
  {#if days.length === 0}
    <p class="text-sm text-[#9a9080] animate-pulse">Loading…</p>
  {:else}
    <div class="grid grid-cols-[repeat(auto-fill,minmax(64px,1fr))] gap-1.5">
      {#each days as d}
        {@const m = d.metadata}
        <div class="rounded-lg p-1.5 flex flex-col items-center"
          style="background:{tempColorAlpha(m.temp_max,0.18)}; border:1px solid {tempColorAlpha(m.temp_max,0.35)}"
          title="{weatherLabel(m.weathercode)} — {m.precipitation}mm">
          <div class="text-[9px] text-[#9a9080] mb-0.5">
            {new Date(d.timestamp).toLocaleDateString('en-US',{month:'short',day:'numeric'})}
          </div>
          <div class="text-xs font-semibold" style="color:{tempColor(m.temp_max)}">{Math.round(m.temp_max)}°</div>
          <div class="text-[9px] text-[#9a9080]">{Math.round(m.temp_min)}°</div>
          {#if m.precipitation > 1}<div class="text-[9px] mt-0.5 text-[#6b9ecc]">💧</div>{/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
