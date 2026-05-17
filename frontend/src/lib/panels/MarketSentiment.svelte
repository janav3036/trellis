<script>
  import { onMount } from 'svelte';
  let fearScore = null, vix = null;

  $: orbColor = fearScore === null
    ? '#333'
    : fearScore > 50
      ? `rgba(200,129,58,${0.5+(fearScore-50)/100})`
      : `rgba(77,171,247,${0.5+(50-fearScore)/100})`;

  $: orbGlow = fearScore === null
    ? 'none'
    : fearScore > 50
      ? `0 0 ${25+fearScore*0.4}px rgba(200,129,58,0.8),0 0 ${55+fearScore}px rgba(200,129,58,0.3)`
      : `0 0 ${25+(100-fearScore)*0.4}px rgba(77,171,247,0.8),0 0 ${55+(100-fearScore)}px rgba(77,171,247,0.3)`;

  $: label = fearScore === null ? '—'
    : fearScore > 80 ? 'Extreme Greed'
    : fearScore > 60 ? 'Greed'
    : fearScore > 40 ? 'Neutral'
    : fearScore > 20 ? 'Fear'
    : 'Extreme Fear';

  onMount(async () => {
    const data = await (await fetch('/api/market/fear-greed')).json();
    fearScore = data.score;
    vix = data.vix;
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 flex flex-col items-center justify-center gap-4 min-w-[180px]">
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider">Sentiment</div>
  {#if fearScore !== null}
    <div class="w-24 h-24 rounded-full transition-all duration-1000"
      style="background:{orbColor};box-shadow:{orbGlow}">
    </div>
    <div class="text-center">
      <div class="text-sm font-medium">{label}</div>
      <div class="text-xs text-[#9a9080] mt-0.5">VIX {vix}</div>
    </div>
  {:else}
    <div class="w-24 h-24 rounded-full bg-[#2a2520] animate-pulse"></div>
  {/if}
</div>
