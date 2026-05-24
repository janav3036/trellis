<script>
  import { onMount } from 'svelte';
  import { todayIST } from '../ist.js';

  export let theme = 'home';

  $: c = theme === 'f1' ? {
    bg:        '#18181c',
    input:     '#0d0d0f',
    hover:     '#1a1a22',
    accent:    '#e8002d',
    text:      '#f0f0f2',
    muted:     '#666',
    dim:       '#444',
    vdim:      '#333',
    border:    '#2a2a35',
    del:       '#e05555',
    svgMain:   '#333',
    svgDim:    '#222',
  } : {
    bg:        'var(--surface)',
    input:     'var(--bg)',
    hover:     'var(--bg)',
    accent:    'var(--accent)',
    text:      'var(--text-primary)',
    muted:     'var(--text-secondary)',
    dim:       'var(--text-secondary)',
    vdim:      'var(--text-secondary)',
    border:    'var(--surface)',
    del:       '#c87a7a',
    svgMain:   'var(--text-secondary)',
    svgDim:    'var(--bg)',
  };

  let season = '', nextRace = null, daysAway = null;
  let racePhotos = [], showUpload = false, selectedPhoto = null;
  let uploadRound = '', uploadCaption = '', uploadUrl = '', uploadUploading = false, uploadError = '';
  let races = [];

  // ── drag-to-reposition ───────────────────────────────────────────────────────
  let positionY    = 50;
  let isDragging   = false;
  let hasDragged   = false;
  let dragStartY   = 0;
  let dragStartPos = 50;
  let containerEl;

  const POS_KEY = 'f1-photo-positions';

  function loadPosition(id) {
    try { return JSON.parse(localStorage.getItem(POS_KEY) || '{}')[id] ?? 50; }
    catch { return 50; }
  }

  function savePosition(id, y) {
    try {
      const map = JSON.parse(localStorage.getItem(POS_KEY) || '{}');
      map[id] = y;
      localStorage.setItem(POS_KEY, JSON.stringify(map));
    } catch {}
  }

  $: if (allPhotos.length) positionY = loadPosition(allPhotos[photoIdx]?.id);

  function onDragStart(e) {
    isDragging  = true;
    hasDragged  = false;
    dragStartY  = e.clientY;
    dragStartPos = positionY;
    e.preventDefault();
  }

  function onDragMove(e) {
    if (!isDragging || !containerEl) return;
    hasDragged = true;
    const h   = containerEl.getBoundingClientRect().height;
    const pct = ((e.clientY - dragStartY) / h) * 100;
    positionY = Math.min(100, Math.max(0, dragStartPos + pct));
  }

  function onDragEnd() {
    if (!isDragging) return;
    isDragging = false;
    if (hasDragged) savePosition(allPhotos[photoIdx]?.id, positionY);
  }

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
        date: race?.date || todayIST(),
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
    const today = todayIST();
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

<svelte:window on:mousemove={onDragMove} on:mouseup={onDragEnd} />

<div class="rounded-xl p-4 h-full flex flex-col overflow-hidden"
     style="background:{c.bg}; color:{c.text}">

  <!-- Header -->
  <div class="flex items-center justify-between shrink-0 mb-2">
    <a href="/#/f1"
       class="text-xs font-semibold uppercase tracking-wider transition-colors"
       style="color:{c.muted}"
       on:mouseenter={e => e.target.style.color = c.text}
       on:mouseleave={e => e.target.style.color = c.muted}>
      F1 {season} · Next Race
    </a>
    <button on:click={() => showUpload = !showUpload}
      class="text-xs transition-colors"
      style="color:{c.muted}"
      on:mouseenter={e => e.target.style.color = c.text}
      on:mouseleave={e => e.target.style.color = c.muted}>+</button>
  </div>

  <!-- Next race info -->
  {#if nextRace}
    <div class="shrink-0">
      <div class="text-base font-semibold leading-tight">{nextRace.name}</div>
      <div class="text-xs mt-0.5" style="color:{c.muted}">{nextRace.circuit} · {nextRace.country}</div>
      <div class="flex items-center gap-2 mt-0.5">
        <span class="text-xs" style="color:{c.muted}">{fmt(nextRace.date)}</span>
        <span class="text-xs font-medium" style="color:{c.accent}">{countdown(daysAway)}</span>
      </div>
    </div>
  {:else}
    <p class="text-sm shrink-0" style="color:{c.muted}">Season complete</p>
  {/if}

  <!-- Race photos -->
  {#if allPhotos.length > 0}
    {@const photo = allPhotos[photoIdx]}
    <div class="flex-1 min-h-0 mt-3 flex flex-col gap-1">
      <div class="relative group flex-1 min-h-0 rounded-lg overflow-hidden"
           bind:this={containerEl}>
        <img src={photo.url} alt={photo.caption || photo.race_name}
          class="absolute inset-0 w-full h-full object-cover select-none"
          style="object-position: center {positionY}%; cursor:{isDragging ? 'grabbing' : 'grab'}"
          on:mousedown={onDragStart}
          on:click={() => { if (!hasDragged) selectedPhoto = photo; }}
          draggable="false" />
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
          class="absolute top-1.5 right-1.5 text-[10px] px-1.5 py-0.5 rounded
                 opacity-0 group-hover:opacity-100 transition-opacity"
          style="background:rgba(0,0,0,0.6); color:{c.del}">✕</button>
      </div>
      <!-- Navigation -->
      <div class="flex items-center justify-center gap-3 shrink-0">
        <button on:click={() => photoIdx = (photoIdx - 1 + allPhotos.length) % allPhotos.length}
          class="text-xs px-2 transition-colors" style="color:{c.muted}"
          on:mouseenter={e => e.target.style.color = c.text}
          on:mouseleave={e => e.target.style.color = c.muted}>‹</button>
        <span class="text-[10px]" style="color:{c.dim}">{photoIdx + 1} / {allPhotos.length}</span>
        <button on:click={() => photoIdx = (photoIdx + 1) % allPhotos.length}
          class="text-xs px-2 transition-colors" style="color:{c.muted}"
          on:mouseenter={e => e.target.style.color = c.text}
          on:mouseleave={e => e.target.style.color = c.muted}>›</button>
      </div>
    </div>
  {:else}
    <!-- SVG track placeholder -->
    <div class="flex-1 flex items-center justify-center min-h-0 mt-2">
      <svg viewBox="0 0 220 110" class="w-full max-h-full opacity-50" xmlns="http://www.w3.org/2000/svg">
        <path d="M 35 80 Q 12 80 12 58 Q 12 22 50 22 L 145 22 Q 178 22 196 40
                 L 206 58 Q 206 80 188 80 L 110 80 Q 92 80 92 64 Q 92 52 110 52
                 L 168 52 Q 178 52 178 62"
              fill="none" stroke={c.svgMain} stroke-width="8"
              stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M 50 48 Q 50 36 62 36 L 100 36"
              fill="none" stroke={c.svgDim} stroke-width="4"
              stroke-linecap="round"/>
        <line x1="35" y1="74" x2="35" y2="86" stroke={c.accent} stroke-width="2.5" stroke-linecap="round"/>
      </svg>
    </div>
  {/if}
</div>

<!-- Photo lightbox -->
{#if selectedPhoto}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="fixed inset-0 z-50 flex items-center justify-center p-8"
       style="background:rgba(0,0,0,0.85)"
       on:click={() => selectedPhoto = null}>
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="rounded-2xl overflow-hidden max-w-lg w-full shadow-2xl"
         style="background:{c.bg}"
         on:click|stopPropagation>
      <img src={selectedPhoto.url} alt={selectedPhoto.caption || selectedPhoto.race_name}
           class="w-full max-h-[70vh] object-contain" style="background:#000" />
      <div class="px-5 py-4 flex items-start justify-between gap-4">
        <div>
          <div class="text-sm font-semibold" style="color:{c.text}">
            {selectedPhoto.race_name || `Round ${selectedPhoto.round}`}
          </div>
          {#if selectedPhoto.caption}
            <p class="text-sm mt-1" style="color:{c.muted}">{selectedPhoto.caption}</p>
          {/if}
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <button on:click={async () => { await deletePhoto(selectedPhoto.id); selectedPhoto = null; }}
            class="text-xs" style="color:{c.del}">Delete</button>
          <button on:click={() => selectedPhoto = null}
            class="text-lg leading-none" style="color:{c.muted}">✕</button>
        </div>
      </div>
    </div>
  </div>
{/if}

<!-- Upload modal -->
{#if showUpload}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="fixed inset-0 z-50 flex items-center justify-center p-6"
       style="background:rgba(0,0,0,0.85)"
       on:click={() => showUpload = false}>
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="rounded-2xl p-5 w-full max-w-sm flex flex-col gap-3 shadow-2xl"
         style="background:{c.bg}"
         on:click|stopPropagation>
      <div class="text-sm font-semibold" style="color:{c.text}">Add Race Photos</div>

      <div class="flex flex-col gap-1">
        <label class="text-xs" style="color:{c.muted}">Race</label>
        <select bind:value={uploadRound}
          class="rounded-lg px-3 py-2 text-sm"
          style="background:{c.input}; color:{c.text}; border:1px solid {c.border}">
          {#each races as r}
            <option value={String(r.round)}>Round {r.round} · {r.name}</option>
          {/each}
        </select>
      </div>

      <div class="flex flex-col gap-1">
        <label class="text-xs" style="color:{c.muted}">Image</label>
        <input type="file" accept="image/*" on:change={handleFileChange}
          class="rounded-lg px-3 py-2 text-sm"
          style="background:{c.input}; color:{c.text}; border:1px solid {c.border}" />
        {#if uploadUploading}
          <p class="text-xs animate-pulse" style="color:{c.muted}">Uploading…</p>
        {:else if uploadError}
          <p class="text-xs" style="color:{c.del}">{uploadError}</p>
        {:else if uploadUrl}
          <img src={uploadUrl} alt="preview" class="h-24 w-full object-cover rounded-lg mt-1" />
        {/if}
      </div>

      <div class="flex flex-col gap-1">
        <label class="text-xs" style="color:{c.muted}">
          Caption <span style="color:{c.vdim}">(optional)</span>
        </label>
        <input type="text" bind:value={uploadCaption} placeholder="Podium at Monaco…"
          class="rounded-lg px-3 py-2 text-sm"
          style="background:{c.input}; color:{c.text}; border:1px solid {c.border}" />
      </div>

      <div class="flex gap-2">
        <button on:click={submitPhoto} disabled={!uploadUrl || !uploadRound}
          class="font-medium px-4 py-2 rounded-lg text-sm flex-1 disabled:opacity-40"
          style="background:{c.accent}; color:{theme === 'f1' ? '#fff' : c.input}">
          Save
        </button>
        <button on:click={() => showUpload = false}
          class="px-4 py-2 rounded-lg text-sm"
          style="background:{c.input}; color:{c.muted}">
          Cancel
        </button>
      </div>
    </div>
  </div>
{/if}
