<script>
  import { onMount } from 'svelte';

  let movies = [], expandedMovie = null, selectedGenres = new Set();
  let showForm = false;
  let movieDate = new Date().toISOString().slice(0,10);
  let movieQuery = '', movieResults = [], selectedMovie = null;
  let movieRating = null, movieNotes = '', movieStatus = '';
  let searchTimeout;

  const TMDB_GENRES = {
    28:'Action',12:'Adventure',16:'Animation',35:'Comedy',80:'Crime',99:'Documentary',
    18:'Drama',10751:'Family',14:'Fantasy',36:'History',27:'Horror',10402:'Music',
    9648:'Mystery',10749:'Romance',878:'Sci-Fi',53:'Thriller',10752:'War',37:'Western',
  };

  $: availableGenres = [...new Set(movies.flatMap(m=>m.metadata.genres||[]))].filter(id=>TMDB_GENRES[id]);
  $: filteredMovies = selectedGenres.size===0 ? movies : movies.filter(m=>(m.metadata.genres||[]).some(id=>selectedGenres.has(id)));

  async function load() {
    movies = await (await fetch('/api/events?source=movies&event_type=watch')).json();
  }
  async function logMovie() {
    if (!selectedMovie) { movieStatus='Pick a movie from results'; return; }
    movieStatus='saving…';
    await fetch('/api/movies/log', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        date:movieDate, title:selectedMovie.title, tmdb_id:selectedMovie.tmdb_id,
        year:selectedMovie.year, poster_path:selectedMovie.poster_path,
        genres:selectedMovie.genre_ids, rating:movieRating, notes:movieNotes,
        overview:selectedMovie.overview,
      }),
    });
    movieStatus='Saved!'; movieQuery=''; selectedMovie=null; movieRating=null; movieNotes=''; showForm=false;
    load();
  }

  onMount(load);
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="flex items-center gap-3 mb-3">
    <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider flex-1">Movie Diary</div>
    <button on:click={() => showForm=!showForm}
      class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-3 py-1 rounded-lg text-xs">
      {showForm ? 'Cancel' : '+ Log'}
    </button>
    {#if movieStatus}<span class="text-xs text-[#9a9080]">{movieStatus}</span>{/if}
  </div>

  {#if showForm}
    <div class="bg-[#1a1714] rounded-xl p-4 mb-4 flex flex-col gap-3">
      <div class="flex gap-3 items-start">
        <div class="flex flex-col gap-1">
          <label class="text-xs text-[#9a9080]">Date</label>
          <input type="date" bind:value={movieDate}
            class="bg-[#242019] text-[#e8e0d0] rounded-lg px-2 py-1.5 text-sm border border-[#3a3530]" />
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs text-[#9a9080]">Rating</label>
          <div class="flex gap-1 mt-1">
            {#each [1,2,3,4,5] as n}
              <button on:click={() => movieRating=movieRating===n?null:n}
                class="text-base {movieRating>=n?'text-[#c8a84b]':'text-[#3a3530]'}">★</button>
            {/each}
          </div>
        </div>
      </div>
      <div class="relative flex flex-col gap-1">
        <label class="text-xs text-[#9a9080]">Search movie</label>
        <input type="text" bind:value={movieQuery}
          on:input={() => {
            clearTimeout(searchTimeout); selectedMovie=null;
            if (movieQuery.length<2){movieResults=[];return;}
            searchTimeout=setTimeout(async()=>{
              const r=await fetch(`/api/movies/search?q=${encodeURIComponent(movieQuery)}`);
              movieResults=await r.json();
            },300);
          }}
          placeholder="Start typing…"
          class="bg-[#242019] text-[#e8e0d0] rounded-lg px-2 py-1.5 text-sm border border-[#3a3530]" />
        {#if movieResults.length>0 && !selectedMovie}
          <div class="absolute top-full left-0 right-0 mt-1 bg-[#2a2520] rounded-lg border border-[#3a3530] z-10 overflow-hidden">
            {#each movieResults as r}
              <button class="w-full flex items-center gap-2 px-3 py-2 hover:bg-[#342f28] text-left"
                on:click={() => {selectedMovie=r;movieQuery=r.title;movieResults=[];}}>
                {#if r.poster_path}
                  <img src="/api/img?url={encodeURIComponent('https://image.tmdb.org/t/p/w92'+r.poster_path)}"
                    alt={r.title} class="w-6 h-9 object-cover rounded shrink-0" />
                {:else}<div class="w-6 h-9 bg-[#1a1714] rounded shrink-0"/>{/if}
                <div>
                  <div class="text-sm text-[#e8e0d0]">{r.title}</div>
                  <div class="text-xs text-[#9a9080]">{r.year}</div>
                </div>
              </button>
            {/each}
          </div>
        {/if}
      </div>
      <input type="text" bind:value={movieNotes} placeholder="Notes (optional)"
        class="bg-[#242019] text-[#e8e0d0] rounded-lg px-2 py-1.5 text-sm border border-[#3a3530]" />
      <button on:click={logMovie}
        class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-1.5 rounded-lg text-sm self-start">Save</button>
    </div>
  {/if}

  {#if availableGenres.length>0}
    <div class="flex flex-wrap gap-1.5 mb-3">
      {#each availableGenres as id}
        <button on:click={() => {if(selectedGenres.has(id))selectedGenres.delete(id);else selectedGenres.add(id);selectedGenres=selectedGenres;}}
          class="px-2 py-0.5 rounded-full text-xs {selectedGenres.has(id)?'bg-[#3d2e1a] text-[#c89a5a]':'bg-[#1a1714] text-[#9a9080] hover:text-[#e8e0d0]'}">
          {TMDB_GENRES[id]}
        </button>
      {/each}
    </div>
  {/if}

  {#if filteredMovies.length===0}
    <p class="text-sm text-[#9a9080]">No movies logged yet.</p>
  {:else}
    <div class="grid grid-cols-[repeat(auto-fill,minmax(110px,1fr))] gap-3">
      {#each filteredMovies as m}
        <button class="flex flex-col gap-1 text-left" on:click={() => expandedMovie=m}>
          {#if m.metadata.poster_path}
            <img src="/api/img?url={encodeURIComponent('https://image.tmdb.org/t/p/w342'+m.metadata.poster_path)}"
              alt={m.metadata.title} class="rounded-lg w-full aspect-[2/3] object-cover" />
          {:else}
            <div class="rounded-lg w-full aspect-[2/3] bg-[#1a1714] flex items-center justify-center text-xs text-[#9a9080] text-center p-2">
              {m.metadata.title}
            </div>
          {/if}
          <div class="text-xs text-[#e8e0d0] truncate">{m.metadata.title}</div>
          <div class="flex items-center gap-1">
            {#if m.metadata.rating}<span class="text-xs text-[#c8a84b]">{'★'.repeat(m.metadata.rating)}</span>{/if}
            <span class="text-xs text-[#9a9080]">{m.metadata.year}</span>
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>

{#if expandedMovie}
  <div class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-8"
    on:click={() => expandedMovie=null}>
    <div class="bg-[#242019] rounded-2xl overflow-hidden max-w-2xl w-full flex shadow-2xl"
      on:click|stopPropagation>
      {#if expandedMovie.metadata.poster_path}
        <img src="/api/img?url={encodeURIComponent('https://image.tmdb.org/t/p/w342'+expandedMovie.metadata.poster_path)}"
          alt={expandedMovie.metadata.title} class="w-40 shrink-0 object-cover" />
      {:else}<div class="w-40 shrink-0 bg-[#1a1714]"/>{/if}
      <div class="flex flex-col gap-3 p-6 flex-1 min-w-0">
        <div class="flex items-start justify-between gap-2">
          <div>
            <div class="text-lg font-semibold">{expandedMovie.metadata.title}</div>
            <div class="text-sm text-[#9a9080]">{expandedMovie.metadata.year}</div>
          </div>
          <button on:click={() => expandedMovie=null} class="text-[#9a9080] hover:text-[#e8e0d0] shrink-0">✕</button>
        </div>
        {#if expandedMovie.metadata.rating}
          <div class="text-[#c8a84b] text-xl">{'★'.repeat(expandedMovie.metadata.rating)}{'☆'.repeat(5-expandedMovie.metadata.rating)}</div>
        {/if}
        <div class="text-xs text-[#9a9080]">Watched {new Date(expandedMovie.timestamp).toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric'})}</div>
        {#if expandedMovie.metadata.overview}
          <p class="text-xs text-[#9a9080] leading-relaxed">{expandedMovie.metadata.overview}</p>
        {/if}
        {#if expandedMovie.metadata.notes}
          <p class="text-sm text-[#c8c0b0]">{expandedMovie.metadata.notes}</p>
        {/if}
        <button on:click={async()=>{await fetch(`/api/events/${expandedMovie.id}`,{method:'DELETE'});load();expandedMovie=null;}}
          class="mt-auto text-xs text-[#c87a7a] hover:text-[#e87a7a] self-start">Delete</button>
      </div>
    </div>
  </div>
{/if}
