<script>
  import { onMount } from 'svelte';
  import { push } from 'svelte-spa-router';
  import { daysAgoIST, fmtDate } from '../ist.js';

  let commits = [];

  function timeAgo(ts) {
    const s = Math.floor((Date.now() - new Date(ts)) / 1000);
    if (s < 60)    return 'just now';
    if (s < 3600)  return `${Math.floor(s/60)}m`;
    if (s < 86400) return `${Math.floor(s/3600)}h`;
    const d = Math.floor(s/86400);
    if (d < 30)    return `${d}d`;
    return fmtDate(ts);
  }

  onMount(async () => {
    commits = await (await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(29)}`)).json();
  });
</script>

<div class="panel">
  <button class="panel-header" on:click={() => push('/code')}>
    <span class="eyebrow">Recent Commits</span>
    <span class="arrow">→</span>
  </button>

  {#if commits.length === 0}
    <p class="idle-text">No commits in the last 30 days.</p>
  {:else}
    <div class="list">
      {#each commits.slice(0, 10) as c}
        {@const repo = c.metadata.repo?.split('/')[1]}
        <div class="commit-row">
          <span class="repo-tag">{repo}</span>
          <span class="message">{c.metadata.message}</span>
          <span class="when">{timeAgo(c.timestamp)}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .panel {
    background: var(--surface);
    border-radius: 14px;
    padding: 14px 16px;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-sizing: border-box;
  }

  .panel-header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 10px;
    flex-shrink: 0;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    text-align: left;
  }
  .eyebrow {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--text-secondary);
    transition: color 0.15s ease;
  }
  .panel-header:hover .eyebrow { color: var(--text-primary); }
  .arrow {
    font-size: 0.7rem;
    color: var(--text-secondary);
    opacity: 0;
    transition: opacity 0.15s ease;
  }
  .panel-header:hover .arrow { opacity: 1; }

  .list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    overflow-y: auto;
    min-height: 0;
  }

  .commit-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border-radius: 8px;
    background: var(--bg);
    transition: background 0.15s ease;
  }
  .commit-row:hover { background: color-mix(in srgb, var(--bg) 70%, var(--accent) 30%); }

  .repo-tag {
    font-size: 0.68rem;
    font-weight: 600;
    font-family: ui-monospace, 'SF Mono', monospace;
    color: #6b9e6b;
    background: rgba(107, 158, 107, 0.12);
    padding: 1px 7px;
    border-radius: 4px;
    flex-shrink: 0;
    white-space: nowrap;
    letter-spacing: 0.01em;
  }
  .message {
    font-size: 0.8rem;
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: var(--text-primary);
  }
  .when {
    font-size: 0.68rem;
    color: var(--text-secondary);
    flex-shrink: 0;
    font-variant-numeric: tabular-nums;
  }

  .idle-text { font-size: 0.85rem; color: var(--text-secondary); }
</style>
