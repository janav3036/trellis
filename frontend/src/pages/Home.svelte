<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@100;200;300&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&family=Lora:ital,wght@0,400;1,400&display=swap" rel="stylesheet" />
</svelte:head>

<script>
  import MusicNowPlaying   from '../lib/panels/MusicNowPlaying.svelte';
  import WeatherToday      from '../lib/panels/WeatherToday.svelte';
  import HomeCalendar      from '../lib/panels/HomeCalendar.svelte';
  import CodeRecentCommits from '../lib/panels/CodeRecentCommits.svelte';
  import HomeF1Race        from '../lib/panels/HomeF1Race.svelte';
  import HomePeople        from '../lib/panels/HomePeople.svelte';
  import HomeF1News        from '../lib/panels/HomeF1News.svelte';
  import JournalPhotos     from '../lib/panels/JournalPhotos.svelte';
  import HomeMovies        from '../lib/panels/HomeMovies.svelte';
  import MarketCrypto      from '../lib/panels/MarketCrypto.svelte';
  import SkyApod           from '../lib/panels/SkyApod.svelte';
  import HomeNoteRAG       from '../lib/panels/HomeNoteRAG.svelte';
  import HomeChatStats     from '../lib/panels/HomeChatStats.svelte';

  const dateLabel = new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  });
</script>

<main class="page">

  <!-- ── Header ─────────────────────────────────────────────────────────────── -->
  <header class="hdr">
    <div class="hdr-left">
      <h1 class="brand">Trellis</h1>
      <span class="hdr-rule"></span>
      <p class="date">{dateLabel}</p>
    </div>
    <a href="/#/edit" class="edit-link">Settings →</a>
  </header>

  <!-- ── Grid ───────────────────────────────────────────────────────────────── -->
  <div class="grid">

    <!-- Row 1 · Music · Weather · Calendar ──────────────────────────────── -->
    <div class="cell" style="grid-column:1/5; grid-row:1; --i:0"><MusicNowPlaying /></div>
    <div class="cell" style="grid-column:5/9; grid-row:1; --i:1"><WeatherToday /></div>
    <div class="cell" style="grid-column:9/13; grid-row:1; --i:2"><HomeCalendar /></div>

    <!-- Row 2 · NoteRAG · ChatStats · F1 Race ──────────────────────────── -->
    <div class="cell" style="grid-column:1/5; grid-row:2; --i:3"><HomeNoteRAG /></div>
    <div class="cell" style="grid-column:5/9; grid-row:2; --i:4"><HomeChatStats /></div>

    <div class="cell" style="grid-column:9/13; grid-row:2/4; --i:5"><HomeF1Race /></div>

    <!-- Row 3 · Code Commits ────────────────────────────────────────────── -->
    <div class="cell" style="grid-column:1/9; grid-row:3; --i:6"><CodeRecentCommits /></div>

    <!-- Rows 4-6 · F1 News + grid ────────────────────────────────────────── -->
    <div class="cell" style="grid-column:1/5; grid-row:4/7; --i:7"><HomeF1News /></div>

    <div class="cell" style="grid-column:5/9; grid-row:4; --i:8"><HomePeople /></div>
    <div class="cell" style="grid-column:9/13; grid-row:4/6; --i:9"><JournalPhotos monthOnly /></div>

    <div class="cell" style="grid-column:5/9; grid-row:5; --i:10"><HomeMovies /></div>

    <div class="cell" style="grid-column:5/10; grid-row:6; --i:11"><SkyApod /></div>
    <div class="cell" style="grid-column:10/13; grid-row:6; --i:12"><MarketCrypto /></div>

  </div>
</main>

<style>
  /* ── Page ─────────────────────────────────────────────────────────────────── */
  .page {
    min-height: 100vh;
    padding: 18px 20px 24px;
    color: var(--text-primary);
    animation: pageFade 0.3s ease both;
    position: relative;
  }

  /* Grain overlay */
  .page::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='1'/%3E%3C/svg%3E");
    opacity: 0.022;
    pointer-events: none;
    z-index: 0;
  }

  @keyframes pageFade {
    from { opacity: 0; transform: translateY(5px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* ── Header ──────────────────────────────────────────────────────────────── */
  .hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
    position: relative;
    z-index: 1;
  }

  .hdr-left {
    display: flex;
    align-items: baseline;
    gap: 14px;
  }

  .brand {
    font-family: 'Raleway', sans-serif;
    font-weight: 200;
    font-size: 1.75rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-primary);
    line-height: 1;
    margin: 0;
  }

  .hdr-rule {
    display: block;
    width: 1px;
    height: 14px;
    background: var(--text-secondary);
    opacity: 0.3;
    flex-shrink: 0;
  }

  .date {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 300;
    color: var(--text-secondary);
    letter-spacing: 0.06em;
    margin: 0;
    opacity: 0.7;
  }

  .edit-link {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 400;
    color: var(--text-secondary);
    text-decoration: none;
    letter-spacing: 0.04em;
    opacity: 0.5;
    transition: opacity 0.2s;
  }

  .edit-link:hover { opacity: 1; }

  /* ── Grid ────────────────────────────────────────────────────────────────── */
  .grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    grid-template-rows: 90px 210px 148px 170px 158px 200px;
    gap: 9px;
    position: relative;
    z-index: 1;
  }

  .cell {
    overflow: hidden;
    border-radius: 12px;
    animation: cellUp 0.38s ease both;
    animation-delay: calc(var(--i, 0) * 35ms);
    transition: box-shadow 0.2s ease;
  }

  .cell:hover {
    box-shadow: 0 0 0 1px rgba(200, 169, 122, 0.1);
  }

  @keyframes cellUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* ── Mobile ──────────────────────────────────────────────────────────────── */
  @media (max-width: 768px) {
    .page {
      padding: 16px 14px 0;
    }

    .hdr {
      margin-bottom: 0;
      padding-bottom: 11px;
      border-bottom: 1px solid rgba(255,255,255,0.05);
      margin-bottom: 12px;
    }

    .brand {
      font-size: 1.15rem;
      letter-spacing: 0.24em;
    }

    .date {
      font-family: 'DM Mono', ui-monospace, monospace;
      font-size: 0.58rem;
      letter-spacing: 0.03em;
      text-transform: uppercase;
    }

    .hdr-rule {
      display: none;
    }

    .edit-link {
      font-family: 'DM Mono', ui-monospace, monospace;
      font-size: 0.58rem;
      letter-spacing: 0.03em;
    }

    .grid {
      display: flex !important;
      flex-direction: column !important;
      gap: 8px !important;
      grid-template-rows: unset !important;
    }

    .cell {
      width: 100% !important;
      height: auto !important;
      min-height: 110px;
      grid-column: unset !important;
      grid-row: unset !important;
    }
  }

</style>
