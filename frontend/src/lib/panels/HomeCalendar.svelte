<script>
  import { onMount } from 'svelte';

  let nextEvent = null;

  const CAL_COLORS = {
    'Projects':           { bg: '#2a3d2a', text: '#8abf8a' },
    'Gym / Sports':       { bg: '#3d2e1a', text: '#c89a5a' },
    'College':            { bg: '#1a2a3d', text: '#6b9ecc' },
    'Slots':              { bg: '#2e1a1a', text: '#c87a7a' },
    'Side projects':      { bg: '#2a1a3d', text: '#9b7ec8' },
    'Courses & Studies':  { bg: '#2e2a1a', text: '#c8a84b' },
    'Test & ICAs':        { bg: '#1a2e2e', text: '#5abfbf' },
  };
  const DEFAULT_COLOR = { bg: '#2a2a2a', text: '#9a9080' };
  function calColor(name) { return CAL_COLORS[name] || DEFAULT_COLOR; }

  function fmtWhen(ts) {
    const d   = new Date(ts);
    const now = new Date();
    const todayStr    = now.toDateString();
    const tomorrowStr = new Date(now.getTime() + 86400000).toDateString();
    const time = d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    if (d.toDateString() === todayStr)    return `Today · ${time}`;
    if (d.toDateString() === tomorrowStr) return `Tomorrow · ${time}`;
    return d.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short' }) + ` · ${time}`;
  }

  onMount(async () => {
    const now      = new Date();
    const localISO = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 19);
    const res      = await fetch(`/api/events?source=calendar&event_type=event&date_from=${encodeURIComponent(localISO)}`);
    const events   = await res.json();
    nextEvent = events.length ? events[events.length - 1] : null;
  });
</script>

<div class="panel" on:click={() => window.location.hash = '/life'}>
  <span class="eyebrow">Next Up</span>

  {#if nextEvent}
    {@const color = calColor(nextEvent.metadata?.calendar_name)}
    <div class="event-title">{nextEvent.metadata?.title || '—'}</div>
    <div class="event-when">{fmtWhen(nextEvent.timestamp)}</div>
    <div class="badge-row">
      <span class="badge" style="background:{color.bg}; color:{color.text}">
        {nextEvent.metadata?.calendar_name || 'Calendar'}
      </span>
    </div>
  {:else}
    <p class="idle-text">Nothing upcoming</p>
  {/if}
</div>

<style>
  .panel {
    background: var(--surface);
    border-radius: 14px;
    padding: 12px 14px;
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 5px;
    overflow: hidden;
    cursor: pointer;
    transition: filter 0.2s ease;
    box-sizing: border-box;
  }
  .panel:hover { filter: brightness(1.06); }

  .eyebrow {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--text-secondary);
    flex-shrink: 0;
  }
  .event-title {
    font-size: 0.9rem;
    font-weight: 600;
    line-height: 1.25;
    flex: 1;
    display: flex;
    align-items: center;
  }
  .event-when {
    font-size: 0.72rem;
    color: var(--text-secondary);
    flex-shrink: 0;
  }
  .badge-row { margin-top: auto; flex-shrink: 0; }
  .badge {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 2px 8px;
    border-radius: 20px;
    line-height: 1.6;
  }
  .idle-text { font-size: 0.85rem; color: var(--text-secondary); }
</style>
