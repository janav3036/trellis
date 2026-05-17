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
    const d = new Date(ts);
    const now = new Date();
    const todayStr = now.toDateString();
    const tomorrowStr = new Date(now.getTime() + 86400000).toDateString();
    const time = d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    if (d.toDateString() === todayStr)     return `Today at ${time}`;
    if (d.toDateString() === tomorrowStr)  return `Tomorrow at ${time}`;
    return d.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short' }) + ` at ${time}`;
  }

  onMount(async () => {
    // Use local time (not UTC) so calendar timestamps stored in local TZ compare correctly
    const now = new Date();
    const localISO = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 19);
    const res = await fetch(`/api/events?source=calendar&event_type=event&date_from=${encodeURIComponent(localISO)}`);
    const events = await res.json();
    // API returns DESC order; last item = nearest future event
    nextEvent = events.length ? events[events.length - 1] : null;
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 h-full flex flex-col gap-2 overflow-hidden cursor-pointer"
     on:click={() => window.location.hash = '/life'}>
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider">Next Up</div>

  {#if nextEvent}
    {@const color = calColor(nextEvent.metadata?.calendar_name)}
    <div class="text-base font-semibold leading-tight">
      {nextEvent.metadata?.title || '—'}
    </div>
    <div class="text-xs text-[#9a9080]">{fmtWhen(nextEvent.timestamp)}</div>
    <div class="mt-auto pt-1">
      <span class="text-xs px-2 py-0.5 rounded-full font-medium"
            style="background:{color.bg}; color:{color.text}">
        {nextEvent.metadata?.calendar_name || 'Calendar'}
      </span>
    </div>
  {:else}
    <p class="text-sm text-[#9a9080]">Nothing upcoming</p>
  {/if}
</div>
