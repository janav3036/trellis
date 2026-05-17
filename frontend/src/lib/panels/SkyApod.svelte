<script>
  import { onMount } from 'svelte';
  let apod = null;

  onMount(async () => {
    const r = await fetch('/api/sky/apod');
    if (r.ok) apod = await r.json();
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 h-full flex gap-4 items-start overflow-hidden cursor-pointer"
     on:click={() => window.location.hash = '/sky'}>
  {#if apod}
    {#if apod.media_type === 'image'}
      <div class="shrink-0 w-48 self-stretch rounded-lg overflow-hidden">
        <img src={apod.url} alt={apod.title} class="w-full h-full object-cover" />
      </div>
      <div class="flex-1 flex flex-col gap-2 min-w-0">
        <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider">
          APOD · {apod.date}
        </div>
        <div class="text-sm font-semibold leading-snug">{apod.title}</div>
        <div class="text-xs text-[#9a9080] leading-relaxed line-clamp-6">
          {apod.explanation}
        </div>
      </div>
    {:else}
      <div class="flex flex-col gap-2">
        <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider">APOD · {apod.date}</div>
        <div class="text-sm font-medium">{apod.title}</div>
        <a href={apod.url} target="_blank" rel="noopener noreferrer"
           class="text-xs text-[#6b9e6b] hover:text-[#8abf8a]">Watch video →</a>
      </div>
    {/if}
  {:else}
    <div class="flex-1 flex items-center justify-center text-[#9a9080] text-sm animate-pulse">Loading…</div>
  {/if}
</div>

