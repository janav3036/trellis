<script>
  import { onMount, onDestroy } from 'svelte';
  import Plotly from 'plotly.js-dist-min';

  let el;
  let range = 'monthly';

  const RANGES = [
    { key: 'daily',   label: 'Today',    n: 0 },
    { key: 'monthly', label: '30 days',  n: 30 },
    { key: '6m',      label: '6 months', n: 180 },
    { key: 'yearly',  label: 'Year',     n: 365 },
  ];

  function daysAgo(n) {
    const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().split('T')[0];
  }
  function buildDates(n) {
    return Array.from({ length: n }, (_, i) => daysAgo(n - 1 - i));
  }
  function groupByDay(evs) {
    const c = {};
    for (const e of evs) { const d = e.timestamp.split('T')[0]; c[d] = (c[d] || 0) + 1; }
    return c;
  }
  function groupByWeek(evs) {
    const c = {};
    for (const e of evs) {
      const d = new Date(e.timestamp);
      const ws = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() - d.getUTCDay()));
      const w = ws.toISOString().split('T')[0];
      c[w] = (c[w] || 0) + 1;
    }
    return c;
  }

  const layout = {
    paper_bgcolor: '#1a1714', plot_bgcolor: '#1a1714',
    font: { color: '#e8e0d0' },
    xaxis: { gridcolor: '#242019', tickcolor: '#9a9080' },
    yaxis: { gridcolor: '#242019', tickcolor: '#9a9080', title: 'plays', rangemode: 'tozero' },
    margin: { t: 10, r: 20, b: 60, l: 50 },
  };

  let dailyTracks = [];

  async function loadChart(r) {
    range = r;
    dailyTracks = [];
    if (r === 'daily') {
      const res = await fetch(`/api/events?source=spotify&date_from=${daysAgo(0)}`);
      const evs = await res.json();
      dailyTracks = evs.map(e => ({
        time: new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        track: e.metadata.track_name, artist: e.metadata.artist,
      }));
      if (el) Plotly.purge(el);
      return;
    }
    let evs, dates, counts, title;
    if (r === 'monthly') {
      evs = await (await fetch(`/api/events?source=spotify&date_from=${daysAgo(29)}`)).json();
      dates = buildDates(30); counts = groupByDay(evs); title = 'Spotify — last 30 days';
    } else if (r === '6m') {
      evs = await (await fetch(`/api/events?source=spotify&date_from=${daysAgo(179)}`)).json();
      dates = buildDates(180); counts = groupByDay(evs); title = 'Spotify — last 6 months';
    } else {
      evs = await (await fetch(`/api/events?source=spotify&date_from=${daysAgo(364)}`)).json();
      counts = groupByWeek(evs); dates = Object.keys(counts).sort(); title = 'Spotify — last year';
    }
    Plotly.react(el, [{ x: dates, y: dates.map(d => counts[d] || 0), type: 'bar', marker: { color: '#c8813a' } }],
      { ...layout, title: { text: title, font: { color: '#e8e0d0', size: 12 } } });
  }

  onMount(() => loadChart('monthly'));
  onDestroy(() => { if (el) Plotly.purge(el); });
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="flex items-center gap-2 mb-3">
    <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider flex-1">Plays</div>
    {#each RANGES as r}
      <button
        on:click={() => loadChart(r.key)}
        class="px-2 py-0.5 rounded text-xs {range === r.key ? 'bg-[#c8813a] text-[#1a1714]' : 'text-[#9a9080] hover:text-[#e8e0d0]'}"
      >{r.label}</button>
    {/each}
  </div>
  {#if range === 'daily'}
    <div class="flex flex-col gap-1 max-h-64 overflow-y-auto">
      {#each dailyTracks as t}
        <div class="flex items-center gap-3 px-3 py-1.5 rounded-lg bg-[#1a1714]">
          <span class="text-xs text-[#9a9080] w-10 shrink-0">{t.time}</span>
          <span class="text-sm truncate">{t.track}</span>
          <span class="text-xs text-[#9a9080] truncate">{t.artist}</span>
        </div>
      {:else}
        <p class="text-sm text-[#9a9080]">No plays yet today.</p>
      {/each}
    </div>
  {:else}
    <div bind:this={el}></div>
  {/if}
</div>
