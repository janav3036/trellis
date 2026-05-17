<script>
  import { onMount, onDestroy } from 'svelte';
  let np = null;
  let timer;

  async function poll() {
    const r = await fetch('/api/now-playing');
    np = await r.json();
  }

  onMount(() => { poll(); timer = setInterval(poll, 10000); });
  onDestroy(() => clearInterval(timer));
</script>

<div class="bg-[#242019] rounded-xl p-3 h-full overflow-hidden flex flex-col justify-center cursor-pointer"
     on:click={() => window.location.hash = '/music'}>
  {#if np}
    <div class="flex items-center gap-3">
      {#if np.cover}
        <img src={np.cover} alt="album" class="w-14 h-14 rounded-md shrink-0 object-cover" />
      {/if}
      <div class="min-w-0 flex-1">
        <div class="text-[10px] font-semibold text-[#9a9080] uppercase tracking-wider mb-0.5">Now Playing</div>
        <div class="text-sm font-semibold truncate">{np.track}</div>
        <div class="text-xs text-[#9a9080] truncate">{np.artist}</div>
      </div>
    </div>
  {:else}
    <div>
      <div class="text-[10px] font-semibold text-[#9a9080] uppercase tracking-wider mb-1">Now Playing</div>
      <p class="text-sm text-[#9a9080]">Not playing</p>
    </div>
  {/if}
</div>
