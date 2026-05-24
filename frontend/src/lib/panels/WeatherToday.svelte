<script>
  import { onMount } from 'svelte';
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
    if (code === 0) return 'Clear';
    if (code <= 3)  return 'Partly cloudy';
    if (code <= 48) return 'Fog';
    if (code <= 57) return 'Drizzle';
    if (code <= 67) return 'Rain';
    if (code <= 77) return 'Snow';
    if (code <= 82) return 'Showers';
    if (code <= 86) return 'Snow showers';
    return 'Thunderstorm';
  }
  function icon(code) {
    if (code === 0)  return '☀️';
    if (code <= 3)   return '⛅';
    if (code <= 48)  return '🌫️';
    if (code <= 57)  return '🌦️';
    if (code <= 67)  return '🌧️';
    if (code <= 77)  return '❄️';
    if (code <= 82)  return '🌧️';
    if (code <= 86)  return '🌨️';
    return '⛈️';
  }

  onMount(async () => {
    const evs = await (await fetch(`/api/events?source=weather&event_type=daily`)).json();
    today = evs[0] ?? null;
  });
</script>

{#if today}
  {@const m = today.metadata}
  <div class="panel"
       style="background:{tempColorAlpha(m.temp_max,0.12)}; border:1px solid {tempColorAlpha(m.temp_max,0.22)}"
       on:click={() => window.location.hash = '/weather'}>

    <div class="top-row">
      <span class="eyebrow">Today</span>
      <span class="wx-icon">{icon(m.weathercode)}</span>
    </div>

    <div class="temp-row">
      <span class="temp-max" style="color:{tempColor(m.temp_max)}">{Math.round(m.temp_max)}°</span>
      <span class="temp-min">/ {Math.round(m.temp_min)}°C</span>
    </div>

    <div class="meta-row">
      <span class="condition">{label(m.weathercode)}</span>
      <span class="wind">{Math.round(m.windspeed_max)} km/h</span>
    </div>
  </div>
{:else}
  <div class="panel loading">
    <span class="eyebrow">Today</span>
    <span class="idle-text">—</span>
  </div>
{/if}

<style>
  .panel {
    border-radius: 14px;
    padding: 12px 14px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
    cursor: pointer;
    transition: filter 0.2s ease;
    box-sizing: border-box;
  }
  .panel:hover { filter: brightness(1.08); }
  .loading { background: var(--surface); border: 1px solid transparent; gap: 4px; }

  .top-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .eyebrow {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--text-secondary);
  }
  .wx-icon {
    font-size: 1rem;
    line-height: 1;
  }

  .temp-row { display: flex; align-items: baseline; gap: 5px; }
  .temp-max {
    font-size: 1.85rem;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.02em;
  }
  .temp-min {
    font-size: 0.82rem;
    color: var(--text-secondary);
  }

  .meta-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 0.72rem;
    color: var(--text-secondary);
  }
  .condition { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .wind { flex-shrink: 0; }

  .idle-text { font-size: 0.85rem; color: var(--text-secondary); }
</style>
