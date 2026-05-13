<script>
  import { onMount } from "svelte";
  import Plotly from "plotly.js-dist-min";

  let season = "";
  let schedule = [];
  let drivers = [];
  let constructors = [];
  let news = [];
  let arcEl;
  let selectedRace = null;
  let raceResults = null;

  $: nextRace = schedule.find(r => !r.completed);
  $: daysToNext = nextRace
    ? Math.ceil((new Date(nextRace.date) - new Date()) / 86400000)
    : null;
  $: completedCount = schedule.filter(r => r.completed).length;

  const COLORS = ["#c8813a", "#4dabf7", "#69db7c", "#ffd43b", "#f783ac"];

  const arcLayout = {
    paper_bgcolor: "#242019",
    plot_bgcolor: "#242019",
    font: { color: "#e8e0d0" },
    xaxis: { gridcolor: "#1a1714", tickangle: -45, tickfont: { size: 10 } },
    yaxis: { gridcolor: "#1a1714", title: "Points" },
    legend: { bgcolor: "#242019" },
    margin: { t: 20, r: 20, b: 100, l: 60 },
  };

  function fmt(dateStr) {
    return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }

  async function openRace(race) {
    if (!race.completed) return;
    selectedRace = race;
    raceResults = null;
    const res = await fetch(`/api/f1/race-results/${race.round}`);
    raceResults = await res.json();
  }

  onMount(async () => {
    const [schRes, standRes, newsRes] = await Promise.all([
      fetch("/api/f1/schedule"),
      fetch("/api/f1/standings"),
      fetch("/api/f1/news"),
    ]);
    const schData = await schRes.json();
    season = schData.season;
    schedule = schData.races;
    const stands = await standRes.json();
    drivers = stands.drivers;
    constructors = stands.constructors;
    news = await newsRes.json();

    const arcRes = await fetch("/api/f1/season-arc");
    const arcData = await arcRes.json();
    if (arcData.races.length) {
      Plotly.react(arcEl, Object.entries(arcData.drivers).map(([name, pts], i) => ({
        x: arcData.races,
        y: pts,
        name,
        type: "scatter",
        mode: "lines+markers",
        line: { color: COLORS[i], width: 2 },
        marker: { size: 5 },
      })), arcLayout);
    }
  });
</script>

<main class="p-8 bg-[#1a1714] min-h-screen text-[#e8e0d0]">

  <!-- Header -->
  <div class="flex items-center justify-between mb-8">
    <h1 class="text-3xl font-semibold">F1 {season}</h1>
    {#if nextRace}
      <div class="text-right">
        <div class="text-base font-medium">{nextRace.name}</div>
        <div class="text-sm text-[#9a9080]">{nextRace.circuit} · {fmt(nextRace.date)}</div>
        <div class="text-xs text-[#c8813a] mt-1">
          {daysToNext === 0 ? "Race day" : daysToNext === 1 ? "Tomorrow" : `${daysToNext} days away`}
        </div>
      </div>
    {/if}
  </div>

  <!-- Calendar + Standings -->
  <div class="grid grid-cols-3 gap-6 mb-8">

    <!-- Calendar -->
    <div class="bg-[#242019] rounded-xl p-4">
      <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">
        Calendar · {completedCount}/{schedule.length}
      </h2>
      <div class="space-y-0.5 max-h-96 overflow-y-auto pr-1">
        {#each schedule as race}
          <button
            on:click={() => openRace(race)}
            class="w-full text-left flex items-center gap-3 px-2 py-1.5 rounded-lg transition-colors
              {race.completed ? 'opacity-40 hover:opacity-70 cursor-pointer' : 'cursor-default'}
              {nextRace?.round === race.round ? 'text-[#c8813a] opacity-100' : ''}
              hover:bg-[#2a2520]"
          >
            <span class="text-xs text-[#9a9080] w-5 shrink-0 tabular-nums">{race.round}</span>
            <div class="flex-1 min-w-0">
              <div class="text-sm truncate">{race.name.replace(" Grand Prix", " GP")}</div>
              <div class="text-xs text-[#9a9080]">{race.country} · {fmt(race.date)}</div>
            </div>
            {#if race.completed}
              <span class="text-xs text-[#9a9080] shrink-0">✓</span>
            {/if}
          </button>
        {/each}
      </div>
    </div>

    <!-- Driver standings -->
    <div class="bg-[#242019] rounded-xl p-4">
      <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Drivers</h2>
      <div class="space-y-2">
        {#each drivers.slice(0, 10) as d}
          <div class="flex items-center gap-3">
            <span class="text-xs text-[#9a9080] w-4 shrink-0 tabular-nums">{d.position}</span>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium truncate">{d.driver}</div>
              <div class="text-xs text-[#9a9080] truncate">{d.team}</div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-sm font-medium tabular-nums">{d.points}</div>
              {#if d.wins > 0}
                <div class="text-xs text-[#9a9080]">{d.wins}W</div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Constructor standings -->
    <div class="bg-[#242019] rounded-xl p-4">
      <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Constructors</h2>
      <div class="space-y-2">
        {#each constructors as c}
          <div class="flex items-center gap-3">
            <span class="text-xs text-[#9a9080] w-4 shrink-0 tabular-nums">{c.position}</span>
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium truncate">{c.team}</div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-sm font-medium tabular-nums">{c.points}</div>
              {#if c.wins > 0}
                <div class="text-xs text-[#9a9080]">{c.wins}W</div>
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>

  </div>

  <!-- Season arc -->
  <div class="bg-[#242019] rounded-xl p-4 mb-8">
    <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Championship Arc — Top 5</h2>
    <div bind:this={arcEl}></div>
  </div>

  <!-- News -->
  <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-4">Latest News</h2>
  <div class="grid grid-cols-3 gap-4">
    {#each news as item}
      <a
        href={item.link}
        target="_blank"
        rel="noopener noreferrer"
        class="bg-[#242019] rounded-xl p-4 hover:bg-[#2a2520] transition-colors block"
      >
        <div class="text-sm font-medium leading-snug mb-3">{item.title}</div>
        <div class="flex items-center gap-2 text-xs text-[#9a9080]">
          <span>{item.source}</span>
          {#if item.published}
            <span>·</span>
            <span>{item.published}</span>
          {/if}
        </div>
      </a>
    {/each}
  </div>

</main>

<!-- Race result modal -->
{#if selectedRace}
  <div
    class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
    on:click|self={() => { selectedRace = null; raceResults = null; }}
  >
    <div class="bg-[#242019] rounded-2xl w-full max-w-md max-h-[80vh] flex flex-col">
      <div class="p-5 border-b border-[#1a1714]">
        <div class="flex items-start justify-between">
          <div>
            <div class="text-base font-semibold">{selectedRace.name}</div>
            <div class="text-sm text-[#9a9080] mt-0.5">{selectedRace.circuit} · {fmt(selectedRace.date)}</div>
          </div>
          <button
            on:click={() => { selectedRace = null; raceResults = null; }}
            class="text-[#9a9080] hover:text-[#e8e0d0] text-xl leading-none ml-4"
          >×</button>
        </div>
      </div>
      <div class="overflow-y-auto p-5">
        {#if !raceResults}
          <p class="text-sm text-[#9a9080]">Loading…</p>
        {:else}
          <div class="space-y-1">
            {#each raceResults.results as r}
              <div class="flex items-center gap-3 py-1.5">
                <span class="text-xs text-[#9a9080] w-5 shrink-0 tabular-nums">{r.position}</span>
                <div class="flex-1 min-w-0">
                  <span class="text-sm font-medium">{r.driver}</span>
                  {#if r.fastest_lap}
                    <span class="text-xs text-[#f783ac] ml-1">⚡</span>
                  {/if}
                  <div class="text-xs text-[#9a9080]">{r.team}</div>
                </div>
                <div class="text-right shrink-0">
                  <div class="text-sm tabular-nums">{r.points > 0 ? `+${r.points}` : ""}</div>
                  {#if r.status !== "Finished"}
                    <div class="text-xs text-[#9a9080]">{r.status}</div>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
