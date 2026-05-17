<script>
  import { onMount, onDestroy } from 'svelte';
  import Plotly from 'plotly.js-dist-min';

  let el;
  const COLORS = ['#c8813a','#4dabf7','#69db7c','#ffd43b','#f783ac'];

  onMount(async () => {
    const r = await fetch('/api/f1/season-arc');
    const data = await r.json();
    if (!data.races.length) return;
    Plotly.react(el,
      Object.entries(data.drivers).map(([name,pts],i) => ({
        x: data.races, y: pts, name,
        type: 'scatter', mode: 'lines+markers',
        line: { color: COLORS[i], width: 2 },
        marker: { size: 5 },
      })),
      {
        paper_bgcolor: '#242019', plot_bgcolor: '#242019',
        font: { color: '#e8e0d0' },
        xaxis: { gridcolor: '#1a1714', tickangle: -45, tickfont: { size: 9 } },
        yaxis: { gridcolor: '#1a1714', title: 'Points' },
        legend: { bgcolor: '#242019' },
        margin: { t: 10, r: 20, b: 100, l: 60 },
      }
    );
  });
  onDestroy(() => { if (el) Plotly.purge(el); });
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Championship Arc — Top 5</div>
  <div bind:this={el}></div>
</div>
