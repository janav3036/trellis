<script>
  import { onMount } from "svelte";
  import Plotly from "plotly.js-dist-min";

  let chartEl;
  let nowPlaying = null;
  let playlists = [];
  let backfillDate = "";
  let backfillStatus = "";
  let range = "monthly";
  let dailyTracks = [];

  const RANGES = [
    { key: "daily",   label: "Today" },
    { key: "monthly", label: "30 days" },
    { key: "6m",      label: "6 months" },
    { key: "yearly",  label: "Year" },
  ];

  const plotLayout = {
    paper_bgcolor: "#1a1714",
    plot_bgcolor: "#1a1714",
    font: { color: "#e8e0d0" },
    xaxis: { gridcolor: "#242019", tickcolor: "#9a9080" },
    yaxis: { gridcolor: "#242019", tickcolor: "#9a9080", title: "plays", rangemode: "tozero" },
    margin: { t: 40, r: 20, b: 60, l: 50 },
  };

  function startOfDay() {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d.toISOString().split("T")[0];
  }

  function daysAgo(n) {
    const d = new Date();
    d.setDate(d.getDate() - n);
    return d.toISOString().split("T")[0];
  }

  function buildDates(n) {
    return Array.from({ length: n }, (_, i) => daysAgo(n - 1 - i));
  }

  function groupByDay(events) {
    const counts = {};
    for (const e of events) {
      const day = e.timestamp.split("T")[0];
      counts[day] = (counts[day] || 0) + 1;
    }
    return counts;
  }

  function groupByWeek(events) {
  const counts = {};
  for (const e of events) {
    const d = new Date(e.timestamp);
    const dayOfWeek = d.getUTCDay();
    const weekStart = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() - dayOfWeek));
    const week = weekStart.toISOString().split("T")[0];
    counts[week] = (counts[week] || 0) + 1;
  }
  return counts;
}


  async function loadChart(r) {
    range = r;
    dailyTracks = [];

    if (r === "daily") {
      const res = await fetch(`/api/events?source=spotify&date_from=${startOfDay()}`);
      const events = await res.json();
      dailyTracks = events.map(e => ({
        time: new Date(e.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        track: e.metadata.track_name,
        artist: e.metadata.artist,
      }));
      if (chartEl) Plotly.purge(chartEl);
      return;
    }

    let events, dates, counts, title;

    if (r === "monthly") {
      const res = await fetch(`/api/events?source=spotify&date_from=${daysAgo(29)}`);
      events = await res.json();
      dates = buildDates(30);
      counts = groupByDay(events);
      title = "Spotify — last 30 days";
    } else if (r === "6m") {
      const res = await fetch(`/api/events?source=spotify&date_from=${daysAgo(179)}`);
      events = await res.json();
      dates = buildDates(180);
      counts = groupByDay(events);
      title = "Spotify — last 6 months";
    } else {
      const res = await fetch(`/api/events?source=spotify&date_from=${daysAgo(364)}`);
      events = await res.json();
      counts = groupByWeek(events);
      dates = Object.keys(counts).sort();
      title = "Spotify — last year (by week)";
    }

    Plotly.react(chartEl, [{
      x: dates,
      y: dates.map(d => counts[d] || 0),
      type: "bar",
      marker: { color: "#c8813a" },
    }], { ...plotLayout, title: { text: title, font: { color: "#e8e0d0" } } });
  }

  async function fetchNowPlaying() {
    const res = await fetch("/api/now-playing");
    nowPlaying = await res.json();
  }

  onMount(async () => {
    const [plRes] = await Promise.all([
      fetch("/api/playlists"),
      loadChart("monthly"),
      fetchNowPlaying(),
    ]);
    playlists = (await plRes.json()).sort((a, b) => a.name.localeCompare(b.name));
    setInterval(fetchNowPlaying, 10000);
  });
</script>

<main class="p-8 bg-[#1a1714] min-h-screen text-[#e8e0d0]">
  <h1 class="text-3xl font-semibold mb-8">Music</h1>

  <div class="flex items-center justify-between mb-8">
    {#if nowPlaying}
      <div class="flex items-center gap-4 p-4 rounded-xl bg-[#242019]">
        {#if nowPlaying.cover}
          <img src={nowPlaying.cover} alt="album art" class="w-16 h-16 rounded-lg" />
        {/if}
        <div>
          <div class="text-base font-semibold">{nowPlaying.track}</div>
          <div class="text-sm text-[#9a9080]">{nowPlaying.artist}</div>
          <div class="text-xs text-[#9a9080] mt-1">{nowPlaying.album}</div>
        </div>
      </div>
    {:else}
      <div></div>
    {/if}
    <div class="flex items-center gap-2">
      <input
        type="date"
        bind:value={backfillDate}
        class="bg-[#242019] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
      />
      <button
        on:click={async () => {
          if (!backfillDate) return;
          backfillStatus = "running…";
          const res = await fetch("/api/backfill/spotify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ date_from: backfillDate }),
          });
          const data = await res.json();
          backfillStatus = `${data.count} new events`;
        }}
        class="bg-[#c8813a] hover:bg-[#b5722e] text-[#1a1714] font-medium px-4 py-2 rounded-lg text-sm"
      >
        Backfill
      </button>
      {#if backfillStatus}
        <span class="text-sm text-[#9a9080]">{backfillStatus}</span>
      {/if}
    </div>
  </div>

  <div class="flex gap-2 mb-4">
    {#each RANGES as r}
      <button
        on:click={() => loadChart(r.key)}
        class="px-4 py-1.5 rounded-lg text-sm font-medium transition-colors
          {range === r.key ? 'bg-[#c8813a] text-[#1a1714]' : 'bg-[#242019] text-[#9a9080] hover:text-[#e8e0d0]'}"
      >
        {r.label}
      </button>
    {/each}
  </div>

  {#if range === "daily"}
    <div class="flex flex-col gap-2 max-w-xl">
      {#each dailyTracks as t}
        <div class="flex items-center gap-4 px-4 py-2 rounded-lg bg-[#242019]">
          <span class="text-xs text-[#9a9080] w-12 shrink-0">{t.time}</span>
          <span class="text-sm font-medium truncate">{t.track}</span>
          <span class="text-xs text-[#9a9080] truncate">{t.artist}</span>
        </div>
      {:else}
        <p class="text-[#9a9080] text-sm">No plays yet today.</p>
      {/each}
    </div>
  {:else}
    <div bind:this={chartEl}></div>
  {/if}

  <h2 class="text-xl font-semibold mt-10 mb-4">Playlists</h2>
  <div class="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-4">
    {#each playlists as p}
      <div class="bg-[#242019] rounded-xl overflow-hidden">
        {#if p.cover}
          <img src={p.cover} alt={p.name} class="w-full aspect-square object-cover" />
        {/if}
        <div class="p-3">
          <div class="text-sm font-medium truncate">{p.name}</div>
          <div class="text-xs text-[#9a9080] mt-1">{p.track_count} tracks</div>
        </div>
      </div>
    {/each}
  </div>
</main>
