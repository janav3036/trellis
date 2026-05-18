<script>
  import { onMount, onDestroy } from 'svelte';
  import Plotly from 'plotly.js-dist-min';

  let el;
  // Ferrari red, McLaren orange, Mercedes teal, Red Bull blue, Alpine yellow
  const COLORS = ['#e8002d', '#FF8000', '#27F4D2', '#3671C6', '#E8D60A'];

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
        autosize: true,
        paper_bgcolor: '#18181c', plot_bgcolor: '#18181c',
        font: { color: '#888', family: 'inherit' },
        xaxis: { showgrid: false, zeroline: false, tickangle: -45, tickfont: { size: 9 }, color: '#555' },
        yaxis: { showgrid: false, zeroline: false, title: '', tickfont: { size: 9 }, color: '#555' },
        legend: { bgcolor: 'transparent', orientation: 'h', y: -0.25, font: { size: 10 } },
        margin: { t: 10, r: 20, b: 60, l: 40 },
      },
      { responsive: true }
    );
  });
  onDestroy(() => { if (el) Plotly.purge(el); });
</script>

<div class="rounded-xl p-4 w-full h-full flex flex-col" style="background:#18181c">
  <div class="text-xs font-bold uppercase tracking-widest mb-2 shrink-0" style="color:#444">Championship Arc — Top 5</div>
  <div bind:this={el} class="flex-1 min-h-0"></div>
</div>
