<script>
  import { onMount } from 'svelte';
  let repos = [];

  onMount(async () => {
    repos = await (await fetch('/api/github/repos')).json();
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Repositories</div>
  {#if repos.length === 0}
    <p class="text-sm text-[#9a9080]">No repos yet.</p>
  {:else}
    <div class="grid grid-cols-[repeat(auto-fill,minmax(180px,1fr))] gap-3">
      {#each repos as r}
        <div class="bg-[#1a1714] rounded-xl px-4 py-3">
          <div class="text-sm font-medium truncate">{r.repo.split('/')[1]}</div>
          <div class="text-xs text-[#9a9080] mt-0.5">{r.repo.split('/')[0]}</div>
          <div class="text-xs text-[#6b9e6b] mt-2">{r.commits} commits</div>
        </div>
      {/each}
    </div>
  {/if}
</div>
