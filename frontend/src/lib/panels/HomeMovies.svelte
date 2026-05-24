<script>
  import { onMount } from 'svelte';
  let watchlist = [], searching = false, query = '', results = [], status = '';
  let scrollEl, selectedMovie = null;
  const CARD_WIDTH = 88;

  async function load() {
    const res = await fetch('/api/events?source=movies&event_type=watchlist');
    watchlist = await res.json();
  }

  async function markWatched(id) {
    await fetch(`/api/events/${id}`, { method: 'DELETE' });
    watchlist = watchlist.filter(m => m.id !== id);
    selectedMovie = null;
  }

  async function search() {
    if (!query.trim()) return;
    const res = await fetch(`/api/movies/search?q=${encodeURIComponent(query)}`);
    results = await res.json();
  }

  async function addToWatchlist(movie) {
    status = 'Adding…';
    await fetch('/api/movies/watchlist', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tmdb_id: movie.tmdb_id,
        title: movie.title,
        year: movie.year,
        poster_path: movie.poster_path,
      }),
    });
    status = ''; query = ''; results = []; searching = false;
    load();
  }

  function scroll(dir) {
    scrollEl?.scrollBy({ left: dir * CARD_WIDTH * 2, behavior: 'smooth' });
  }

  onMount(load);
</script>

<div class="th-surface h-full flex flex-col overflow-hidden" style="border-radius:14px;padding:12px 14px">

  <!-- Header -->
  <div class="flex items-center gap-2 mb-2 shrink-0">
    <a href="/#/life"
       class="uppercase tracking-wider flex-1 hover:th-text transition-colors"
       style="font-size:9px;font-weight:600;letter-spacing:0.13em;color:var(--text-secondary)">
      Watchlist
    </a>
    {#if status}<span class="text-xs th-muted">{status}</span>{/if}
    <button on:click={() => { searching = !searching; query = ''; results = []; }}
            class="text-xs text-[#6b9e6b] hover:text-[#8abf8a] transition-colors">
      {searching ? 'Cancel' : '+ Add'}
    </button>
  </div>

  <!-- Search -->
  {#if searching}
    <div class="shrink-0 mb-2 flex flex-col gap-1.5">
      <div class="flex gap-1.5">
        <input type="text" bind:value={query}
               on:keydown={e => e.key === 'Enter' && search()}
               placeholder="Search movies…"
               class="flex-1 th-bg th-text rounded-lg px-2 py-1 text-xs border th-border" />
        <button on:click={search}
                class="th-bg th-hover-up th-text px-2 py-1 rounded-lg text-xs">Go</button>
      </div>
      {#if results.length > 0}
        <div class="flex flex-col gap-0.5 max-h-28 overflow-y-auto">
          {#each results as r}
            <button on:click={() => addToWatchlist(r)}
                    class="flex items-center gap-2 px-2 py-1 rounded-lg th-hover text-left">
              {#if r.poster_path}
                <img src="/api/img?url=https://image.tmdb.org/t/p/w92{r.poster_path}"
                     alt={r.title} class="w-5 h-7 object-cover rounded shrink-0" />
              {:else}
                <div class="w-5 h-7 th-bg rounded shrink-0" />
              {/if}
              <span class="text-xs truncate">{r.title}</span>
              <span class="text-xs th-muted shrink-0">{r.year}</span>
            </button>
          {/each}
        </div>
      {/if}
    </div>
  {/if}

  <!-- Movie strip -->
  <div class="flex-1 flex flex-col justify-center min-h-0">
    {#if watchlist.length === 0 && !searching}
      <p class="text-xs th-muted px-1">No movies in watchlist.</p>
    {:else if !searching}
      <div class="relative">
        {#if watchlist.length > 4}
          <button on:click={() => scroll(-1)}
                  class="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1 z-10
                         w-5 h-5 flex items-center justify-center rounded-full
                         th-bg th-muted hover:th-text text-xs shrink-0">‹</button>
          <button on:click={() => scroll(1)}
                  class="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1 z-10
                         w-5 h-5 flex items-center justify-center rounded-full
                         th-bg th-muted hover:th-text text-xs shrink-0">›</button>
        {/if}
        <div bind:this={scrollEl}
             class="flex gap-2 overflow-x-auto scroll-smooth"
             style="scrollbar-width:none">
          {#each watchlist as m}
            {@const meta = m.metadata}
            <button class="flex-shrink-0 flex flex-col items-center gap-1 text-left"
                    style="width:76px"
                    on:click={() => selectedMovie = m}>
              {#if meta.poster_path}
                <img src="/api/img?url=https://image.tmdb.org/t/p/w92{meta.poster_path}"
                     alt={meta.title}
                     class="w-full rounded-md object-cover hover:opacity-80 transition-opacity"
                     style="height:104px" />
              {:else}
                <div class="w-full th-bg rounded-md flex items-center justify-center th-hover-up"
                     style="height:104px">
                  <span class="th-muted text-xs text-center px-1 leading-tight">{meta.title}</span>
                </div>
              {/if}
              <span class="text-[10px] th-muted text-center w-full truncate leading-tight">
                {meta.title}
              </span>
            </button>
          {/each}
        </div>
      </div>
    {/if}
  </div>
</div>

<!-- Movie detail modal -->
{#if selectedMovie}
  {@const meta = selectedMovie.metadata}
  <div class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8"
       on:click={() => selectedMovie = null}>
    <div class="th-surface rounded-2xl overflow-hidden max-w-xs w-full shadow-2xl"
         on:click|stopPropagation>
      {#if meta.poster_path}
        <img src="/api/img?url=https://image.tmdb.org/t/p/w342{meta.poster_path}"
             alt={meta.title} class="w-full object-cover" style="max-height:360px" />
      {/if}
      <div class="px-5 py-4 flex items-start justify-between gap-4">
        <div>
          <div class="text-sm font-semibold leading-snug">{meta.title}</div>
          {#if meta.year}<div class="text-xs th-muted mt-0.5">{meta.year}</div>{/if}
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <button on:click={() => markWatched(selectedMovie.id)}
            class="text-xs bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-3 py-1.5 rounded-lg">
            Watched
          </button>
          <button on:click={() => selectedMovie = null}
            class="th-muted hover:th-text">✕</button>
        </div>
      </div>
    </div>
  </div>
{/if}
