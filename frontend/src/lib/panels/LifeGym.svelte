<script>
  import { onMount } from 'svelte';
  let sessions = [];
  let showForm = false;
  let gymDate = new Date().toISOString().slice(0,10);
  let gymType = 'workout';
  let gymMuscles = [];
  let gymDistance = '';
  let gymDuration = '';
  let gymNotes = '';
  let status = '';

  function formatDuration(mins) {
    if (!mins) return '';
    const h = Math.floor(mins/60), m = mins%60;
    if (h===0) return `${m}m`; if (m===0) return `${h}h`; return `${h}h ${m}m`;
  }
  function timeAgo(ts) {
    const s = Math.floor((Date.now()-new Date(ts))/1000);
    if (s < 3600) return `${Math.floor(s/60)}m ago`;
    if (s < 86400) return `${Math.floor(s/3600)}h ago`;
    const d = Math.floor(s/86400);
    if (d < 30) return `${d}d ago`;
    return new Date(ts).toLocaleDateString('en-US',{month:'short',day:'numeric'});
  }
  async function load() {
    sessions = await (await fetch('/api/events?source=gym&event_type=session')).json();
  }
  async function save() {
    status = 'saving…';
    const res = await fetch('/api/gym/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: gymDate, type: gymType,
        muscle_groups: gymMuscles,
        distance_km: gymDistance ? parseFloat(gymDistance) : null,
        duration_minutes: gymDuration ? parseInt(gymDuration) : null,
        notes: gymNotes,
      }),
    });
    const data = await res.json();
    status = data.count ? 'Saved!' : 'Already logged';
    gymMuscles = []; gymDistance = ''; gymDuration = ''; gymNotes = '';
    showForm = false;
    load();
  }
  onMount(load);
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="flex items-center gap-3 mb-3">
    <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider flex-1">Gym</div>
    <button on:click={() => showForm=!showForm}
      class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-3 py-1 rounded-lg text-xs">
      {showForm ? 'Cancel' : '+ Log'}
    </button>
    {#if status}<span class="text-xs text-[#9a9080]">{status}</span>{/if}
  </div>

  {#if showForm}
    <div class="bg-[#1a1714] rounded-xl p-4 mb-4 flex flex-col gap-3">
      <div class="flex gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-xs text-[#9a9080]">Date</label>
          <input type="date" bind:value={gymDate}
            class="bg-[#242019] text-[#e8e0d0] rounded-lg px-2 py-1.5 text-sm border border-[#3a3530]" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs text-[#9a9080]">Type</label>
          <div class="flex gap-2">
            <button on:click={() => gymType='workout'}
              class="px-3 py-1.5 rounded-lg text-xs {gymType==='workout'?'bg-[#6b9e6b] text-[#1a1714]':'bg-[#242019] text-[#9a9080]'}">Workout</button>
            <button on:click={() => gymType='run'}
              class="px-3 py-1.5 rounded-lg text-xs {gymType==='run'?'bg-[#6b9e6b] text-[#1a1714]':'bg-[#242019] text-[#9a9080]'}">Run</button>
          </div>
        </div>
      </div>
      {#if gymType === 'workout'}
        <div class="flex flex-wrap gap-1.5">
          {#each ['Chest','Back','Shoulders','Biceps','Triceps','Legs','Core','Calisthenics','Boxing'] as m}
            <button on:click={() => gymMuscles=gymMuscles.includes(m)?gymMuscles.filter(x=>x!==m):[...gymMuscles,m]}
              class="px-2 py-0.5 rounded-full text-xs {gymMuscles.includes(m)?'bg-[#3d2e1a] text-[#c89a5a]':'bg-[#242019] text-[#9a9080]'}">
              {m}
            </button>
          {/each}
        </div>
      {:else}
        <input type="number" bind:value={gymDistance} placeholder="Distance km" step="0.1"
          class="bg-[#242019] text-[#e8e0d0] rounded-lg px-2 py-1.5 text-sm border border-[#3a3530] w-28" />
      {/if}
      <div class="flex gap-3">
        <input type="number" bind:value={gymDuration} placeholder="Duration min"
          class="bg-[#242019] text-[#e8e0d0] rounded-lg px-2 py-1.5 text-sm border border-[#3a3530] w-28" />
        <input type="text" bind:value={gymNotes} placeholder="Notes (optional)"
          class="bg-[#242019] text-[#e8e0d0] rounded-lg px-2 py-1.5 text-sm border border-[#3a3530] flex-1" />
      </div>
      <button on:click={save}
        class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-1.5 rounded-lg text-sm self-start">Save</button>
    </div>
  {/if}

  {#if sessions.length === 0}
    <p class="text-sm text-[#9a9080]">No sessions logged yet.</p>
  {:else}
    <div class="flex flex-col gap-2 max-h-64 overflow-y-auto">
      {#each sessions.slice(0,20) as s}
        <div class="flex items-center gap-3 px-3 py-2 rounded-lg bg-[#1a1714]">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm font-medium capitalize">{s.metadata.type}</span>
              {#each s.metadata.muscle_groups||[] as m}
                <span class="text-xs px-1.5 py-0.5 rounded-full bg-[#3d2e1a] text-[#c89a5a]">{m}</span>
              {/each}
              {#if s.metadata.distance_km}<span class="text-xs text-[#9a9080]">{s.metadata.distance_km} km</span>{/if}
            </div>
            {#if s.metadata.notes}<div class="text-xs text-[#9a9080] mt-0.5">{s.metadata.notes}</div>{/if}
          </div>
          <div class="text-right shrink-0">
            {#if s.metadata.duration_minutes}<div class="text-xs text-[#c89a5a]">{formatDuration(s.metadata.duration_minutes)}</div>{/if}
            <div class="text-xs text-[#9a9080]">{timeAgo(s.timestamp)}</div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
