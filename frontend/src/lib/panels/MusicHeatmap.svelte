<script>
  import { onMount } from 'svelte';
  import { musicTheme } from '../musicTheme.js';

  const DAYS  = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const HOURS = Array.from({ length: 24 }, (_, i) => i);

  let grid   = Array.from({ length: 7 }, () => new Array(24).fill(0));
  let maxVal = 1;

  onMount(async () => {
    const res  = await fetch('/api/spotify/heatmap');
    const data = await res.json();
    const g    = Array.from({ length: 7 }, () => new Array(24).fill(0));
    for (const row of data) g[row.dow][row.hour] = row.plays;
    maxVal = Math.max(1, ...data.map(r => r.plays));
    grid = g;
  });

  function opacity(val) {
    if (val === 0) return 0.07;
    return 0.18 + (val / maxVal) * 0.82;
  }
</script>

<div style="background:{$musicTheme.card}" class="rounded-xl p-4 h-full flex flex-col">
  <div class="text-xs font-semibold uppercase tracking-wider mb-3 shrink-0" style="color:{$musicTheme.muted}">
    Listening Heatmap
  </div>

  <div class="flex-1 flex gap-2 min-h-0">
    <!-- Day labels -->
    <div class="flex flex-col pr-1 shrink-0" style="min-width:2.5rem">
      <div style="height:16px"></div>
      {#each DAYS as d}
        <div class="flex-1 flex items-center justify-end text-[10px]" style="color:{$musicTheme.muted}">{d}</div>
      {/each}
    </div>

    <!-- Grid -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Hour labels -->
      <div class="flex mb-1 shrink-0" style="gap:2px; height:16px">
        {#each HOURS as h}
          <div class="text-[9px] text-center flex-1" style="color:{$musicTheme.muted}">
            {h % 6 === 0 ? h : ''}
          </div>
        {/each}
      </div>
      <!-- Rows -->
      {#each DAYS as _, dow}
        <div class="flex flex-1" style="gap:2px; margin-bottom:2px">
          {#each HOURS as h}
            <div
              class="rounded-sm flex-1"
              style="background:{$musicTheme.accent}; opacity:{opacity(grid[dow][h])}"
              title="{DAYS[dow]} {h}:00 — {grid[dow][h]} plays"
            ></div>
          {/each}
        </div>
      {/each}
    </div>
  </div>
</div>
