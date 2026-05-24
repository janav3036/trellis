<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@100;200;300&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap" rel="stylesheet" />
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

  const dateLabel = new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  });
</script>

<main class="page">
  <header class="hdr">
    <div>
      <h1 class="brand">Trellis</h1>
      <p class="date">{dateLabel}</p>
    </div>
    <a href="/#/edit" class="edit-link">Settings →</a>
  </header>

  <!--
    12-column bento grid.
    Row heights: 96 | 180 | 140 | 180 | 150 | 200 px
  -->
  <div class="grid" style="
    grid-template-columns: repeat(12, 1fr);
    grid-template-rows: 96px 180px 140px 180px 150px 200px;
  ">
    <!-- Row 1 -->
    <div style="grid-column:1/5;  grid-row:1" class="cell" style:--i={0}><MusicNowPlaying /></div>
    <div style="grid-column:5/9;  grid-row:1" class="cell" style:--i={1}><WeatherToday /></div>
    <div style="grid-column:9/13; grid-row:1" class="cell" style:--i={2}><HomeCalendar /></div>

    <!-- Row 2 -->
    <div style="grid-column:1/9;  grid-row:2"   class="cell" style:--i={3}><CodeRecentCommits /></div>
    <div style="grid-column:9/13; grid-row:2/4" class="cell" style:--i={4}><HomeF1Race /></div>

    <!-- Row 3 -->
    <div style="grid-column:1/5;  grid-row:3/6" class="cell" style:--i={5}><HomeF1News /></div>
    <div style="grid-column:5/9;  grid-row:3"   class="cell" style:--i={6}><HomePeople /></div>

    <!-- Rows 4-5 -->
    <div style="grid-column:5/9;  grid-row:4/6" class="cell" style:--i={7}><JournalPhotos monthOnly /></div>
    <div style="grid-column:9/13; grid-row:4"   class="cell" style:--i={8}><HomeMovies /></div>

    <!-- Row 5-6 -->
    <div style="grid-column:9/13; grid-row:5/7" class="cell" style:--i={9}><MarketCrypto /></div>

    <!-- Row 6 -->
    <div style="grid-column:1/9;  grid-row:6"   class="cell" style:--i={10}><SkyApod /></div>
  </div>
</main>

<style>
  .page {
    min-height: 100vh;
    padding: 20px;
    color: var(--text-primary);
    animation: pageFade 0.35s ease both;
  }
  @keyframes pageFade {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  /* ── Header ── */
  .hdr {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-bottom: 18px;
  }
  .brand {
    font-family: 'Raleway', sans-serif;
    font-weight: 200;
    font-size: 1.9rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-primary);
    line-height: 1;
    margin: 0;
  }
  .date {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.7rem;
    font-weight: 300;
    color: var(--text-secondary);
    letter-spacing: 0.05em;
    margin: 4px 0 0;
  }
  .edit-link {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.72rem;
    font-weight: 400;
    color: var(--text-secondary);
    text-decoration: none;
    letter-spacing: 0.03em;
    transition: color 0.2s ease;
    padding-bottom: 2px;
  }
  .edit-link:hover { color: var(--text-primary); }

  /* ── Grid ── */
  .grid {
    display: grid;
    gap: 10px;
  }

  /* Staggered fade-up for each cell */
  .cell {
    overflow: hidden;
    animation: cellUp 0.4s ease both;
    animation-delay: calc(var(--i, 0) * 40ms);
  }
  @keyframes cellUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
  }
</style>
