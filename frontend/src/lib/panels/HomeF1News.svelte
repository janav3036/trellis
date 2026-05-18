<script>
  import { onMount } from 'svelte';

  export let theme = 'home';

  $: c = theme === 'f1' ? {
    bg:    '#18181c',
    item:  '#0d0d0f',
    hover: '#1a1a22',
    text:  '#f0f0f2',
    muted: '#666',
  } : {
    bg:    '#242019',
    item:  '#1a1714',
    hover: '#2e2a24',
    text:  'var(--text-primary)',
    muted: '#9a9080',
  };

  let items = [];

  onMount(async () => {
    const res = await fetch('/api/f1/news');
    const all = await res.json();
    items = all.slice(0, 15);
  });
</script>

<div class="rounded-xl p-4 h-full flex flex-col overflow-hidden"
     style="background:{c.bg}; color:{c.text}">

  <a href="/#/f1"
     class="text-xs font-semibold uppercase tracking-wider mb-2 transition-colors block shrink-0"
     style="color:{c.muted}"
     on:mouseenter={e => e.target.style.color = c.text}
     on:mouseleave={e => e.target.style.color = c.muted}>
    F1 News
  </a>

  {#if items.length === 0}
    <p class="text-sm animate-pulse" style="color:{c.muted}">Loading…</p>
  {:else}
    <div class="flex flex-col gap-1.5 overflow-y-auto flex-1" style="scrollbar-width:none">
      {#each items as item}
        <a href={item.link} target="_blank" rel="noopener noreferrer"
           class="block px-3 py-2 rounded-lg text-sm leading-snug transition-colors"
           style="background:{c.item}; color:{c.text}"
           on:mouseenter={e => e.currentTarget.style.background = c.hover}
           on:mouseleave={e => e.currentTarget.style.background = c.item}>
          {item.title}
        </a>
      {/each}
    </div>
  {/if}
</div>
