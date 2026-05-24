<script>
  import { onMount } from 'svelte';

  export let theme = 'home';

  $: c = theme === 'f1' ? {
    bg:    '#18181c',
    item:  '#0d0d0f',
    hover: '#1a1a22',
    text:  '#f0f0f2',
    muted: '#555',
    tag:   '#e8002d',
  } : {
    bg:    'var(--surface)',
    item:  'var(--bg)',
    hover: 'color-mix(in srgb, var(--bg) 70%, var(--surface) 30%)',
    text:  'var(--text-primary)',
    muted: 'var(--text-secondary)',
    tag:   'var(--accent)',
  };

  let items = [];

  onMount(async () => {
    const res = await fetch('/api/f1/news');
    const all = await res.json();
    items = all.slice(0, 15);
  });
</script>

<div class="panel" style="background:{c.bg}; color:{c.text}">
  <a href="/#/f1" class="eyebrow-link" style="color:{c.muted}"
     on:mouseenter={e => e.target.style.color = c.text}
     on:mouseleave={e => e.target.style.color = c.muted}>
    F1 News
  </a>

  {#if items.length === 0}
    <p class="idle-text" style="color:{c.muted}">Loading…</p>
  {:else}
    <div class="list">
      {#each items as item}
        <a href={item.link} target="_blank" rel="noopener noreferrer"
           class="news-row"
           style="background:{c.item}; color:{c.text}"
           on:mouseenter={e => e.currentTarget.style.background = c.hover}
           on:mouseleave={e => e.currentTarget.style.background = c.item}>
          <span class="title">{item.title}</span>
          <div class="meta">
            {#if item.source}
              <span class="source" style="color:{c.tag}">{item.source}</span>
            {/if}
            {#if item.published}
              <span class="pub-date" style="color:{c.muted}">{item.published}</span>
            {/if}
          </div>
        </a>
      {/each}
    </div>
  {/if}
</div>

<style>
  .panel {
    border-radius: 14px;
    padding: 14px 14px 10px;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-sizing: border-box;
  }

  .eyebrow-link {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    text-decoration: none;
    margin-bottom: 8px;
    flex-shrink: 0;
    display: block;
    transition: color 0.15s ease;
  }

  .list {
    display: flex;
    flex-direction: column;
    gap: 3px;
    overflow-y: auto;
    flex: 1;
  }

  .news-row {
    display: block;
    padding: 7px 10px;
    border-radius: 8px;
    text-decoration: none;
    transition: background 0.15s ease;
  }

  .title {
    display: block;
    font-size: 0.78rem;
    line-height: 1.35;
  }

  .meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 3px;
  }
  .source {
    font-size: 0.62rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .pub-date {
    font-size: 0.62rem;
    font-variant-numeric: tabular-nums;
  }

  .idle-text { font-size: 0.85rem; }
</style>
