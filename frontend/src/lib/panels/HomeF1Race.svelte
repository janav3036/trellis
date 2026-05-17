<script>
  import { onMount } from 'svelte';
  let season = '', nextRace = null, daysAway = null;
  let racePhotos = [], showUpload = false, selectedPhoto = null;
  let uploadRound = '', uploadCaption = '', uploadUrl = '', uploadUploading = false, uploadError = '';
  let races = [];

  function fmt(dateStr) {
    return new Date(dateStr + 'T12:00:00').toLocaleDateString('en-US', {
      weekday: 'short', day: 'numeric', month: 'long'
    });
  }

  function countdown(days) {
    if (days <= 0)  return 'Race day!';
    if (days === 1) return 'Tomorrow';
    return `In ${days} days`;
  }

  // Flat list ordered by round descending (most recent first)
  $: allPhotos = [...racePhotos].sort((a, b) => b.round - a.round);
  let photoIdx = 0;
  $: if (allPhotos.length && photoIdx >= allPhotos.length) photoIdx = 0;

  async function loadPhotos() {
    racePhotos = await (await fetch('/api/f1/photos')).json();
  }

  async function handleFileChange(e) {
    const file = e.target.files[0];
    if (!file) return;
    uploadUploading = true;
    uploadError = '';
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch('/api/f1/photos/upload', { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok || !data.url) throw new Error(data.error || 'Upload failed');
      uploadUrl = data.url;
    } catch (err) {
      uploadError = err.message;
    }
    uploadUploading = false;
  }

  async function submitPhoto() {
    if (!uploadUrl || !uploadRound) return;
    const race = races.find(r => String(r.round) === String(uploadRound));
    await fetch('/api/f1/photos/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        round: uploadRound,
        race_name: race?.name || '',
        url: uploadUrl,
        caption: uploadCaption,
        date: race?.date || new Date().toISOString().slice(0, 10),
      }),
    });
    uploadUrl = ''; uploadCaption = ''; showUpload = false;
    loadPhotos();
  }

  async function deletePhoto(id) {
    await fetch(`/api/f1/photos/${id}`, { method: 'DELETE' });
    loadPhotos();
  }

  onMount(async () => {
    const res = await fetch('/api/f1/schedule');
    const data = await res.json();
    season = data.season;
    races = data.races;
    const today = new Date().toISOString().slice(0, 10);
    nextRace = data.races.find(r => !r.completed) || null;
    if (nextRace) {
      daysAway = Math.ceil((new Date(nextRace.date) - new Date(today)) / 86400000);
    }
    if (!uploadRound && races.length) {
      const last = [...races].reverse().find(r => r.completed);
      uploadRound = last ? String(last.round) : String(races[0].round);
    }
    loadPhotos();
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 h-full flex flex-col overflow-hidden">
  <!-- Header -->
  <div class="flex items-center justify-between shrink-0 mb-2">
    <a href="/#/f1"
       class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider hover:text-[#e8e0d0] transition-colors">
      F1 {season} · Next Race
    </a>
    <button on:click={() => showUpload = !showUpload}
      class="text-xs text-[#9a9080] hover:text-[#e8e0d0] transition-colors">+</button>
  </div>

  <!-- Next race info -->
  {#if nextRace}
    <div class="shrink-0">
      <div class="text-base font-semibold leading-tight">{nextRace.name}</div>
      <div class="text-xs text-[#9a9080]">{nextRace.circuit} · {nextRace.country}</div>
      <div class="flex items-center gap-2 mt-0.5">
        <span class="text-xs text-[#9a9080]">{fmt(nextRace.date)}</span>
        <span class="text-xs font-medium" style="color: var(--accent, #c8813a)">{countdown(daysAway)}</span>
      </div>
    </div>
  {:else}
    <p class="text-sm text-[#9a9080] shrink-0">Season complete</p>
  {/if}

  <!-- Race photos: indexed single photo with arrow nav -->
  {#if allPhotos.length > 0}
    {@const photo = allPhotos[photoIdx]}
    <div class="flex-1 min-h-0 mt-3 flex flex-col gap-1">
      <div class="relative group flex-1 min-h-0 flex items-center justify-center rounded-lg overflow-hidden">
        <img src={photo.url} alt={photo.caption || photo.race_name}
          class="rounded-lg object-cover cursor-pointer"
          style="height:100%; width:auto; max-width:100%"
          on:click={() => selectedPhoto = photo} />
        <div class="absolute bottom-0 left-0 right-0 px-2 pb-2 pt-6 pointer-events-none
                    bg-gradient-to-t from-black/70 to-transparent rounded-b-lg">
          <div class="text-[11px] font-medium text-white leading-tight">
            {photo.race_name || `Round ${photo.round}`}
          </div>
          {#if photo.caption}
            <div class="text-[10px] text-white/70">{photo.caption}</div>
          {/if}
        </div>
        <button on:click={() => deletePhoto(photo.id)}
          class="absolute top-1.5 right-1.5 bg-black/60 text-[#c87a7a] text-[10px]
                 px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity">✕</button>
      </div>
      <!-- Navigation -->
      <div class="flex items-center justify-center gap-3 shrink-0">
        <button on:click={() => photoIdx = (photoIdx - 1 + allPhotos.length) % allPhotos.length}
          class="text-[#9a9080] hover:text-[#e8e0d0] text-xs px-2">‹</button>
        <span class="text-[10px] text-[#6a6058]">{photoIdx + 1} / {allPhotos.length}</span>
        <button on:click={() => photoIdx = (photoIdx + 1) % allPhotos.length}
          class="text-[#9a9080] hover:text-[#e8e0d0] text-xs px-2">›</button>
      </div>
    </div>
  {:else}
    <!-- SVG track placeholder when no photos -->
    <div class="flex-1 flex items-center justify-center min-h-0 mt-2">
      <svg viewBox="0 0 220 110" class="w-full max-h-full opacity-50" xmlns="http://www.w3.org/2000/svg">
        <path d="M 35 80 Q 12 80 12 58 Q 12 22 50 22 L 145 22 Q 178 22 196 40
                 L 206 58 Q 206 80 188 80 L 110 80 Q 92 80 92 64 Q 92 52 110 52
                 L 168 52 Q 178 52 178 62"
              fill="none" stroke="#6a6058" stroke-width="8"
              stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M 50 48 Q 50 36 62 36 L 100 36"
              fill="none" stroke="#4a4038" stroke-width="4"
              stroke-linecap="round"/>
        <line x1="35" y1="74" x2="35" y2="86" stroke="#c8813a" stroke-width="2.5" stroke-linecap="round"/>
      </svg>
    </div>
  {/if}
</div>

<!-- Photo lightbox -->
{#if selectedPhoto}
  <div class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8"
       on:click={() => selectedPhoto = null}>
    <div class="bg-[#242019] rounded-2xl overflow-hidden max-w-lg w-full shadow-2xl"
         on:click|stopPropagation>
      <img src={selectedPhoto.url} alt={selectedPhoto.caption || selectedPhoto.race_name}
           class="w-full max-h-[70vh] object-contain bg-black" />
      <div class="px-5 py-4 flex items-start justify-between gap-4">
        <div>
          <div class="text-sm font-semibold">{selectedPhoto.race_name || `Round ${selectedPhoto.round}`}</div>
          {#if selectedPhoto.caption}
            <p class="text-sm text-[#9a9080] mt-1">{selectedPhoto.caption}</p>
          {/if}
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <button on:click={async () => { await deletePhoto(selectedPhoto.id); selectedPhoto = null; }}
            class="text-xs text-[#c87a7a] hover:text-[#e87a7a]">Delete</button>
          <button on:click={() => selectedPhoto = null}
            class="text-[#9a9080] hover:text-[#e8e0d0]">✕</button>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Upload modal -->
{#if showUpload}
  <div class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-6"
       on:click={() => showUpload = false}>
    <div class="bg-[#242019] rounded-2xl p-5 w-full max-w-sm flex flex-col gap-3 shadow-2xl"
         on:click|stopPropagation>
      <div class="text-sm font-semibold">Add Race Photos</div>

      <div class="flex flex-col gap-1">
        <label class="text-xs text-[#9a9080]">Race</label>
        <select bind:value={uploadRound}
          class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]">
          {#each races as r}
            <option value={String(r.round)}>Round {r.round} · {r.name}</option>
          {/each}
        </select>
      </div>

      <div class="flex flex-col gap-1">
        <label class="text-xs text-[#9a9080]">Image</label>
        <input type="file" accept="image/*" on:change={handleFileChange}
          class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]" />
        {#if uploadUploading}
          <p class="text-xs text-[#9a9080] animate-pulse">Uploading…</p>
        {:else if uploadError}
          <p class="text-xs text-[#c87a7a]">{uploadError}</p>
        {:else if uploadUrl}
          <img src={uploadUrl} alt="preview" class="h-24 w-full object-cover rounded-lg mt-1" />
        {/if}
      </div>

      <div class="flex flex-col gap-1">
        <label class="text-xs text-[#9a9080]">Caption <span class="text-[#5a5040]">(optional)</span></label>
        <input type="text" bind:value={uploadCaption} placeholder="Podium at Monaco…"
          class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]" />
      </div>

      <div class="flex gap-2">
        <button on:click={submitPhoto} disabled={!uploadUrl || !uploadRound}
          class="bg-[#c8813a] hover:bg-[#d8914a] disabled:opacity-40 text-[#1a1714] font-medium
                 px-4 py-2 rounded-lg text-sm flex-1">
          Save
        </button>
        <button on:click={() => showUpload = false}
          class="bg-[#1a1714] hover:bg-[#2a2520] text-[#9a9080] px-4 py-2 rounded-lg text-sm">
          Cancel
        </button>
      </div>
    </div>
  </div>
{/if}
