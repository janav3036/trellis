<script>
  import { onMount } from 'svelte';
  let playlists = [];

  onMount(async () => {
    const r = await fetch('/api/playlists');
    playlists = (await r.json()).sort((a, b) => a.name.localeCompare(b.name));
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Playlists</div>
  {#if playlists.length === 0}
    <p class="text-sm text-[#9a9080]">Loading…</p>
  {:else}
    <div class="grid grid-cols-[repeat(auto-fill,minmax(140px,1fr))] gap-3">
      {#each playlists as p}
        <div class="bg-[#1a1714] rounded-xl overflow-hidden">
          {#if p.cover}
            <img src={p.cover} alt={p.name} class="w-full aspect-square object-cover" />
          {/if}
          <div class="p-2">
            <div class="text-xs font-medium truncate">{p.name}</div>
            <div class="text-[10px] text-[#9a9080] mt-0.5">{p.track_count} tracks</div>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>
