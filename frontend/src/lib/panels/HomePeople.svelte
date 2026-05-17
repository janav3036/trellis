<script>
  import { onMount } from 'svelte';
  let events = [], expanded = null;

  function groupEvents(evs) {
    const map = new Map();
    for (const e of evs) {
      const key = `${e.timestamp.slice(0,10)}::${(e.metadata.notes||'').trim()}`;
      if (!map.has(key)) map.set(key, { ...e, metadata: { ...e.metadata, people: [] } });
      const g = map.get(key);
      for (const p of (e.metadata.people || [])) {
        if (!g.metadata.people.find(q => q.name === p.name)) g.metadata.people.push(p);
      }
    }
    return [...map.values()];
  }

  function timeAgo(ts) {
    const s = Math.floor((Date.now() - new Date(ts)) / 1000);
    if (s < 3600)   return `${Math.floor(s / 60)}m ago`;
    if (s < 86400)  return `${Math.floor(s / 3600)}h ago`;
    const d = Math.floor(s / 86400);
    if (d < 30)     return `${d}d ago`;
    return new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  onMount(async () => {
    const res = await fetch('/api/events?source=people&event_type=meetup');
    const all = await res.json();
    events = groupEvents(all).slice(0, 3);
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 h-full flex flex-col overflow-hidden">
  <a href="/#/life"
     class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3 shrink-0 hover:text-[#e8e0d0] transition-colors">
    People
  </a>

  {#if events.length === 0}
    <p class="text-sm text-[#9a9080]">No events logged yet.</p>
  {:else}
    <div class="flex flex-col gap-1 flex-1 overflow-y-auto min-h-0">
      {#each events as ev}
        {@const people = ev.metadata?.people || []}
        <div class="rounded-lg overflow-hidden">
          <button class="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-[#1a1714] transition-colors"
                  on:click={() => expanded = expanded === ev.id ? null : ev.id}>
            <span class="text-xs text-[#9a9080] shrink-0 w-14">{timeAgo(ev.timestamp)}</span>
            <span class="text-sm flex-1 truncate">{ev.metadata?.notes || 'Meetup'}</span>
            <span class="text-[#9a9080] text-xs shrink-0 transition-transform"
                  style="transform: rotate({expanded === ev.id ? 90 : 0}deg)">›</span>
          </button>
          {#if expanded === ev.id}
            <div class="px-3 pb-2 flex flex-wrap gap-1.5 border-t border-[#1a1714]">
              {#each people as p}
                <span class="text-xs px-2 py-0.5 rounded-full bg-[#1a1714] text-[#9a9080]">
                  {p.name}
                </span>
              {/each}
              {#if people.length === 0}
                <span class="text-xs text-[#9a9080]">No people logged</span>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
