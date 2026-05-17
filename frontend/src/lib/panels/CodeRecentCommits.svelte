<script>
  import { onMount } from 'svelte';
  let commits = [];

  function daysAgo(n) {
    const d = new Date(); d.setDate(d.getDate() - n); return d.toISOString().split('T')[0];
  }
  function timeAgo(ts) {
    const s = Math.floor((Date.now() - new Date(ts)) / 1000);
    if (s < 60) return 'just now';
    if (s < 3600) return `${Math.floor(s/60)}m ago`;
    if (s < 86400) return `${Math.floor(s/3600)}h ago`;
    const d = Math.floor(s/86400);
    if (d < 30) return `${d}d ago`;
    return new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  onMount(async () => {
    commits = await (await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgo(29)}`)).json();
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 h-full flex flex-col overflow-hidden">
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3 shrink-0">Recent Commits</div>
  {#if commits.length === 0}
    <p class="text-sm text-[#9a9080]">No commits in the last 30 days.</p>
  {:else}
    <div class="flex flex-col gap-2 flex-1 overflow-y-auto min-h-0" style="scrollbar-width:none">
      {#each commits.slice(0, 10) as c}
        <div class="flex items-start gap-3 px-3 py-2 rounded-lg bg-[#1a1714]">
          <span class="text-xs bg-[#242019] text-[#6b9e6b] px-2 py-0.5 rounded font-mono shrink-0">{c.metadata.repo?.split('/')[1]}</span>
          <span class="text-sm text-[#e8e0d0] truncate flex-1">{c.metadata.message}</span>
          <span class="text-xs text-[#9a9080] shrink-0">{timeAgo(c.timestamp)}</span>
        </div>
      {/each}
    </div>
  {/if}
</div>
