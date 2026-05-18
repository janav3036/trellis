<script>
  import { musicTheme } from '../musicTheme.js';
  export let nowPlaying = null;
</script>

<div
  style="border:1px solid {$musicTheme.border}; background:{$musicTheme.card}"
  class="rounded-xl h-full overflow-hidden relative"
>
  {#if nowPlaying}
    <!-- Full-bleed album art -->
    <img
      src={nowPlaying.cover}
      alt="album art"
      class="absolute inset-0 w-full h-full object-cover"
      style="transition: opacity 0.8s ease"
    />

    <!-- Gradient overlay: transparent top → dark bottom -->
    <div
      class="absolute inset-0"
      style="background: linear-gradient(to top, {$musicTheme.bg}f0 0%, {$musicTheme.bg}88 45%, transparent 75%)"
    ></div>

    <!-- NOW PLAYING badge -->
    <div class="absolute top-4 left-4 flex items-center gap-1.5">
      <span
        class="w-2 h-2 rounded-full"
        style="background:{$musicTheme.accent}; box-shadow: 0 0 6px {$musicTheme.accent}"
      ></span>
      <span class="text-[10px] font-bold uppercase tracking-widest" style="color:{$musicTheme.accent}">Now Playing</span>
    </div>

    <!-- Track info overlaid at bottom -->
    <div class="absolute bottom-0 left-0 right-0 p-5">
      <div class="text-2xl font-black leading-tight mb-2 line-clamp-2" style="color:{$musicTheme.text}">
        {nowPlaying.track}
      </div>
      <div class="text-sm font-semibold" style="color:{$musicTheme.muted}">{nowPlaying.artist}</div>
      <div class="text-xs mt-0.5" style="color:{$musicTheme.muted}; opacity:0.6">{nowPlaying.album}</div>
    </div>
  {:else}
    <div class="h-full flex flex-col items-center justify-center gap-3 p-6">
      <svg viewBox="0 0 24 24" class="w-14 h-14 opacity-20" fill="currentColor" style="color:{$musicTheme.text}">
        <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
      </svg>
      <div class="text-sm font-medium text-center" style="color:{$musicTheme.muted}">Nothing playing</div>
    </div>
  {/if}
</div>
