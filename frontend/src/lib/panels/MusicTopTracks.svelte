<script>
  import { onMount } from 'svelte';
  import { musicTheme } from '../musicTheme.js';

  let tracks = [];
  let range = 'monthly';
  const RANGES = [
    { key: 'weekly',  label: 'Week' },
    { key: 'monthly', label: 'Month' },
    { key: '6m',      label: '6 mo' },
    { key: 'alltime', label: 'All' },
  ];

  async function load(r) {
    range = r;
    const res = await fetch(`/api/spotify/top-tracks?range=${r}`);
    tracks = await res.json();
  }

  onMount(() => load('monthly'));
</script>

<div style="background:{$musicTheme.card}" class="rounded-xl p-4 h-full flex flex-col">
  <div class="flex items-center gap-2 mb-3">
    <div class="text-xs font-semibold uppercase tracking-wider flex-1" style="color:{$musicTheme.muted}">Top Tracks</div>
    {#each RANGES as r}
      <button
        on:click={() => load(r.key)}
        style="{range === r.key
          ? `background:${$musicTheme.accent};color:${$musicTheme.bg}`
          : `color:${$musicTheme.muted}`}"
        class="px-2 py-0.5 rounded text-xs"
      >{r.label}</button>
    {/each}
  </div>

  <div class="flex flex-col gap-1.5 overflow-y-auto flex-1">
    {#each tracks as t, i}
      {@const pct = Math.round((t.plays / tracks[0].plays) * 100)}
      <div class="relative flex items-center gap-3 px-3 py-2.5 rounded-lg overflow-hidden">
        <div class="absolute inset-0 rounded-lg" style="width:{pct}%; background:{$musicTheme.cardAlt}"></div>
        <span class="relative text-xs w-4 shrink-0 tabular-nums" style="color:{$musicTheme.muted}">{i + 1}</span>
        <div class="relative flex-1 min-w-0">
          <div class="text-sm truncate" style="color:{$musicTheme.text}">{t.track}</div>
          <div class="text-xs truncate" style="color:{$musicTheme.muted}">{t.artist}</div>
        </div>
        <span class="relative text-xs tabular-nums shrink-0" style="color:{$musicTheme.muted}">{t.plays}</span>
      </div>
    {:else}
      <p class="text-sm" style="color:{$musicTheme.muted}">No data yet.</p>
    {/each}
  </div>
</div>
