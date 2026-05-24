<script>
  import { onMount } from 'svelte';
  import { musicTheme } from '../musicTheme.js';

  let playlists = [];

  onMount(async () => {
    const r = await fetch('/api/playlists');
    playlists = (await r.json()).sort((a, b) => a.name.localeCompare(b.name));
  });
</script>

<div style="background:{$musicTheme.card}" class="rounded-xl p-4 w-full h-full flex flex-col">
  <div class="text-xs font-semibold uppercase tracking-wider mb-3 shrink-0" style="color:{$musicTheme.muted}">Playlists</div>
  {#if playlists.length === 0}
    <p class="text-sm" style="color:{$musicTheme.muted}">Loading…</p>
  {:else}
    <div class="flex-1 overflow-y-auto" style="scrollbar-width:none">
      <div class="grid grid-cols-[repeat(auto-fill,minmax(130px,1fr))] gap-3">
        {#each playlists as p}
          <div style="background:{$musicTheme.bg}" class="rounded-xl overflow-hidden">
            {#if p.cover}
              <img src={p.cover} alt={p.name} class="w-full aspect-square object-cover" />
            {/if}
            <div class="p-2">
              <div class="text-xs font-medium truncate" style="color:{$musicTheme.text}">{p.name}</div>
              <div class="text-[10px] mt-0.5" style="color:{$musicTheme.muted}">{p.track_count} tracks</div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>
