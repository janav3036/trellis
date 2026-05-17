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
</script>

<main class="min-h-screen p-5" style="color: var(--text-primary)">
  <div class="flex items-center justify-between mb-4">
    <h1 class="text-2xl font-semibold">Trellis</h1>
    <a href="/#/edit" style="color: var(--text-secondary)"
       class="text-xs transition-colors hover:opacity-80">Edit →</a>
  </div>

  <!--
    12-column bento grid.
    Row heights: 96 | 180 | 140 | 180 | 150 | 200 px
    Each wrapper uses overflow-hidden so panel content never exceeds its row.
  -->
  <div class="grid gap-3" style="
    grid-template-columns: repeat(12, 1fr);
    grid-template-rows: 96px 180px 140px 180px 150px 200px;
  ">

    <!-- ── Row 1: music · weather · calendar (same height via grid row) ── -->
    <div style="grid-column:1/5;  grid-row:1" class="overflow-hidden"><MusicNowPlaying /></div>
    <div style="grid-column:5/9;  grid-row:1" class="overflow-hidden"><WeatherToday /></div>
    <div style="grid-column:9/13; grid-row:1" class="overflow-hidden"><HomeCalendar /></div>

    <!-- ── Row 2: commits (65%) · F1Race (35%) top ── -->
    <div style="grid-column:1/9;  grid-row:2"   class="overflow-hidden"><CodeRecentCommits /></div>
    <div style="grid-column:9/13; grid-row:2/4" class="overflow-hidden"><HomeF1Race /></div>

    <!-- ── Row 3: F1news (30%, spans 3-5) · people (35%) · F1Race continues ── -->
    <div style="grid-column:1/5;  grid-row:3/6" class="overflow-hidden"><HomeF1News /></div>
    <div style="grid-column:5/9;  grid-row:3"   class="overflow-hidden"><HomePeople /></div>

    <!-- ── Rows 4-5: photo · movie/crypto ── -->
    <div style="grid-column:5/9;  grid-row:4/6" class="overflow-hidden"><JournalPhotos monthOnly /></div>
    <div style="grid-column:9/13; grid-row:4"   class="overflow-hidden"><HomeMovies /></div>

    <!-- ── Rows 5-6: crypto ── -->
    <div style="grid-column:9/13; grid-row:5/7" class="overflow-hidden"><MarketCrypto /></div>

    <!-- ── Row 6: APOD (wide) ── -->
    <div style="grid-column:1/9;  grid-row:6"   class="overflow-hidden"><SkyApod /></div>

  </div>
</main>
