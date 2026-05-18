<script>
  import { onMount } from 'svelte';
  import { daysAgoIST } from '../ist.js';
  let today = null;

  function tempColor(t) {
    const v = Math.max(0, Math.min(35, t)) / 35;
    return `rgb(${Math.round(60+v*160)},${Math.round(80+v*60)},${Math.round(160-v*120)})`;
  }
  function tempColorAlpha(t, a) {
    const v = Math.max(0, Math.min(35, t)) / 35;
    return `rgba(${Math.round(60+v*160)},${Math.round(80+v*60)},${Math.round(160-v*120)},${a})`;
  }
  function label(code) {
    if (code === 0) return 'Clear sky';
    if (code <= 3) return 'Partly cloudy';
    if (code <= 48) return 'Fog';
    if (code <= 57) return 'Drizzle';
    if (code <= 67) return 'Rain';
    if (code <= 77) return 'Snow';
    if (code <= 82) return 'Rain showers';
    if (code <= 86) return 'Snow showers';
    return 'Thunderstorm';
  }

  onMount(async () => {
    const evs = await (await fetch(`/api/events?source=weather&event_type=daily&date_from=${daysAgoIST(1)}`)).json();
    today = evs[0] ?? null;
  });
</script>

{#if today}
  {@const m = today.metadata}
  <div class="rounded-xl p-3 h-full flex flex-col justify-between overflow-hidden cursor-pointer"
       style="background:{tempColorAlpha(m.temp_max,0.13)}; border:1px solid {tempColorAlpha(m.temp_max,0.27)}"
       on:click={() => window.location.hash = '/weather'}>
    <div class="flex items-center justify-between gap-2">
      <span class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider shrink-0">Today</span>
      <span class="text-xs text-[#9a9080] truncate">
        {new Date(today.timestamp).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
      </span>
    </div>
    <div class="flex items-baseline gap-2">
      <span class="text-2xl font-bold leading-none" style="color:{tempColor(m.temp_max)}">{Math.round(m.temp_max)}°C</span>
      <span class="text-sm text-[#9a9080] leading-none">/ {Math.round(m.temp_min)}°C</span>
    </div>
    <div class="flex items-center gap-3 text-xs text-[#9a9080]">
      <span class="truncate">{label(m.weathercode)}</span>
      <span class="shrink-0">{Math.round(m.windspeed_max)} km/h</span>
    </div>
  </div>
{:else}
  <div class="bg-[#242019] rounded-xl p-3 h-full flex items-center justify-center">
    <span class="text-sm text-[#9a9080] animate-pulse">Loading…</span>
  </div>
{/if}
