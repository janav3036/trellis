<script>
  import { onMount } from 'svelte';
  let news = [];

  onMount(async () => {
    news = await (await fetch('/api/f1/news')).json();
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Latest News</div>
  {#if news.length === 0}
    <p class="text-sm text-[#9a9080] animate-pulse">Loading…</p>
  {:else}
    <div class="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3">
      {#each news as item}
        <a href={item.link} target="_blank" rel="noopener noreferrer"
          class="bg-[#1a1714] rounded-xl p-3 hover:bg-[#2a2520] transition-colors block">
          <div class="text-xs font-medium leading-snug mb-2">{item.title}</div>
          <div class="flex items-center gap-2 text-[10px] text-[#9a9080]">
            <span>{item.source}</span>
            {#if item.published}<span>·</span><span>{item.published}</span>{/if}
          </div>
        </a>
      {/each}
    </div>
  {/if}
</div>
