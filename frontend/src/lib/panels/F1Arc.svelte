<script>
  import { onMount, onDestroy } from 'svelte';
  import Plotly from 'plotly.js-dist-min';

  let el;
  const COLORS = ['#e8002d', '#FF8000', '#27F4D2', '#3671C6', '#E8D60A'];

  onMount(async () => {
    const r = await fetch('/api/f1/season-arc');
    const data = await r.json();
    if (!data.races.length) return;

    Plotly.react(el,
      Object.entries(data.drivers).map(([name, pts], i) => ({
        x: data.races, y: pts, name,
        type: 'scatter', mode: 'lines+markers',
        line: { color: COLORS[i % COLORS.length], width: 1.5, shape: 'spline', smoothing: 0.6 },
        marker: { size: 4, color: COLORS[i % COLORS.length] },
        hovertemplate: `<b>%{fullData.name}</b><br>%{x}: %{y} pts<extra></extra>`,
      })),
      {
        autosize: true,
        paper_bgcolor: '#18181c',
        plot_bgcolor: '#18181c',
        font: { color: '#555', family: 'Barlow Condensed, system-ui, sans-serif', size: 11 },
        xaxis: {
          showgrid: false,
          zeroline: false,
          tickangle: -45,
          tickfont: { size: 9, color: '#3a3a44' },
          color: '#2a2a32',
          linecolor: '#222228',
          ticklen: 4,
        },
        yaxis: {
          showgrid: true,
          gridcolor: 'rgba(255,255,255,0.03)',
          zeroline: false,
          title: '',
          tickfont: { size: 9, color: '#3a3a44' },
          color: '#2a2a32',
        },
        legend: {
          bgcolor: 'transparent',
          orientation: 'h',
          x: 0,
          y: -0.28,
          font: { size: 10, color: '#888' },
          traceorder: 'normal',
        },
        margin: { t: 8, r: 16, b: 64, l: 36 },
        hoverlabel: {
          bgcolor: '#0d0d0f',
          bordercolor: '#2a2a35',
          font: { color: '#f0f0f2', size: 11 },
        },
      },
      { responsive: true, displayModeBar: false }
    );
  });

  onDestroy(() => { if (el) Plotly.purge(el); });
</script>

<div class="arc-panel">
  <div class="arc-eyebrow">Championship Arc — Top 5</div>
  <div bind:this={el} class="arc-chart"></div>
</div>

<style>
  .arc-panel {
    background: #18181c;
    border-radius: 14px;
    padding: 14px 14px 8px;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    overflow: hidden;
  }
  .arc-eyebrow {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: #383840;
    flex-shrink: 0;
    margin-bottom: 4px;
  }
  .arc-chart {
    flex: 1;
    min-height: 0;
  }
</style>
