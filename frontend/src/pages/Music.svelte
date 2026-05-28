<script>
  import { onMount, onDestroy } from 'svelte';
  import { musicTheme, SPOTIFY_THEME } from '../lib/musicTheme.js';
  import MusicNowPlayingCard from '../lib/panels/MusicNowPlayingCard.svelte';
  import MusicStreak         from '../lib/panels/MusicStreak.svelte';
  import MusicTopTracks      from '../lib/panels/MusicTopTracks.svelte';
  import MusicTopArtists     from '../lib/panels/MusicTopArtists.svelte';
  import MusicHeatmap        from '../lib/panels/MusicHeatmap.svelte';
  import MusicPlaysChart     from '../lib/panels/MusicPlaysChart.svelte';
  import MusicPlaylists      from '../lib/panels/MusicPlaylists.svelte';

  let nowPlaying = null;
  let lastCover = null;
  let timer;
  let backfillDate = '';
  let backfillStatus = '';

  // ── Color extraction ──────────────────────────────────────────────
  function rgbToHsl(r, g, b) {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    let h, s, l = (max + min) / 2;
    if (max === min) { h = s = 0; }
    else {
      const d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      switch (max) {
        case r: h = (g - b) / d + (g < b ? 6 : 0); break;
        case g: h = (b - r) / d + 2; break;
        case b: h = (r - g) / d + 4; break;
      }
      h /= 6;
    }
    return [h * 360, s * 100, l * 100];
  }

  function hslToRgbStr(h, s, l) {
    h /= 360; s /= 100; l /= 100;
    if (s === 0) {
      const v = Math.round(l * 255);
      return `rgb(${v},${v},${v})`;
    }
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1; if (t > 1) t -= 1;
      if (t < 1/6) return p + (q - p) * 6 * t;
      if (t < 1/2) return q;
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
      return p;
    };
    const r = Math.round(hue2rgb(p, q, h + 1/3) * 255);
    const g = Math.round(hue2rgb(p, q, h) * 255);
    const b = Math.round(hue2rgb(p, q, h - 1/3) * 255);
    return `rgb(${r},${g},${b})`;
  }

  function buildTheme(rgb) {
    if (!rgb) return { ...SPOTIFY_THEME };
    const [r, g, b] = rgb;
    const [h, s] = rgbToHsl(r, g, b);
    if (s < 10) return { ...SPOTIFY_THEME };
    return {
      bg:      hslToRgbStr(h, Math.min(s, 25), 7),
      card:    hslToRgbStr(h, Math.min(s, 25), 13),
      cardAlt: hslToRgbStr(h, Math.min(s, 25), 20),
      accent:  hslToRgbStr(h, Math.max(s, 70), 58),
      border:  hslToRgbStr(h, Math.min(s, 25), 22),
      muted:   '#9a9080',
      text:    '#e8e0d0',
    };
  }

  async function extractColor(url) {
    return new Promise(resolve => {
      const img = new Image();
      img.onload = () => {
        try {
          const c = document.createElement('canvas');
          c.width = c.height = 64;
          const ctx = c.getContext('2d');
          ctx.drawImage(img, 0, 0, 64, 64);
          const { data } = ctx.getImageData(0, 0, 64, 64);
          let bestColor = null, bestScore = -1;
          for (let i = 0; i < data.length; i += 4) {
            const r = data[i], g = data[i+1], b = data[i+2];
            const max = Math.max(r, g, b), min = Math.min(r, g, b);
            const brightness = max / 255;
            const sat = max === 0 ? 0 : (max - min) / max;
            const score = sat * Math.max(0, 1 - Math.abs(brightness - 0.55) * 1.5);
            if (score > bestScore) { bestScore = score; bestColor = [r, g, b]; }
          }
          resolve(bestColor);
        } catch { resolve(null); }
      };
      img.onerror = () => resolve(null);
      img.src = url;
    });
  }

  async function pollNowPlaying() {
    const res = await fetch('/api/now-playing');
    nowPlaying = await res.json();
    const cover = nowPlaying?.cover ?? null;
    if (cover !== lastCover) {
      lastCover = cover;
      const rgb = cover ? await extractColor(cover) : null;
      musicTheme.set(buildTheme(rgb));
    }
  }

  async function runBackfill() {
    if (!backfillDate) return;
    backfillStatus = 'running…';
    const res = await fetch('/api/backfill/spotify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date_from: backfillDate }),
    });
    const data = await res.json();
    backfillStatus = `${data.count} new events`;
  }

  onMount(() => { pollNowPlaying(); timer = setInterval(pollNowPlaying, 10000); });
  onDestroy(() => { clearInterval(timer); musicTheme.set({ ...SPOTIFY_THEME }); });
</script>

<main
  style="
    background: linear-gradient(160deg, {$musicTheme.cardAlt} 0%, {$musicTheme.bg} 35%);
    color: {$musicTheme.text};
    transition: background 0.8s ease;
  "
  class="p-8 min-h-screen"
>
  <!-- Header -->
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-3xl font-semibold">Music</h1>
    <div class="flex items-center gap-2">
      <input
        type="date"
        bind:value={backfillDate}
        style="background:{$musicTheme.card}; border:1px solid {$musicTheme.border}; color:{$musicTheme.text}"
        class="rounded-lg px-3 py-2 text-sm outline-none"
      />
      <button
        on:click={runBackfill}
        style="background:{$musicTheme.accent}; color:{$musicTheme.bg}"
        class="font-medium px-4 py-2 rounded-lg text-sm"
      >Backfill</button>
      {#if backfillStatus}
        <span class="text-sm" style="color:{$musicTheme.muted}">{backfillStatus}</span>
      {/if}
    </div>
  </div>

  <!-- Bento grid -->
  <div class="grid gap-4" style="
    grid-template-columns: repeat(10, 1fr);
    grid-template-rows: 130px 750px 380px 420px;
  ">
    <!-- Streak: 70% width, row 1 -->
    <div style="grid-column:1/8; grid-row:1">
      <MusicStreak />
    </div>

    <!-- Now Playing Card: 30% width, spans rows 1–2 -->
    <div style="grid-column:8/11; grid-row:1/3">
      <MusicNowPlayingCard {nowPlaying} />
    </div>

    <!-- Top Tracks: ~40%, row 2 -->
    <div style="grid-column:1/5; grid-row:2">
      <MusicTopTracks />
    </div>

    <!-- Top Artists: ~30%, row 2 -->
    <div style="grid-column:5/8; grid-row:2">
      <MusicTopArtists />
    </div>

    <!-- Heatmap: 50%, row 3 -->
    <div style="grid-column:1/6; grid-row:3">
      <MusicHeatmap />
    </div>

    <!-- Plays chart: 50%, row 3 -->
    <div style="grid-column:6/11; grid-row:3">
      <MusicPlaysChart />
    </div>

    <!-- Playlists: full width, row 4 -->
    <div style="grid-column:1/11; grid-row:4">
      <MusicPlaylists />
    </div>
  </div>
</main>

<style>
  @media (max-width: 768px) {
    main {
      padding: 14px 14px 0 !important;
    }
    main > div:first-child {
      margin-bottom: 12px;
    }
    main > div:first-child h1 {
      font-size: 1.3rem !important;
    }
    main > div:first-child > div {
      flex-wrap: wrap;
      gap: 8px !important;
    }
    main .grid {
      display: flex !important;
      flex-direction: column !important;
      gap: 10px !important;
    }
    main .grid > div {
      grid-column: unset !important;
      grid-row: unset !important;
      height: auto !important;
      min-height: 130px;
    }
  }
</style>
