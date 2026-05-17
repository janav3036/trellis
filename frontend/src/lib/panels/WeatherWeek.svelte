<script>
  import { onMount } from 'svelte';
  let days = [], forecast = [], weekDays = [], weekOffset = 0;

  function tempColor(t) {
    const v = Math.max(0, Math.min(35, t)) / 35;
    return `rgb(${Math.round(60+v*160)},${Math.round(80+v*60)},${Math.round(160-v*120)})`;
  }
  function tempColorAlpha(t, a) {
    const v = Math.max(0, Math.min(35, t)) / 35;
    return `rgba(${Math.round(60+v*160)},${Math.round(80+v*60)},${Math.round(160-v*120)},${a})`;
  }
  function weatherLabel(code) {
    if (code === 0) return 'Clear';
    if (code <= 3) return 'Partly cloudy';
    if (code <= 48) return 'Fog';
    if (code <= 57) return 'Drizzle';
    if (code <= 67) return 'Rain';
    if (code <= 77) return 'Snow';
    if (code <= 82) return 'Showers';
    return 'Storm';
  }
  function daysAgo(n) {
    const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().split('T')[0];
  }

  $: {
    const today = new Date();
    const dow = today.getDay();
    const toMon = dow === 0 ? -6 : 1 - dow;
    const mon = new Date(today); mon.setDate(today.getDate() + toMon + weekOffset * 7); mon.setHours(0,0,0,0);
    const sun = new Date(mon); sun.setDate(mon.getDate() + 6); sun.setHours(23,59,59,0);
    weekDays = [...days, ...forecast].filter(d => {
      const t = new Date(d.timestamp); return t >= mon && t <= sun;
    });
  }

  $: weekLabel = (() => {
    const today = new Date();
    const dow = today.getDay();
    const toMon = dow === 0 ? -6 : 1 - dow;
    const mon = new Date(today); mon.setDate(today.getDate() + toMon + weekOffset * 7);
    const sun = new Date(mon); sun.setDate(mon.getDate() + 6);
    const fmt = d => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    return `${fmt(mon)} – ${fmt(sun)}`;
  })();

  onMount(async () => {
    const [calRes, fRes] = await Promise.all([
      fetch(`/api/events?source=weather&event_type=daily&date_from=${daysAgo(89)}`),
      fetch('/api/weather/forecast'),
    ]);
    days = (await calRes.json()).reverse();
    forecast = await fRes.json();
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="flex items-center gap-3 mb-3">
    <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider flex-1">This Week</div>
    <button on:click={() => weekOffset--} class="bg-[#1a1714] hover:bg-[#2a2520] px-2 py-0.5 rounded text-xs">←</button>
    <span class="text-xs text-[#9a9080]">{weekLabel}</span>
    <button on:click={() => weekOffset = Math.min(1, weekOffset+1)} disabled={weekOffset>=1}
      class="bg-[#1a1714] hover:bg-[#2a2520] px-2 py-0.5 rounded text-xs disabled:opacity-30">→</button>
  </div>
  {#if weekDays.length > 0}
    <div class="grid grid-cols-7 gap-1.5">
      {#each weekDays as d}
        {@const m = d.metadata}
        <div class="rounded-lg p-2 flex flex-col items-center gap-0.5"
          style="background:{tempColorAlpha(m.temp_max,0.18)}; border:1px solid {tempColorAlpha(m.temp_max,0.35)}">
          <div class="text-[9px] text-[#9a9080]">{new Date(d.timestamp).toLocaleDateString('en-US',{weekday:'short'})}</div>
          <div class="text-[9px] text-[#9a9080]">{new Date(d.timestamp).toLocaleDateString('en-US',{month:'short',day:'numeric'})}</div>
          <div class="text-sm font-semibold mt-0.5" style="color:{tempColor(m.temp_max)}">{Math.round(m.temp_max)}°</div>
          <div class="text-[9px] text-[#9a9080]">{Math.round(m.temp_min)}°</div>
          <div class="text-[9px] text-center text-[#c8c0b0] leading-tight mt-0.5">{weatherLabel(m.weathercode)}</div>
          {#if m.precipitation > 1}<div class="text-[9px] text-[#6b9ecc]">💧{m.precipitation}mm</div>{/if}
        </div>
      {/each}
    </div>
  {:else}
    <p class="text-sm text-[#9a9080]">No data for this week.</p>
  {/if}
</div>
