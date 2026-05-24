<script>
  import { onMount } from 'svelte';
  let apod = null;

  onMount(async () => {
    const r = await fetch('/api/sky/apod');
    if (r.ok) apod = await r.json();
  });
</script>

<div class="panel" on:click={() => window.location.hash = '/sky'}>
  {#if apod}
    {#if apod.media_type === 'image'}
      <div class="img-wrap">
        <img src={apod.url} alt={apod.title} class="img" />
        <div class="img-fade" />
      </div>
      <div class="text-col">
        <div class="meta-row">
          <span class="eyebrow">Astronomy · APOD</span>
          <span class="apod-date">{apod.date}</span>
        </div>
        <div class="title">{apod.title}</div>
        <p class="description">{apod.explanation}</p>
      </div>
    {:else}
      <div class="text-col">
        <span class="eyebrow">Astronomy · APOD</span>
        <div class="title">{apod.title}</div>
        <a href={apod.url} target="_blank" rel="noopener noreferrer" class="video-link"
           on:click|stopPropagation>Watch video →</a>
      </div>
    {/if}
  {:else}
    <div class="loading">Loading…</div>
  {/if}
</div>

<style>
  .panel {
    background: var(--surface);
    border-radius: 14px;
    padding: 0;
    height: 100%;
    display: flex;
    gap: 0;
    overflow: hidden;
    cursor: pointer;
    transition: filter 0.2s ease;
    box-sizing: border-box;
  }
  .panel:hover { filter: brightness(1.06); }

  /* Image column */
  .img-wrap {
    position: relative;
    width: 200px;
    flex-shrink: 0;
    align-self: stretch;
  }
  .img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
  /* Right-side gradient fade for blending into text */
  .img-fade {
    position: absolute;
    inset: 0;
    background: linear-gradient(to right, transparent 55%, var(--surface) 100%);
  }

  /* Text column */
  .text-col {
    flex: 1;
    min-width: 0;
    padding: 14px 16px 14px 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    overflow: hidden;
  }

  .meta-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    flex-shrink: 0;
  }
  .eyebrow {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--text-secondary);
  }
  .apod-date {
    font-size: 0.65rem;
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
    flex-shrink: 0;
  }

  .title {
    font-size: 0.92rem;
    font-weight: 600;
    line-height: 1.3;
    flex-shrink: 0;
  }

  .description {
    font-size: 0.75rem;
    color: var(--text-secondary);
    line-height: 1.55;
    margin: 0;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 5;
    -webkit-box-orient: vertical;
  }

  .video-link {
    font-size: 0.8rem;
    color: #6b9e6b;
    text-decoration: none;
    transition: color 0.15s ease;
  }
  .video-link:hover { color: #8abf8a; }

  .loading {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    color: var(--text-secondary);
  }
</style>
