<script>
  import { onMount } from 'svelte';
  let season = '', schedule = [], drivers = [], constructors = [];
  let selectedRace = null, raceResults = null;

  $: nextRace = schedule.find(r => !r.completed);
  $: daysToNext = nextRace ? Math.ceil((new Date(nextRace.date)-new Date())/86400000) : null;
  $: completedCount = schedule.filter(r => r.completed).length;

  function fmt(dateStr) {
    return new Date(dateStr).toLocaleDateString('en-US',{month:'short',day:'numeric'});
  }
  async function openRace(race) {
    if (!race.completed) return;
    selectedRace = race; raceResults = null;
    const r = await fetch(`/api/f1/race-results/${race.round}`);
    raceResults = await r.json();
  }

  onMount(async () => {
    const [schRes, standRes] = await Promise.all([fetch('/api/f1/schedule'), fetch('/api/f1/standings')]);
    const schData = await schRes.json();
    season = schData.season; schedule = schData.races;
    const stands = await standRes.json();
    drivers = stands.drivers; constructors = stands.constructors;
  });
</script>

<div class="w-full">
  {#if nextRace}
    <div class="bg-[#242019] rounded-xl p-4 mb-4">
      <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-2">F1 {season}</div>
      <div class="text-base font-medium">{nextRace.name}</div>
      <div class="text-sm text-[#9a9080]">{nextRace.circuit} · {fmt(nextRace.date)}</div>
      <div class="text-xs text-[#c8813a] mt-1">
        {daysToNext===0?'Race day':daysToNext===1?'Tomorrow':`${daysToNext} days away`}
      </div>
    </div>
  {/if}

  <div class="grid grid-cols-3 gap-4">
    <!-- Calendar -->
    <div class="bg-[#242019] rounded-xl p-4">
      <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">
        Calendar · {completedCount}/{schedule.length}
      </div>
      <div class="space-y-0.5 max-h-80 overflow-y-auto">
        {#each schedule as race}
          <button on:click={() => openRace(race)}
            class="w-full text-left flex items-center gap-2 px-2 py-1.5 rounded-lg transition-colors
              {race.completed?'opacity-40 hover:opacity-70 cursor-pointer':'cursor-default'}
              {nextRace?.round===race.round?'text-[#c8813a] opacity-100':''}
              hover:bg-[#2a2520]">
            <span class="text-xs text-[#9a9080] w-4 shrink-0 tabular-nums">{race.round}</span>
            <div class="flex-1 min-w-0">
              <div class="text-xs truncate">{race.name.replace(' Grand Prix',' GP')}</div>
              <div class="text-[10px] text-[#9a9080]">{race.country} · {fmt(race.date)}</div>
            </div>
            {#if race.completed}<span class="text-[10px] text-[#9a9080] shrink-0">✓</span>{/if}
          </button>
        {/each}
      </div>
    </div>

    <!-- Drivers -->
    <div class="bg-[#242019] rounded-xl p-4">
      <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Drivers</div>
      <div class="space-y-2">
        {#each drivers.slice(0,10) as d}
          <div class="flex items-center gap-2">
            <span class="text-xs text-[#9a9080] w-4 shrink-0 tabular-nums">{d.position}</span>
            <div class="flex-1 min-w-0">
              <div class="text-xs font-medium truncate">{d.driver}</div>
              <div class="text-[10px] text-[#9a9080] truncate">{d.team}</div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-xs font-medium tabular-nums">{d.points}</div>
              {#if d.wins>0}<div class="text-[10px] text-[#9a9080]">{d.wins}W</div>{/if}
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Constructors -->
    <div class="bg-[#242019] rounded-xl p-4">
      <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Constructors</div>
      <div class="space-y-2">
        {#each constructors as c}
          <div class="flex items-center gap-2">
            <span class="text-xs text-[#9a9080] w-4 shrink-0 tabular-nums">{c.position}</span>
            <div class="flex-1 min-w-0">
              <div class="text-xs font-medium truncate">{c.team}</div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-xs font-medium tabular-nums">{c.points}</div>
              {#if c.wins>0}<div class="text-[10px] text-[#9a9080]">{c.wins}W</div>{/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  </div>
</div>

{#if selectedRace}
  <div class="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4"
    on:click|self={() => { selectedRace=null; raceResults=null; }}>
    <div class="bg-[#242019] rounded-2xl p-6 max-w-md w-full shadow-2xl">
      <div class="flex items-start justify-between mb-4">
        <div>
          <div class="text-lg font-semibold">{selectedRace.name}</div>
          <div class="text-sm text-[#9a9080]">{selectedRace.circuit}</div>
        </div>
        <button on:click={() => {selectedRace=null;raceResults=null;}} class="text-[#9a9080] hover:text-[#e8e0d0]">✕</button>
      </div>
      {#if !raceResults}
        <p class="text-sm text-[#9a9080] animate-pulse">Loading results…</p>
      {:else}
        <div class="space-y-1.5 max-h-80 overflow-y-auto">
          {#each raceResults.results as r}
            <div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-[#1a1714]">
              <span class="text-xs text-[#9a9080] w-4 tabular-nums shrink-0">{r.position}</span>
              <div class="flex-1 min-w-0">
                <div class="text-sm truncate">{r.driver}</div>
                <div class="text-xs text-[#9a9080] truncate">{r.team}</div>
              </div>
              <div class="text-right shrink-0">
                <div class="text-xs font-medium tabular-nums">{r.points}pt</div>
                {#if r.fastest_lap}<div class="text-[10px] text-[#9b7ec8]">⚡ fastest</div>{/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
{/if}
