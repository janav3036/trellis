<script>
  import { onMount } from 'svelte';
  let quotes = [], selectedTag = '';

  $: allTags = [...new Set(quotes.flatMap(q => q.tags||[]))];
  $: filtered = selectedTag ? quotes.filter(q => q.tags?.includes(selectedTag)) : quotes;

  onMount(async () => {
    quotes = await (await fetch('/api/quotes')).json();
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Quotes</div>

  {#if allTags.length>0}
    <div class="flex flex-wrap gap-1.5 mb-3">
      <button on:click={() => selectedTag=''}
        class="px-2 py-0.5 rounded-full text-xs {selectedTag===''?'bg-[#3a3530] text-[#e8e0d0]':'text-[#9a9080] hover:text-[#e8e0d0]'}">All</button>
      {#each allTags as tag}
        <button on:click={() => selectedTag=selectedTag===tag?'':tag}
          class="px-2 py-0.5 rounded-full text-xs {selectedTag===tag?'bg-[#3a3530] text-[#e8e0d0]':'text-[#9a9080] hover:text-[#e8e0d0]'}">#{tag}</button>
      {/each}
    </div>
  {/if}

  {#if filtered.length===0}
    <p class="text-sm text-[#9a9080]">No quotes yet.</p>
  {:else}
    <div class="flex flex-col gap-3 max-h-80 overflow-y-auto">
      {#each filtered as q}
        <div class="bg-[#1a1714] rounded-xl px-4 py-3 group relative">
          <p class="text-sm text-[#c8c0b0] leading-relaxed italic mb-2">"{q.text}"</p>
          <div class="flex items-center justify-between gap-3">
            <div class="text-xs text-[#9a9080]">
              {#if q.author}— {q.author}{/if}{#if q.source_title}, <span class="italic">{q.source_title}</span>{/if}
            </div>
            <div class="flex items-center gap-2">
              {#each q.tags||[] as tag}<span class="text-xs text-[#5a5040]">#{tag}</span>{/each}
              <button on:click={async()=>{await fetch(`/api/events/${q.id}`,{method:'DELETE'});quotes=await(await fetch('/api/quotes')).json();}}
                class="text-xs text-[#c87a7a] hover:text-[#e87a7a] opacity-0 group-hover:opacity-100 transition-opacity">✕</button>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
