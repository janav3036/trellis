<script>
  import { onMount } from 'svelte';
  import HomeF1Race from '../lib/panels/HomeF1Race.svelte';
  import F1Arc from '../lib/panels/F1Arc.svelte';
  import HomeF1News from '../lib/panels/HomeF1News.svelte';

  let schedule = [], drivers = [], constructors = [], season = '';
  let activeStandings = 'drivers';
  let selectedRace = null, raceResults = null;

  let videoUrl = '';
  let editingVideo = false;
  let videoInput = '';
  let videoInputEl;

  $: nextRace = schedule.find(r => !r.completed);
  $: maxPts = constructors.length ? constructors[0].points : 1;

  const IMG_EXTS = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.avif'];
  const VID_EXTS = ['.mp4', '.webm', '.mov', '.m4v', '.ogg'];
  $: mediaLower = videoUrl.split('?')[0].toLowerCase();
  $: isImage   = IMG_EXTS.some(e => mediaLower.endsWith(e));
  $: isVideo   = VID_EXTS.some(e => mediaLower.endsWith(e));
  $: isYoutube = videoUrl.includes('youtube.com') || videoUrl.includes('youtu.be');
  $: youtubeId = isYoutube
    ? (videoUrl.match(/(?:v=|youtu\.be\/)([^&?/]+)/) || [])[1]
    : null;

  function startEditVideo() {
    videoInput = videoUrl;
    editingVideo = true;
    setTimeout(() => videoInputEl?.focus(), 50);
  }

  function confirmVideo() {
    videoUrl = videoInput.trim();
    localStorage.setItem('f1-video-url', videoUrl);
    editingVideo = false;
  }

  function fmt(dateStr) {
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  async function openRace(race) {
    if (!race.completed) return;
    selectedRace = race;
    raceResults = null;
    const res = await fetch(`/api/f1/race-results/${race.round}`);
    raceResults = await res.json();
  }

  onMount(async () => {
    videoUrl = localStorage.getItem('f1-video-url') || '';
    const [schRes, standRes] = await Promise.all([
      fetch('/api/f1/schedule'),
      fetch('/api/f1/standings'),
    ]);
    const schData = await schRes.json();
    season = schData.season;
    schedule = schData.races;
    const stands = await standRes.json();
    drivers = stands.drivers;
    constructors = stands.constructors;
  });
</script>

<!-- F1-themed page: near-black bg, red accent -->
<main class="p-5 min-h-screen" style="background:#0d0d0f; color:#f0f0f2">

  <!-- Bento grid: fills viewport height -->
  <div class="grid gap-4 mb-5"
    style="grid-template-columns: 35fr 35fr 30fr; grid-template-rows: 55fr 45fr; height: calc(100vh - 2.5rem)">

    <!-- Next Race: col 1, row 1 -->
    <div class="h-full" style="grid-column: 1; grid-row: 1">
      <HomeF1Race theme="f1" />
    </div>

    <!-- Driver / Constructor Leaderboard: col 2, row 1 -->
    <div class="rounded-xl p-4 flex flex-col overflow-hidden h-full"
         style="background:#18181c; grid-column: 2; grid-row: 1">

      <!-- Toggle -->
      <div class="flex items-center gap-1 shrink-0 mb-4 p-0.5 rounded-lg" style="background:#0d0d0f">
        <button
          on:click={() => activeStandings = 'drivers'}
          class="flex-1 text-xs font-bold uppercase tracking-widest py-1.5 rounded-md transition-all"
          style="background:{activeStandings === 'drivers' ? '#e8002d' : 'transparent'};
                 color:{activeStandings === 'drivers' ? '#fff' : '#666'}"
        >Drivers</button>
        <button
          on:click={() => activeStandings = 'constructors'}
          class="flex-1 text-xs font-bold uppercase tracking-widest py-1.5 rounded-md transition-all"
          style="background:{activeStandings === 'constructors' ? '#e8002d' : 'transparent'};
                 color:{activeStandings === 'constructors' ? '#fff' : '#666'}"
        >Constructors</button>
      </div>

      <!-- Drivers: scrollable list -->
      {#if activeStandings === 'drivers'}
        <div class="flex flex-col gap-2 overflow-y-auto flex-1" style="scrollbar-width: none">
          {#each drivers as d}
            <div class="flex items-center gap-3">
              <span class="text-xs w-5 shrink-0 tabular-nums" style="color:#555">{d.position}</span>
              <div class="flex-1 min-w-0">
                <div class="text-sm font-medium truncate">{d.driver}</div>
                <div class="text-xs truncate" style="color:#666">{d.team}</div>
              </div>
              <div class="text-right shrink-0">
                <div class="text-sm font-semibold tabular-nums">{d.points}</div>
                {#if d.wins > 0}<div class="text-xs" style="color:#e8002d">{d.wins}W</div>{/if}
              </div>
            </div>
          {/each}
        </div>

      <!-- Constructors: spread to fill full column height -->
      {:else}
        <div class="flex flex-col justify-between flex-1 overflow-hidden">
          {#each constructors as c}
            <div class="flex items-center gap-3">
              <span class="text-xs w-5 shrink-0 tabular-nums" style="color:#555">{c.position}</span>
              <div class="flex-1 min-w-0">
                <div class="text-xs font-medium truncate mb-0.5">{c.team}</div>
                <div class="h-1 rounded-full overflow-hidden" style="background:#222">
                  <div class="h-full rounded-full" style="width:{(c.points/maxPts)*100}%; background:#e8002d; opacity:0.7"></div>
                </div>
              </div>
              <div class="text-right shrink-0 ml-2">
                <div class="text-sm font-semibold tabular-nums">{c.points}</div>
                {#if c.wins > 0}<div class="text-[10px]" style="color:#e8002d">{c.wins}W</div>{/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <!-- Right column: Video (35) + News (65) — col 3, spans both rows -->
    <div class="flex flex-col gap-4" style="grid-column: 3; grid-row: 1 / 3">

      <!-- Video Player -->
      <!-- svelte-ignore a11y-click-events-have-key-events -->
      <!-- svelte-ignore a11y-no-static-element-interactions -->
      <div
        class="rounded-xl overflow-hidden relative group cursor-pointer"
        style="flex: 35; background:#18181c"
        on:click={() => !editingVideo && startEditVideo()}
      >
        {#if !videoUrl}
          <div class="absolute inset-0 flex flex-col items-center justify-center gap-2">
            <div class="text-3xl" style="color:#2a2a35">▶</div>
            <div class="text-xs" style="color:#444">Click to add media URL</div>
          </div>
        {:else if isImage}
          <img src={videoUrl} alt="media" class="absolute inset-0 w-full h-full object-cover" />
        {:else if isYoutube && youtubeId}
          <iframe
            src="https://www.youtube.com/embed/{youtubeId}?autoplay=1&mute=1&loop=1&playlist={youtubeId}&controls=0&disablekb=1&modestbranding=1"
            class="absolute inset-0 w-full h-full border-0"
            allow="autoplay; encrypted-media"
            title="F1 Video"
          />
        {:else if isVideo}
          <video src={videoUrl} autoplay loop muted playsinline
            class="absolute inset-0 w-full h-full object-cover" />
        {:else if videoUrl}
          <img src={videoUrl} alt="media" class="absolute inset-0 w-full h-full object-cover" />
        {/if}

        {#if videoUrl && !editingVideo}
          <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              on:click|stopPropagation={startEditVideo}
              class="text-xs px-2 py-1 rounded-lg"
              style="background:rgba(0,0,0,0.7); color:#888"
            >Edit URL</button>
          </div>
        {/if}

        {#if editingVideo}
          <!-- svelte-ignore a11y-click-events-have-key-events -->
          <!-- svelte-ignore a11y-no-static-element-interactions -->
          <div class="absolute inset-0 flex items-center justify-center p-5" style="background:rgba(0,0,0,0.85)" on:click|stopPropagation>
            <div class="w-full flex flex-col gap-2">
              <input
                bind:this={videoInputEl}
                type="text"
                bind:value={videoInput}
                placeholder="Paste image, video, or YouTube URL…"
                class="w-full rounded-lg px-3 py-2 text-sm"
                style="background:#0d0d0f; color:#f0f0f2; border:1px solid #2a2a35"
                on:keydown={e => { if (e.key === 'Enter') confirmVideo(); if (e.key === 'Escape') editingVideo = false; }}
              />
              <div class="flex gap-2">
                <button on:click={confirmVideo}
                  class="flex-1 font-medium px-4 py-1.5 rounded-lg text-sm"
                  style="background:#e8002d; color:#fff">Set</button>
                <button on:click={() => { if (videoUrl) { videoUrl = ''; localStorage.removeItem('f1-video-url'); } editingVideo = false; }}
                  class="px-4 py-1.5 rounded-lg text-sm"
                  style="background:#18181c; color:#888"
                >{videoUrl ? 'Clear' : 'Cancel'}</button>
              </div>
            </div>
          </div>
        {/if}
      </div>

      <!-- F1 News -->
      <div class="min-h-0" style="flex: 65">
        <HomeF1News theme="f1" />
      </div>
    </div>

    <!-- Championship Arc: cols 1–2, row 2 -->
    <div class="h-full" style="grid-column: 1 / 3; grid-row: 2">
      <F1Arc />
    </div>

  </div>

  <!-- Calendar: 6 per row -->
  <h2 class="text-xs font-bold uppercase tracking-widest mb-4" style="color:#444">
    F1 {season} Calendar
  </h2>
  <div class="grid gap-3" style="grid-template-columns: repeat(6, 1fr)">
    {#each schedule as race}
      {@const isNext = nextRace?.round === race.round}
      <button
        on:click={() => openRace(race)}
        disabled={!race.completed}
        class="rounded-xl p-4 text-left flex flex-col transition-all"
        style="background:{isNext ? '#1e0a0d' : '#18181c'};
               border:1px solid {isNext ? '#e8002d' : 'transparent'};
               opacity:{race.completed ? 0.45 : 1};
               cursor:{race.completed ? 'pointer' : 'default'}"
        on:mouseenter={e => { if (race.completed) e.currentTarget.style.opacity = '0.7'; }}
        on:mouseleave={e => { if (race.completed) e.currentTarget.style.opacity = '0.45'; }}
      >
        <div class="text-[10px] tabular-nums mb-1" style="color:#444">Round {race.round}</div>
        <div class="text-sm font-semibold leading-tight mb-1">{race.name.replace(' Grand Prix', ' GP')}</div>
        <div class="text-xs truncate" style="color:#666">{race.circuit}</div>
        <div class="text-xs mt-0.5" style="color:#555">{race.country}</div>
        <div class="text-xs mt-2" style="color:#444">{fmt(race.date)}</div>
        {#if isNext}
          <div class="text-[10px] mt-1.5 font-bold" style="color:#e8002d">NEXT RACE</div>
        {:else if race.completed}
          <div class="text-[10px] mt-1.5" style="color:#333">✓</div>
        {/if}
      </button>
    {/each}
  </div>

</main>

<!-- Race result modal -->
{#if selectedRace}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div
    class="fixed inset-0 flex items-center justify-center z-50 p-4"
    style="background:rgba(0,0,0,0.75)"
    on:click|self={() => { selectedRace = null; raceResults = null; }}
  >
    <div class="rounded-2xl w-full max-w-md max-h-[80vh] flex flex-col" style="background:#18181c">
      <div class="p-5 shrink-0" style="border-bottom:1px solid #222">
        <div class="flex items-start justify-between">
          <div>
            <div class="text-base font-semibold">{selectedRace.name}</div>
            <div class="text-sm mt-0.5" style="color:#666">{selectedRace.circuit} · {fmt(selectedRace.date)}</div>
          </div>
          <button
            on:click={() => { selectedRace = null; raceResults = null; }}
            class="text-xl leading-none ml-4"
            style="color:#555"
          >×</button>
        </div>
      </div>
      <div class="overflow-y-auto p-5">
        {#if !raceResults}
          <p class="text-sm animate-pulse" style="color:#555">Loading…</p>
        {:else}
          <div class="space-y-1">
            {#each raceResults.results as r}
              <div class="flex items-center gap-3 py-1.5">
                <span class="text-xs w-5 shrink-0 tabular-nums" style="color:#555">{r.position}</span>
                <div class="flex-1 min-w-0">
                  <span class="text-sm font-medium">{r.driver}</span>
                  {#if r.fastest_lap}
                    <span class="text-xs ml-1" style="color:#e8002d">⚡</span>
                  {/if}
                  <div class="text-xs" style="color:#666">{r.team}</div>
                </div>
                <div class="text-right shrink-0">
                  <div class="text-sm tabular-nums">{r.points > 0 ? `+${r.points}` : ''}</div>
                  {#if r.status !== 'Finished'}
                    <div class="text-xs" style="color:#555">{r.status}</div>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}
