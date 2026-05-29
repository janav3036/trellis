<script>
  import { onMount } from 'svelte';
  import { musicTheme } from '../musicTheme.js';

  let weeks   = [];
  let loading = true;
  let scrollEl;

  function weatherColor(code) {
    if (code == null) return 'rgba(100,85,75,0.72)';
    if (code === 0)   return 'rgba(212,168,67,0.82)';
    if (code <= 3)    return 'rgba(170,140,85,0.72)';
    if (code <= 48)   return 'rgba(105,125,132,0.72)';
    if (code <= 55)   return 'rgba(80,115,148,0.78)';
    if (code <= 65)   return 'rgba(58,92,140,0.82)';
    if (code <= 77)   return 'rgba(130,162,188,0.60)';
    if (code <= 82)   return 'rgba(68,112,122,0.78)';
    return 'rgba(95,68,128,0.82)';
  }

  function formatMonth(key) {
    const [yearStr, wStr] = key.split('-W');
    const year = parseInt(yearStr);
    const week = parseInt(wStr);
    const jan4 = new Date(year, 0, 4);
    const dow  = jan4.getDay() || 7;
    const monday = new Date(jan4.getTime() - (dow - 1) * 86400000 + (week - 1) * 7 * 86400000);
    return monday.toLocaleString('en', { month: 'short' }) + " '" + String(year).slice(2);
  }

  function weekNum(key) {
    return 'W' + key.split('-W')[1];
  }

  function groupWeeks(ws) {
    const out = [];
    let i = 0;
    while (i < ws.length) {
      if (ws[i].chapter) {
        const name  = ws[i].chapter;
        const start = i;
        while (i < ws.length && ws[i].chapter === name) i++;
        out.push({ type: 'chapter', name, weeks: ws.slice(start, i) });
      } else {
        out.push({ type: 'solo', week: ws[i] });
        i++;
      }
    }
    return out;
  }

  $: groups  = groupWeeks(weeks);
  $: maxPlays = weeks.length ? Math.max(...weeks.map(w => w.play_count)) : 1;

  function barH(plays) {
    const MIN = 6, MAX = 68;
    return MIN + (plays / maxPlays) * (MAX - MIN);
  }

  function fmtPlays(n) {
    return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n);
  }

  onMount(async () => {
    const res = await fetch('/api/spotify/archaeology');
    weeks = await res.json();
    loading = false;
    setTimeout(() => { if (scrollEl) scrollEl.scrollLeft = scrollEl.scrollWidth; }, 120);
  });
</script>

<div class="panel" style="background:{$musicTheme.card}">

  <div class="panel-head">
    <span class="panel-title" style="color:{$musicTheme.muted}">Playlist Archaeologist</span>
    {#if weeks.length}
      <span class="panel-meta" style="color:{$musicTheme.muted}">
        {weeks.length} weeks &middot; {formatMonth(weeks[0].week)} &rarr; now
      </span>
    {/if}
  </div>

  {#if loading}
    <div class="empty" style="color:{$musicTheme.muted}">Loading timeline…</div>
  {:else}
    <div class="timeline" bind:this={scrollEl}>

      {#each groups as g}

        {#if g.type === 'chapter'}
          <div class="chapter-group">
            <div class="chapter-head">
              <span class="chapter-name" style="color:{$musicTheme.accent}">{g.name}</span>
              <span class="chapter-rule" style="background:{$musicTheme.border}"></span>
              <span class="chapter-len" style="color:{$musicTheme.muted}">{g.weeks.length}w</span>
            </div>
            <div class="chapter-row">
              {#each g.weeks as w}
                <div class="card chapter-card"
                     style="background:{$musicTheme.bg}; border-color:{$musicTheme.border}; border-left-color:{$musicTheme.accent}">
                  <div class="bar-zone">
                    <div class="bar" style="height:{barH(w.play_count)}px; background:{weatherColor(w.weathercode)}"></div>
                  </div>
                  <div class="card-body" style="border-color:{$musicTheme.border}">
                    <div class="wlabel" style="color:{$musicTheme.muted}">{weekNum(w.week)} &middot; {formatMonth(w.week)}</div>
                    <div class="artist" style="color:{$musicTheme.text}">{w.top_artist}</div>
                    {#each w.top_tracks as t}
                      <div class="track" style="color:{$musicTheme.muted}">{t}</div>
                    {/each}
                  </div>
                  <div class="plays" style="color:{$musicTheme.accent}">{fmtPlays(w.play_count)}</div>
                </div>
              {/each}
            </div>
          </div>

        {:else}
          {@const w = g.week}
          <div class="card"
               style="background:{$musicTheme.bg}; border-color:{$musicTheme.border}">
            <div class="bar-zone">
              <div class="bar" style="height:{barH(w.play_count)}px; background:{weatherColor(w.weathercode)}"></div>
            </div>
            <div class="card-body" style="border-color:{$musicTheme.border}">
              <div class="wlabel" style="color:{$musicTheme.muted}">{weekNum(w.week)} &middot; {formatMonth(w.week)}</div>
              <div class="artist" style="color:{$musicTheme.text}">{w.top_artist}</div>
              {#each w.top_tracks as t}
                <div class="track" style="color:{$musicTheme.muted}">{t}</div>
              {/each}
            </div>
            <div class="plays" style="color:{$musicTheme.muted}">{fmtPlays(w.play_count)}</div>
          </div>
        {/if}

      {/each}
    </div>
  {/if}

</div>

<style>
  .panel {
    border-radius: 14px;
    padding: 16px 20px 14px;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .panel-head {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 12px;
    flex-shrink: 0;
  }

  .panel-title {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }

  .panel-meta {
    font-size: 11px;
    letter-spacing: 0.02em;
  }

  .empty {
    font-size: 13px;
    padding: 16px 0;
  }

  /* ── Timeline scroll strip ── */
  .timeline {
    display: flex;
    align-items: flex-end;
    gap: 5px;
    overflow-x: auto;
    overflow-y: visible;
    flex: 1;
    padding-bottom: 2px;
    scrollbar-width: none;
  }
  .timeline::-webkit-scrollbar { display: none; }

  /* ── Solo week card ── */
  .card {
    flex-shrink: 0;
    width: 108px;
    height: 183px;
    border-radius: 10px;
    border: 1px solid;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
    transition: transform 0.14s ease, box-shadow 0.14s ease;
    cursor: default;
  }
  .card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 24px rgba(0,0,0,0.4);
  }
  .card:hover .plays { opacity: 1; }

  /* chapter card gets a left accent */
  .chapter-card { border-left-width: 2px !important; }

  /* ── Bar zone (top 72px) ── */
  .bar-zone {
    height: 72px;
    flex-shrink: 0;
    display: flex;
    align-items: flex-end;
    padding: 0 9px;
  }
  .bar {
    width: 100%;
    border-radius: 3px 3px 0 0;
    min-height: 4px;
  }

  /* ── Text body ── */
  .card-body {
    flex: 1;
    padding: 7px 9px 5px;
    display: flex;
    flex-direction: column;
    gap: 2px;
    overflow: hidden;
    border-top: 1px solid;
  }

  .wlabel {
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 1px;
  }

  .artist {
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.3;
  }

  .track {
    font-size: 9.5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.45;
  }

  /* plays count — hidden until hover */
  .plays {
    position: absolute;
    top: 5px;
    right: 7px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.02em;
    opacity: 0;
    transition: opacity 0.14s;
    z-index: 2;
  }

  /* ── Chapter group ── */
  .chapter-group {
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 5px;
    align-self: flex-end;
  }

  .chapter-head {
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 0 1px;
    height: 16px;
  }

  .chapter-name {
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .chapter-rule {
    flex: 1;
    height: 1px;
    display: block;
    min-width: 6px;
  }

  .chapter-len {
    font-size: 9px;
    letter-spacing: 0.04em;
    flex-shrink: 0;
  }

  .chapter-row {
    display: flex;
    gap: 5px;
  }
</style>
