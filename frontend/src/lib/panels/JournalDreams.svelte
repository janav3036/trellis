<script>
  import { onMount } from 'svelte';
  let dreams = [], expandedDream = null;

  const MOOD_COLORS = {
    neutral:   { bg: '#2a2a2a', text: '#9a9080' },
    peaceful:  { bg: '#1a2a3d', text: '#6b9ecc' },
    vivid:     { bg: '#2a1a3d', text: '#9b7ec8' },
    eerie:     { bg: '#1a2e2e', text: '#5abfbf' },
    anxious:   { bg: '#2e1a1a', text: '#c87a7a' },
    nostalgic: { bg: '#3d2e1a', text: '#c89a5a' },
    joyful:    { bg: '#2a3d2a', text: '#8abf8a' },
  };
  function mc(mood) { return MOOD_COLORS[mood] || MOOD_COLORS.neutral; }
  function timeAgo(ts) {
    const s = Math.floor((Date.now()-new Date(ts))/1000);
    if (s<3600) return `${Math.floor(s/60)}m ago`;
    if (s<86400) return `${Math.floor(s/3600)}h ago`;
    const d=Math.floor(s/86400); if(d<30) return `${d}d ago`;
    return new Date(ts).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
  }
  async function load() {
    dreams = await (await fetch('/api/dreams')).json();
  }
  onMount(load);
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Dream Journal</div>
  {#if dreams.length === 0}
    <p class="text-sm text-[#9a9080]">No dreams logged yet.</p>
  {:else}
    <div class="flex flex-col gap-2 max-h-80 overflow-y-auto">
      {#each dreams as d}
        {@const c = mc(d.mood)}
        <button class="bg-[#1a1714] hover:bg-[#2a2520] rounded-xl px-4 py-3 text-left transition-colors"
          on:click={() => expandedDream=d}>
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap mb-1">
                <span class="text-sm font-medium">{d.title}</span>
                {#if d.lucid}<span class="text-xs px-1.5 py-0.5 rounded-full bg-[#2a1a3d] text-[#9b7ec8]">lucid</span>{/if}
                {#if d.mood}<span class="text-xs px-1.5 py-0.5 rounded-full capitalize" style="background:{c.bg};color:{c.text}">{d.mood}</span>{/if}
              </div>
              {#if d.description}<p class="text-xs text-[#9a9080] truncate">{d.description}</p>{/if}
            </div>
            <span class="text-xs text-[#9a9080] shrink-0">{timeAgo(d.timestamp)}</span>
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>

{#if expandedDream}
  {@const c = mc(expandedDream.mood)}
  <div class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-8"
    on:click={() => expandedDream=null}>
    <div class="bg-[#242019] rounded-2xl p-8 max-w-xl w-full shadow-2xl" on:click|stopPropagation>
      <div class="flex items-start justify-between gap-4 mb-4">
        <div>
          <div class="text-xl font-semibold mb-1">{expandedDream.title}</div>
          <div class="text-xs text-[#9a9080]">
            {new Date(expandedDream.timestamp).toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'})}
          </div>
        </div>
        <button on:click={() => expandedDream=null} class="text-[#9a9080] hover:text-[#e8e0d0]">✕</button>
      </div>
      <div class="flex flex-wrap gap-2 mb-4">
        {#if expandedDream.lucid}<span class="text-xs px-2 py-0.5 rounded-full bg-[#2a1a3d] text-[#9b7ec8]">lucid</span>{/if}
        {#if expandedDream.mood}<span class="text-xs px-2 py-0.5 rounded-full capitalize" style="background:{c.bg};color:{c.text}">{expandedDream.mood}</span>{/if}
        {#each expandedDream.tags||[] as tag}<span class="text-xs px-2 py-0.5 rounded-full bg-[#1a1714] text-[#5a5040]">#{tag}</span>{/each}
      </div>
      {#if expandedDream.description}
        <p class="text-sm text-[#c8c0b0] leading-relaxed whitespace-pre-wrap mb-6">{expandedDream.description}</p>
      {/if}
      <button on:click={async()=>{await fetch(`/api/events/${expandedDream.id}`,{method:'DELETE'});expandedDream=null;load();}}
        class="text-xs text-[#c87a7a] hover:text-[#e87a7a]">Delete</button>
    </div>
  </div>
{/if}
