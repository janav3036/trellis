<script>
  import { onMount, onDestroy } from 'svelte';
  let np = null;
  let timer;

  async function poll() {
    const r = await fetch('/api/now-playing');
    np = await r.json();
  }

  onMount(() => { poll(); timer = setInterval(poll, 10000); });
  onDestroy(() => clearInterval(timer));

  $: pct = np ? Math.round((np.progress_ms / np.duration_ms) * 100) : 0;
</script>

<div class="panel" on:click={() => window.location.hash = '/music'}>
  {#if np}
    <div class="row">
      {#if np.cover}
        <div class="art-frame">
          <img src={np.cover} alt="album" class="art" />
        </div>
      {/if}
      <div class="info">
        <div class="label-row">
          <span class="live-dot" />
          <span class="eyebrow">Now Playing</span>
        </div>
        <div class="track">{np.track}</div>
        <div class="artist">{np.artist}</div>
      </div>
    </div>
    <div class="progress-track">
      <div class="progress-fill" style="width:{pct}%" />
    </div>
  {:else}
    <div class="idle">
      <span class="eyebrow">Music</span>
      <span class="idle-text">Nothing playing</span>
    </div>
  {/if}
</div>

<style>
  .panel {
    background: var(--surface);
    border-radius: 14px;
    padding: 12px 14px;
    height: 100%;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 10px;
    cursor: pointer;
    transition: filter 0.2s ease;
  }
  .panel:hover { filter: brightness(1.06); }

  .row { display: flex; align-items: center; gap: 12px; }

  .art-frame {
    width: 56px;
    height: 56px;
    border-radius: 8px;
    overflow: hidden;
    flex-shrink: 0;
    box-shadow:
      0 4px 14px rgba(0,0,0,0.4),
      0 0 0 1px rgba(255,255,255,0.06);
  }
  .art { width: 100%; height: 100%; object-fit: cover; display: block; }

  .info { min-width: 0; flex: 1; }

  .label-row {
    display: flex;
    align-items: center;
    gap: 5px;
    margin-bottom: 3px;
  }
  .live-dot {
    width: 5px; height: 5px; border-radius: 50%;
    background: #6b9e6b;
    flex-shrink: 0;
    animation: livepulse 2.2s ease-in-out infinite;
  }
  @keyframes livepulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.35; }
  }

  .eyebrow {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--text-secondary);
  }
  .track {
    font-size: 0.875rem;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.25;
  }
  .artist {
    font-size: 0.75rem;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 1px;
  }

  /* Progress bar */
  .progress-track {
    height: 2px;
    background: var(--bg);
    border-radius: 2px;
    overflow: hidden;
    flex-shrink: 0;
  }
  .progress-fill {
    height: 100%;
    background: var(--accent);
    border-radius: 2px;
    transition: width 1s linear;
  }

  /* Idle state */
  .idle { display: flex; flex-direction: column; gap: 5px; }
  .idle-text { font-size: 0.85rem; color: var(--text-secondary); }
</style>
