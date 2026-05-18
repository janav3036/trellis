<script>
  import { onMount, onDestroy } from 'svelte';
  import Plotly from 'plotly.js-dist-min';
  import { musicTheme } from '../musicTheme.js';
  import { get } from 'svelte/store';
  import { daysAgoIST, buildDatesIST, groupByDayIST, groupByWeekIST, istTime } from '../ist.js';

  let el;
  let range = 'monthly';
  let dailyTracks = [];
  let cachedEvents = [];
  let cachedRange  = null;
  let unsubTheme;

  const RANGES = [
    { key: 'daily',   label: 'Today' },
    { key: 'monthly', label: '30 days' },
    { key: '6m',      label: '6 months' },
    { key: 'yearly',  label: 'Year' },
  ];

  function plotLayout(theme) {
    return {
      paper_bgcolor: theme.bg,
      plot_bgcolor:  theme.bg,
      font:   { color: theme.text },
      xaxis:  { gridcolor: 'transparent', tickcolor: theme.muted, showgrid: false },
      yaxis:  { gridcolor: 'transparent', tickcolor: theme.muted, showgrid: false, rangemode: 'tozero' },
      margin: { t: 10, r: 20, b: 60, l: 50 },
    };
  }

  function drawChart() {
    if (!el || cachedRange === 'daily' || !cachedEvents.length) return;
    const theme = get(musicTheme);
    let dates, counts;
    if (cachedRange === 'monthly') {
      dates = buildDatesIST(30); counts = groupByDayIST(cachedEvents);
    } else if (cachedRange === '6m') {
      dates = buildDatesIST(180); counts = groupByDayIST(cachedEvents);
    } else {
      counts = groupByWeekIST(cachedEvents); dates = Object.keys(counts).sort();
    }
    Plotly.react(
      el,
      [{ x: dates, y: dates.map(d => counts[d] || 0), type: 'bar', marker: { color: theme.accent } }],
      plotLayout(theme),
    );
  }

  async function loadChart(r) {
    range = r;
    cachedRange = r;
    dailyTracks = [];

    if (r === 'daily') {
      const evs = await (await fetch(`/api/events?source=spotify&date_from=${daysAgoIST(0)}`)).json();
      cachedEvents = evs;
      dailyTracks  = evs.map(e => ({
        time:   istTime(e.timestamp),
        track:  e.metadata.track_name,
        artist: e.metadata.artist,
      }));
      if (el) Plotly.purge(el);
      return;
    }

    const n = r === 'monthly' ? 29 : r === '6m' ? 179 : 364;
    cachedEvents = await (await fetch(`/api/events?source=spotify&date_from=${daysAgoIST(n)}`)).json();
    drawChart();
  }

  onMount(async () => {
    await loadChart('monthly');
    unsubTheme = musicTheme.subscribe(() => drawChart());
  });

  onDestroy(() => {
    unsubTheme?.();
    if (el) Plotly.purge(el);
  });
</script>

<div style="background:{$musicTheme.card}" class="rounded-xl p-4 h-full flex flex-col">
  <div class="flex items-center gap-2 justify-end mb-3">
    {#each RANGES as r}
      <button
        on:click={() => loadChart(r.key)}
        style="{range === r.key
          ? `background:${$musicTheme.accent};color:${$musicTheme.bg}`
          : `color:${$musicTheme.muted}`}"
        class="px-2 py-0.5 rounded text-xs"
      >{r.label}</button>
    {/each}
  </div>

  {#if range === 'daily'}
    <div class="flex flex-col gap-1 overflow-y-auto flex-1" style="scrollbar-width:none; -ms-overflow-style:none">
      {#each dailyTracks as t}
        <div class="flex items-center gap-3 px-3 py-1.5 rounded-lg" style="background:{$musicTheme.bg}">
          <span class="text-xs w-10 shrink-0" style="color:{$musicTheme.muted}">{t.time}</span>
          <span class="text-sm truncate" style="color:{$musicTheme.text}">{t.track}</span>
          <span class="text-xs truncate" style="color:{$musicTheme.muted}">{t.artist}</span>
        </div>
      {:else}
        <p class="text-sm" style="color:{$musicTheme.muted}">No plays yet today.</p>
      {/each}
    </div>
  {:else}
    <div bind:this={el} class="flex-1"></div>
  {/if}
</div>
