<script>
  import { onMount } from 'svelte';
  import HomeF1Race from '../lib/panels/HomeF1Race.svelte';
  import F1Arc from '../lib/panels/F1Arc.svelte';
  import HomeF1News from '../lib/panels/HomeF1News.svelte';

  let schedule = [], drivers = [], constructors = [], season = '';
  let activeStandings = 'drivers';
  let selectedRace = null, raceResults = null;
  let videoUrl = '', editingVideo = false, videoInput = '', videoInputEl;

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

  const TEAM_COLORS = {
    'red bull': '#3671C6',
    'ferrari': '#E8002D',
    'mercedes': '#27F4D2',
    'mclaren': '#FF8000',
    'aston martin': '#229971',
    'alpine': '#FF87BC',
    'williams': '#64C4FF',
    'rb': '#6692FF',
    'kick sauber': '#52E252',
    'sauber': '#52E252',
    'haas': '#B6BABD',
  };

  function teamColor(name) {
    if (!name) return '#555';
    const lower = name.toLowerCase();
    for (const [k, v] of Object.entries(TEAM_COLORS)) {
      if (lower.includes(k)) return v;
    }
    return '#666';
  }

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

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="" />
  <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&display=swap" rel="stylesheet" />
</svelte:head>

<main class="f1-root">

  <!-- 12-col bento grid -->
  <div class="bento">

    <!-- Race photo — cols 1–4, row 1 -->
    <div class="cell" style="grid-column:1/5;grid-row:1;animation-delay:0.04s">
      <HomeF1Race theme="f1" />
    </div>

    <!-- Championship standings — cols 5–8, row 1 -->
    <div class="cell standings-cell" style="grid-column:5/9;grid-row:1;animation-delay:0.08s">
      <div class="eyebrow">Championship</div>

      <div class="tab-bar">
        <button class="tab" class:active={activeStandings === 'drivers'}
          on:click={() => activeStandings = 'drivers'}>Drivers</button>
        <button class="tab" class:active={activeStandings === 'constructors'}
          on:click={() => activeStandings = 'constructors'}>Constructors</button>
      </div>

      {#if activeStandings === 'drivers'}
        <div class="scroll-list">
          {#each drivers as d}
            <div class="d-row">
              <span class="d-pos" style="color:{d.position <= 3 ? '#e8002d' : '#2c2c32'}">{d.position}</span>
              <div class="d-info">
                <div class="d-name">{d.driver}</div>
                <div class="d-team" style="color:{teamColor(d.team)}">{d.team}</div>
              </div>
              <div class="d-right">
                <span class="d-pts">{d.points}</span>
                {#if d.wins > 0}<span class="d-wins">{d.wins}W</span>{/if}
              </div>
            </div>
          {/each}
        </div>

      {:else}
        <div class="scroll-list">
          {#each constructors as c}
            <div class="c-row">
              <div class="c-stripe" style="background:{teamColor(c.team)}"></div>
              <div class="c-body">
                <div class="c-header">
                  <span class="c-name">{c.team}</span>
                  <div class="c-right">
                    {#if c.wins > 0}<span class="c-wins" style="color:{teamColor(c.team)}">{c.wins}W</span>{/if}
                    <span class="d-pts">{c.points}</span>
                  </div>
                </div>
                <div class="c-track">
                  <div class="c-bar" style="width:{(c.points/maxPts)*100}%;background:{teamColor(c.team)}"></div>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <!-- F1 News — cols 9–12, row 1 -->
    <div class="cell" style="grid-column:9/13;grid-row:1;animation-delay:0.12s">
      <HomeF1News theme="f1" />
    </div>

    <!-- Championship arc — cols 1–8, row 2 -->
    <div class="cell" style="grid-column:1/9;grid-row:2;animation-delay:0.16s">
      <F1Arc />
    </div>

    <!-- Video — cols 9–12, row 2 -->
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="cell vid-cell" style="grid-column:9/13;grid-row:2;animation-delay:0.2s"
         on:click={() => !editingVideo && startEditVideo()}>

      {#if !videoUrl}
        <div class="vid-empty">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 3l14 9-14 9V3z" fill="#252530"/>
          </svg>
          <span class="vid-hint">Add media URL</span>
        </div>
      {:else if isImage}
        <img src={videoUrl} alt="media" class="vid-cover" />
      {:else if isYoutube && youtubeId}
        <iframe
          src="https://www.youtube.com/embed/{youtubeId}?autoplay=1&mute=1&loop=1&playlist={youtubeId}&controls=0&disablekb=1&modestbranding=1"
          class="vid-cover" style="border:0"
          allow="autoplay; encrypted-media" title="F1 Video"
        />
      {:else if isVideo}
        <video src={videoUrl} autoplay loop muted playsinline class="vid-cover" />
      {:else}
        <img src={videoUrl} alt="media" class="vid-cover" />
      {/if}

      {#if videoUrl && !editingVideo}
        <div class="vid-hover">
          <button on:click|stopPropagation={startEditVideo} class="vid-edit-btn">Edit URL</button>
        </div>
      {/if}

      {#if editingVideo}
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div class="vid-overlay" on:click|stopPropagation>
          <input bind:this={videoInputEl} type="text" bind:value={videoInput}
            placeholder="YouTube, image, or video URL…"
            class="vid-input"
            on:keydown={e => { if (e.key === 'Enter') confirmVideo(); if (e.key === 'Escape') editingVideo = false; }}
          />
          <div class="vid-actions">
            <button on:click={confirmVideo} class="vid-set">Set</button>
            <button on:click={() => { if (videoUrl) { videoUrl = ''; localStorage.removeItem('f1-video-url'); } editingVideo = false; }}
              class="vid-cancel">{videoUrl ? 'Clear' : 'Cancel'}</button>
          </div>
        </div>
      {/if}
    </div>

  </div>

  <!-- Season calendar -->
  <div class="cal-section">
    <div class="cal-header">
      <span class="cal-title">Formula 1 · {season} Season</span>
      <div class="cal-legend">
        <span class="leg done">completed</span>
        <span class="leg next">next race</span>
        <span class="leg up">upcoming</span>
      </div>
    </div>

    <div class="cal-grid">
      {#each schedule as race}
        {@const isNext = nextRace?.round === race.round}
        <button
          on:click={() => openRace(race)}
          disabled={!race.completed}
          class="cal-card"
          class:is-next={isNext}
          class:is-done={race.completed && !isNext}
        >
          <div class="cal-round">{String(race.round).padStart(2,'0')}</div>
          <div class="cal-gp">{race.name.replace(' Grand Prix','').replace('Grand Prix','GP')}</div>
          <div class="cal-country">{race.country}</div>
          <div class="cal-date">{fmt(race.date)}</div>
          {#if isNext}
            <div class="cal-next-pill">NEXT</div>
          {:else if race.completed}
            <div class="cal-check">✓</div>
          {/if}
        </button>
      {/each}
    </div>
  </div>

</main>

<!-- Race results modal -->
{#if selectedRace}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="modal-bg" on:click|self={() => { selectedRace = null; raceResults = null; }}>
    <div class="modal">
      <div class="modal-head">
        <div>
          <div class="modal-title">{selectedRace.name}</div>
          <div class="modal-sub">{selectedRace.circuit} · {fmt(selectedRace.date)}</div>
        </div>
        <button on:click={() => { selectedRace = null; raceResults = null; }} class="modal-x">×</button>
      </div>
      <div class="modal-body">
        {#if !raceResults}
          <p class="modal-loading">Loading results…</p>
        {:else}
          {#each raceResults.results as r}
            <div class="res-row">
              <span class="res-pos" style="color:{r.position <= 3 ? '#e8002d' : '#3a3a42'}">{r.position}</span>
              <div class="res-info">
                <div class="res-driver">
                  {r.driver}
                  {#if r.fastest_lap}<span class="res-flash">⚡</span>{/if}
                </div>
                <div class="res-team" style="color:{teamColor(r.team)}">{r.team}</div>
              </div>
              <div class="res-right">
                {#if r.points > 0}<div class="res-pts">+{r.points}</div>{/if}
                {#if r.status !== 'Finished'}<div class="res-status">{r.status}</div>{/if}
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .f1-root {
    background: radial-gradient(ellipse at 0% 0%, rgba(232,0,45,0.05) 0%, #0d0d0f 45%);
    color: #f0f0f2;
    padding: 18px;
    min-height: 100vh;
    box-sizing: border-box;
  }

  /* ── Bento grid ── */
  .bento {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    grid-template-rows: 52vh 34vh;
    gap: 10px;
    margin-bottom: 10px;
  }

  .cell {
    border-radius: 14px;
    overflow: hidden;
    background: #18181c;
    animation: cell-in 0.38s cubic-bezier(0.22,1,0.36,1) both;
  }

  @keyframes cell-in {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* ── Standings ── */
  .standings-cell {
    padding: 14px;
    display: flex;
    flex-direction: column;
  }

  .eyebrow {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: #383840;
    margin-bottom: 10px;
    flex-shrink: 0;
  }

  .tab-bar {
    display: flex;
    gap: 2px;
    background: #0d0d0f;
    padding: 3px;
    border-radius: 8px;
    margin-bottom: 10px;
    flex-shrink: 0;
  }
  .tab {
    flex: 1;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 5px 0;
    border-radius: 6px;
    border: none;
    background: transparent;
    color: #3a3a44;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .tab.active {
    background: #e8002d;
    color: #fff;
  }

  .scroll-list {
    flex: 1;
    overflow-y: auto;
    min-height: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
    scrollbar-width: none;
  }

  /* Driver rows */
  .d-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 6px;
    border-radius: 8px;
    transition: background 0.12s ease;
  }
  .d-row:hover { background: rgba(255,255,255,0.03); }

  .d-pos {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 20px;
    font-weight: 800;
    width: 26px;
    text-align: center;
    flex-shrink: 0;
    line-height: 1;
    transition: color 0.15s;
  }
  .d-info { flex: 1; min-width: 0; }
  .d-name {
    font-size: 12px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: #d8d8e0;
  }
  .d-team {
    font-size: 10px;
    margin-top: 1px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .d-right { text-align: right; flex-shrink: 0; }
  .d-pts {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 17px;
    font-weight: 700;
    line-height: 1;
    color: #c8c8d0;
  }
  .d-wins {
    display: block;
    font-size: 9px;
    color: #e8002d;
    letter-spacing: 0.05em;
    margin-top: 1px;
  }

  /* Constructor rows */
  .c-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 7px 6px;
    border-radius: 8px;
    transition: background 0.12s ease;
  }
  .c-row:hover { background: rgba(255,255,255,0.03); }
  .c-stripe {
    width: 3px;
    height: 36px;
    border-radius: 2px;
    flex-shrink: 0;
    opacity: 0.8;
  }
  .c-body { flex: 1; min-width: 0; }
  .c-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 5px;
  }
  .c-name {
    font-size: 12px;
    font-weight: 500;
    color: #d0d0d8;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .c-right {
    display: flex;
    align-items: baseline;
    gap: 6px;
    flex-shrink: 0;
  }
  .c-wins {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.04em;
  }
  .c-track {
    height: 3px;
    background: #1e1e24;
    border-radius: 2px;
    overflow: hidden;
  }
  .c-bar {
    height: 100%;
    border-radius: 2px;
    opacity: 0.7;
    transition: width 0.6s cubic-bezier(0.22,1,0.36,1);
  }

  /* ── Video ── */
  .vid-cell {
    position: relative;
    cursor: pointer;
  }
  .vid-empty {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: #111115;
    border: 1px dashed #22222a;
    border-radius: 14px;
    transition: border-color 0.2s;
  }
  .vid-cell:hover .vid-empty { border-color: #333340; }
  .vid-hint {
    font-size: 11px;
    color: #2c2c38;
    letter-spacing: 0.06em;
  }
  .vid-cover {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
  .vid-hover {
    position: absolute;
    top: 8px;
    right: 8px;
    opacity: 0;
    transition: opacity 0.15s;
  }
  .vid-cell:hover .vid-hover { opacity: 1; }
  .vid-edit-btn {
    font-size: 10px;
    padding: 4px 10px;
    border-radius: 6px;
    background: rgba(0,0,0,0.75);
    color: #666;
    border: none;
    cursor: pointer;
    transition: color 0.15s;
  }
  .vid-edit-btn:hover { color: #f0f0f2; }
  .vid-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.9);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 18px;
    gap: 8px;
    border-radius: 14px;
  }
  .vid-input {
    width: 100%;
    background: #0d0d0f;
    color: #f0f0f2;
    border: 1px solid #2a2a35;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
    outline: none;
    box-sizing: border-box;
    transition: border-color 0.15s;
  }
  .vid-input:focus { border-color: #e8002d; }
  .vid-actions { display: flex; gap: 6px; width: 100%; }
  .vid-set {
    flex: 1;
    background: #e8002d;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 8px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.15s;
  }
  .vid-set:hover { background: #c8001f; }
  .vid-cancel {
    background: #1e1e26;
    color: #555;
    border: none;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
    cursor: pointer;
    transition: color 0.15s;
  }
  .vid-cancel:hover { color: #888; }

  /* ── Calendar ── */
  .cal-section { margin-top: 4px; }
  .cal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
  }
  .cal-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #333340;
  }
  .cal-legend { display: flex; gap: 14px; }
  .leg {
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .leg.done { color: #2c2c36; }
  .leg.next { color: #e8002d; }
  .leg.up   { color: #404050; }

  .cal-grid {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 6px;
  }

  .cal-card {
    background: #111115;
    border-radius: 10px;
    padding: 10px 10px 8px;
    text-align: left;
    border: 1px solid transparent;
    cursor: default;
    transition: background 0.15s, opacity 0.15s, border-color 0.15s;
    display: flex;
    flex-direction: column;
    gap: 1px;
    box-sizing: border-box;
  }
  .cal-card.is-done {
    opacity: 0.4;
    cursor: pointer;
  }
  .cal-card.is-done:hover {
    opacity: 0.65;
    background: #181820;
  }
  .cal-card.is-next {
    background: #170507;
    border-color: rgba(232,0,45,0.35);
    cursor: default;
  }

  .cal-round {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 22px;
    font-weight: 800;
    line-height: 1;
    color: #1e1e26;
    margin-bottom: 3px;
  }
  .is-next .cal-round { color: rgba(232,0,45,0.35); }

  .cal-gp {
    font-size: 10.5px;
    font-weight: 600;
    line-height: 1.2;
    color: #b0b0bc;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .cal-country {
    font-size: 9px;
    color: #38383e;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 1px;
  }
  .cal-date {
    font-size: 9px;
    color: #2a2a34;
    font-variant-numeric: tabular-nums;
    margin-top: 2px;
  }
  .cal-next-pill {
    margin-top: 5px;
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.12em;
    color: #e8002d;
  }
  .cal-check {
    margin-top: 5px;
    font-size: 9px;
    color: #252530;
  }

  /* ── Modal ── */
  .modal-bg {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.82);
    z-index: 50;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
  }
  .modal {
    background: #18181c;
    border-radius: 18px;
    width: 100%;
    max-width: 420px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid #222228;
    box-shadow: 0 24px 64px rgba(0,0,0,0.7);
  }
  .modal-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 18px 20px 16px;
    border-bottom: 1px solid #1c1c22;
    flex-shrink: 0;
  }
  .modal-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.02em;
    color: #f0f0f2;
  }
  .modal-sub { font-size: 12px; color: #444; margin-top: 3px; }
  .modal-x {
    font-size: 24px;
    color: #333;
    background: none;
    border: none;
    cursor: pointer;
    line-height: 1;
    padding: 0;
    transition: color 0.15s;
    margin-left: 12px;
    flex-shrink: 0;
  }
  .modal-x:hover { color: #f0f0f2; }
  .modal-body { overflow-y: auto; padding: 14px 20px; flex: 1; }
  .modal-loading { font-size: 13px; color: #444; }

  .res-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0;
    border-bottom: 1px solid #1a1a1e;
  }
  .res-row:last-child { border-bottom: none; }
  .res-pos {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 22px;
    font-weight: 800;
    width: 30px;
    text-align: center;
    flex-shrink: 0;
    line-height: 1;
  }
  .res-info { flex: 1; min-width: 0; }
  .res-driver { font-size: 13px; font-weight: 500; color: #d8d8e0; }
  .res-team   { font-size: 10px; margin-top: 1px; }
  .res-flash  { font-size: 11px; color: #e8002d; margin-left: 4px; }
  .res-right  { text-align: right; flex-shrink: 0; }
  .res-pts    { font-size: 12px; color: #555; font-variant-numeric: tabular-nums; }
  .res-status { font-size: 10px; color: #3a3a40; margin-top: 1px; }
</style>
