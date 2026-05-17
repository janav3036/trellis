<script>
  import { onMount, onDestroy } from 'svelte';
  import Plotly from 'plotly.js-dist-min';

  let el;
  let range = '30d';

  const RANGES = [
    { key: '30d',  label: '30 days',  n: 30 },
    { key: '90d',  label: '90 days',  n: 90 },
    { key: '180d', label: '6 months', n: 180 },
  ];

  function daysAgo(n) {
    const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().split('T')[0];
  }

  async function loadChart(r) {
    range = r.key;
    const evs = await (await fetch(`/api/events?source=weather&event_type=daily&date_from=${daysAgo(r.n)}`)).json();
    const x = evs.map(e => e.timestamp.split('T')[0]).reverse();
    const yMax = evs.map(e => e.metadata.temp_max).reverse();
    const yMin = evs.map(e => e.metadata.temp_min).reverse();
    const precip = evs.map(e => e.metadata.precipitation).reverse();
    Plotly.react(el, [
      { x, y: yMax, name: 'High', type: 'scatter', mode: 'lines', line: { color: '#c87941', width: 2 } },
      { x, y: yMin, name: 'Low',  type: 'scatter', mode: 'lines', line: { color: '#6b9ecc', width: 2 } },
      { x, y: precip, name: 'Precip (mm)', type: 'bar', yaxis: 'y2', marker: { color: '#4a7a9b', opacity: 0.5 } },
    ], {
      paper_bgcolor: '#1a1714', plot_bgcolor: '#1a1714',
      font: { color: '#e8e0d0' },
      xaxis: { gridcolor: '#242019', tickcolor: '#9a9080' },
      yaxis: { gridcolor: '#242019', tickcolor: '#9a9080', title: '°C' },
      yaxis2: { overlaying: 'y', side: 'right', title: 'mm', showgrid: false },
      legend: { bgcolor: '#1a1714' },
      margin: { t: 10, r: 60, b: 60, l: 50 },
    });
  }

  onMount(() => loadChart(RANGES[0]));
  onDestroy(() => { if (el) Plotly.purge(el); });
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="flex items-center gap-2 mb-3">
    <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider flex-1">Temperature Trend</div>
    {#each RANGES as r}
      <button
        on:click={() => loadChart(r)}
        class="px-2 py-0.5 rounded text-xs {range === r.key ? 'bg-[#6b9e6b] text-[#1a1714]' : 'text-[#9a9080] hover:text-[#e8e0d0]'}"
      >{r.label}</button>
    {/each}
  </div>
  <div bind:this={el}></div>
</div>
