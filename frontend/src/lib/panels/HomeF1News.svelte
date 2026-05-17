<script>
  import { onMount } from 'svelte';
  let items = [];

  onMount(async () => {
    const res = await fetch('/api/f1/news');
    const all = await res.json();
    items = all.slice(0, 15);
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 h-full flex flex-col overflow-hidden">
  <a href="/#/f1"
     class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-2 hover:text-[#e8e0d0] transition-colors">
    F1 News
  </a>

  {#if items.length === 0}
    <p class="text-sm text-[#9a9080] animate-pulse">Loading…</p>
  {:else}
    <div class="flex flex-col gap-1.5 overflow-y-auto flex-1" style="scrollbar-width:none">
      {#each items as item}
        <a href={item.link} target="_blank" rel="noopener noreferrer"
           class="block px-3 py-2 rounded-lg text-sm leading-snug transition-colors
                  hover:bg-[#2e2a24]"
           style="background:#1a1714; color: var(--text-primary)">
          {item.title}
        </a>
      {/each}
    </div>
  {/if}
</div>
