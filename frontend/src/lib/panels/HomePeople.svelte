<script>
  import { onMount } from 'svelte';
  import { istDate, fmtDate } from '../ist.js';
  let events = [], expanded = null;

  function groupEvents(evs) {
    const map = new Map();
    for (const e of evs) {
      const key = `${istDate(e.timestamp)}::${(e.metadata.notes||'').trim()}`;
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
    if (s < 3600)  return `${Math.floor(s / 60)}m ago`;
    if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
    const d = Math.floor(s / 86400);
    if (d < 30)    return `${d}d ago`;
    return fmtDate(ts);
  }

  onMount(async () => {
    const res = await fetch('/api/events?source=people&event_type=meetup');
    const all = await res.json();
    events = groupEvents(all).slice(0, 3);
  });
</script>

<div class="panel">
  <a href="/#/life" class="eyebrow-link">People</a>

  {#if events.length === 0}
    <p class="idle-text">No meetups logged yet.</p>
  {:else}
    <div class="list">
      {#each events as ev}
        {@const people = ev.metadata?.people || []}
        <div class="event-wrap">
          <button class="event-row"
                  on:click={() => expanded = expanded === ev.id ? null : ev.id}>
            <span class="when">{timeAgo(ev.timestamp)}</span>
            <span class="note">{ev.metadata?.notes || 'Meetup'}</span>
            <span class="chevron" class:open={expanded === ev.id}>›</span>
          </button>
          {#if expanded === ev.id}
            <div class="chips">
              {#each people as p}
                <span class="chip">{p.name}</span>
              {/each}
              {#if people.length === 0}
                <span class="chip muted">No names logged</span>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .panel {
    background: var(--surface);
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
    color: var(--text-secondary);
    text-decoration: none;
    margin-bottom: 8px;
    flex-shrink: 0;
    transition: color 0.15s ease;
  }
  .eyebrow-link:hover { color: var(--text-primary); }

  .list {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex: 1;
    overflow-y: auto;
    min-height: 0;
  }

  .event-wrap { border-radius: 8px; overflow: hidden; }

  .event-row {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    background: var(--bg);
    border: none;
    cursor: pointer;
    text-align: left;
    transition: background 0.15s ease;
  }
  .event-row:hover { background: color-mix(in srgb, var(--bg) 70%, var(--surface) 30%); }

  .when {
    font-size: 0.68rem;
    color: var(--text-secondary);
    flex-shrink: 0;
    width: 48px;
    font-variant-numeric: tabular-nums;
  }
  .note {
    font-size: 0.8rem;
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--text-primary);
  }
  .chevron {
    font-size: 0.75rem;
    color: var(--text-secondary);
    flex-shrink: 0;
    transition: transform 0.2s ease;
  }
  .chevron.open { transform: rotate(90deg); }

  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    padding: 6px 10px 8px;
    background: var(--bg);
    border-top: 1px solid var(--surface);
  }
  .chip {
    font-size: 0.65rem;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 20px;
    background: var(--surface);
    color: var(--text-secondary);
    letter-spacing: 0.02em;
  }
  .chip.muted { opacity: 0.6; }

  .idle-text { font-size: 0.85rem; color: var(--text-secondary); }
</style>
