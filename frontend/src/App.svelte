<script>
import { onMount } from "svelte";
import Plotly from 'plotly.js-dist-min'

let chartEl
let githubEl

onMount(async () => {
  const dateFrom = new Date()
  dateFrom.setDate(dateFrom.getDate()-7)
  const dateFromStr = dateFrom.toISOString().split('T')[0]

  const res = await fetch(`/api/events?source=spotify&date_from=${dateFromStr}`)
  const events = await res.json()

  const counts = {}
  for (const event of events) {
    const day = event.timestamp.split('T')[0]
    counts[day] = (counts[day] || 0 )+1
  }

  const dates = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    dates.push(d.toISOString().split('T')[0])
  }
  const plays = dates.map(d => counts[d] || 0)

  Plotly.newPlot(chartEl, [{
    x: dates,
      y: plays,
      type: 'bar',
      marker: { color: '#c8813a' }
    }], {
      paper_bgcolor: '#1a1714',
      plot_bgcolor: '#1a1714',
      font: { color: '#e8e0d0' },
      xaxis: { gridcolor: '#242019', tickcolor: '#9a9080' },
      yaxis: { gridcolor: '#242019', tickcolor: '#9a9080', title: 'plays', rangemode:"tozero"},
      margin: { t: 40, r: 20, b: 60, l: 50 },
      title: { text: 'Spotify — last 7 days', font: { color: '#e8e0d0' } }
  })

  const ghRes = await fetch(`/api/events?source=github&event_type=commit&date_from=${dateFromStr}`)
  const ghEvents = await ghRes.json()

  const ghCounts = {}
  for (const event of ghEvents) {
    const day = event.timestamp.split('T')[0]
    ghCounts[day] = (ghCounts[day] || 0) + 1
  }
  const ghPlays = dates.map(d => ghCounts[d] || 0)

  Plotly.newPlot(githubEl, [{
    x: dates,
    y:ghPlays,
    type: 'bar',
    marker: {color: '#6b8c6b'}
  }], {
    paper_bgcolor: '#1a1714',
    plot_bgcolor: '#1a1714',
    font: { color: '#e8e0d0' },
    xaxis: { gridcolor: '#242019', tickcolor: '#9a9080' },
    yaxis: { gridcolor: '#242019', tickcolor: '#9a9080', title: 'commits', rangemode: 'tozero' },
    margin: { t: 40, r: 20, b: 60, l: 50 },
    title: { text: 'GitHub — last 7 days', font: { color: '#e8e0d0' } }
  })

})


</script>

<main>
  <h1>Trellis</h1>
  <div bind:this={chartEl}></div>
  <div bind:this={githubEl}></div>
</main>