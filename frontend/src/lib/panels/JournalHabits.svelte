<script>
  import { onMount } from 'svelte';
  let habits = [];
  let showForm = false;
  let newName = '', newColor = '#6b9e6b';
  const COLORS = ['#6b9e6b','#6b9ecc','#9b7ec8','#c89a5a','#c87a7a','#5abfbf'];

  async function load() {
    habits = await (await fetch('/api/habits')).json();
  }
  async function toggle(id) {
    await fetch(`/api/habits/${id}/checkin`, { method: 'POST' });
    load();
  }
  async function deleteHabit(id) {
    await fetch(`/api/habits/${id}`, { method: 'DELETE' });
    load();
  }
  async function create() {
    if (!newName.trim()) return;
    await fetch('/api/habits', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName.trim(), color: newColor }),
    });
    newName = ''; newColor = '#6b9e6b'; showForm = false;
    load();
  }
  onMount(load);
</script>

<div class="bg-[#242019] rounded-xl p-4 min-w-[240px]">
  <div class="flex items-center gap-3 mb-3">
    <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider flex-1">Habits Today</div>
    <button on:click={() => showForm=!showForm}
      class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-2 py-0.5 rounded text-xs">
      {showForm ? 'Cancel' : '+'}
    </button>
  </div>

  {#if showForm}
    <div class="bg-[#1a1714] rounded-lg p-3 mb-3 flex flex-col gap-2">
      <input type="text" bind:value={newName} placeholder="Habit name"
        class="bg-[#242019] text-[#e8e0d0] rounded-lg px-2 py-1.5 text-sm border border-[#3a3530]" />
      <div class="flex gap-1.5">
        {#each COLORS as c}
          <button on:click={() => newColor=c}
            class="w-5 h-5 rounded-full border-2 transition-all"
            style="background:{c};border-color:{newColor===c?'#e8e0d0':'transparent'}">
          </button>
        {/each}
      </div>
      <button on:click={create}
        class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-3 py-1 rounded-lg text-xs self-start">Add</button>
    </div>
  {/if}

  {#if habits.length === 0}
    <p class="text-sm text-[#9a9080]">No habits yet.</p>
  {:else}
    <div class="flex flex-col gap-2">
      {#each habits as h}
        <div class="flex items-center gap-3 group">
          <button on:click={() => toggle(h.id)}
            class="w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-all"
            style="border-color:{h.color};background:{h.done_today?h.color:'transparent'}">
            {#if h.done_today}<span class="text-[#1a1714] text-xs font-bold">✓</span>{/if}
          </button>
          <span class="text-sm flex-1" style="color:{h.done_today?h.color:'#e8e0d0'}">{h.name}</span>
          <button on:click={() => deleteHabit(h.id)}
            class="text-xs text-[#c87a7a] hover:text-[#e87a7a] opacity-0 group-hover:opacity-100 transition-opacity">✕</button>
        </div>
      {/each}
    </div>
  {/if}
</div>
