<script>
  import { onMount, onDestroy } from 'svelte';
  import Plotly from 'plotly.js-dist-min';
  import { daysAgoIST, buildDatesIST, groupByDayIST, groupByWeekIST } from '../ist.js';

  let el;
  let range = 'monthly';

  const RANGES = [
    { key: 'daily',   label: 'Today' },
    { key: 'monthly', label: '30 days' },
    { key: '6m',      label: '6 months' },
    { key: 'yearly',  label: 'Year' },
  ];

  const layout = {
    paper_bgcolor: '#1a1714', plot_bgcolor: '#1a1714',
    font: { color: '#e8e0d0' },
    xaxis: { gridcolor: '#242019', tickcolor: '#9a9080' },
    yaxis: { gridcolor: '#242019', tickcolor: '#9a9080', title: 'commits', rangemode: 'tozero' },
    margin: { t: 10, r: 20, b: 60, l: 50 },
  };

  let dailyCommits = [];

  async function loadChart(r) {
    range = r;
    dailyCommits = [];
    if (r === 'daily') {
      dailyCommits = await (await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(0)}`)).json();
      if (el) Plotly.purge(el);
      return;
    }
    let evs, dates, counts, title;
    if (r === 'monthly') {
      evs = await (await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(29)}`)).json();
      dates = buildDatesIST(30); counts = groupByDayIST(evs); title = 'GitHub — last 30 days';
    } else if (r === '6m') {
      evs = await (await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(179)}`)).json();
      dates = buildDatesIST(180); counts = groupByDayIST(evs); title = 'GitHub — last 6 months';
    } else {
      evs = await (await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(364)}`)).json();
      counts = groupByWeekIST(evs); dates = Object.keys(counts).sort(); title = 'GitHub — last year';
    }
    Plotly.react(el, [{ x: dates, y: dates.map(d => counts[d] || 0), type: 'bar', marker: { color: '#6b9e6b' } }],
      { ...layout, title: { text: title, font: { color: '#e8e0d0', size: 12 } } });
  }

  onMount(() => loadChart('monthly'));
  onDestroy(() => { if (el) Plotly.purge(el); });
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="flex items-center gap-2 mb-3">
    <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider flex-1">Commits</div>
    {#each RANGES as r}
      <button
        on:click={() => loadChart(r.key)}
        class="px-2 py-0.5 rounded text-xs {range === r.key ? 'bg-[#6b9e6b] text-[#1a1714]' : 'text-[#9a9080] hover:text-[#e8e0d0]'}"
      >{r.label}</button>
    {/each}
  </div>
  {#if range === 'daily'}
    <div class="flex flex-col gap-1 max-h-64 overflow-y-auto">
      {#each dailyCommits as c}
        <div class="flex items-center gap-3 px-3 py-1.5 rounded bg-[#1a1714]">
          <span class="text-xs text-[#6b9e6b] font-mono shrink-0">{c.metadata.repo?.split('/')[1]}</span>
          <span class="text-sm truncate">{c.metadata.message}</span>
        </div>
      {:else}
        <p class="text-sm text-[#9a9080]">No commits today.</p>
      {/each}
    </div>
  {:else}
    <div bind:this={el}></div>
  {/if}
</div>
