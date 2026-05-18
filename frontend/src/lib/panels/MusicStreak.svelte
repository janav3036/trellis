<script>
  import { onMount } from 'svelte';
  import { musicTheme } from '../musicTheme.js';

  let streak = 0;
  let longest = 0;

  onMount(async () => {
    const res = await fetch('/api/spotify/streak');
    const data = await res.json();
    streak = data.streak;
    longest = data.longest;
  });
</script>

<div style="background:{$musicTheme.card}" class="rounded-xl p-4 h-full flex flex-col justify-center">
  <div class="text-xs font-semibold uppercase tracking-wider mb-4" style="color:{$musicTheme.muted}">
    Listening Streak
  </div>
  <div class="flex items-end gap-8">
    <div>
      <div class="text-5xl font-bold tabular-nums leading-none" style="color:{$musicTheme.accent}">{streak}</div>
      <div class="text-xs mt-1.5" style="color:{$musicTheme.muted}">day{streak !== 1 ? 's' : ''} in a row</div>
    </div>
    <div class="mb-0.5">
      <div class="text-2xl font-semibold tabular-nums leading-none" style="color:{$musicTheme.text}">{longest}</div>
      <div class="text-xs mt-1.5" style="color:{$musicTheme.muted}">longest</div>
    </div>
  </div>
</div>
