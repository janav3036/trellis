<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@100;200;300&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&family=Lora:ital,wght@0,400;1,400&display=swap" rel="stylesheet" />
</svelte:head>

<script>
  import { marked } from 'marked';
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

  marked.setOptions({ breaks: true });

  const dateLabel = new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  });

  // ── NoteRAG mini-chat ─────────────────────────────────────────────────────
  let chatQuery    = '';
  let chatUser     = '';
  let chatResponse = '';
  let chatLoading  = false;
  let chatBodyEl;

  async function askNoteRAG() {
    const text = chatQuery.trim();
    if (!text || chatLoading) return;
    chatQuery    = '';
    chatUser     = text;
    chatResponse = '';
    chatLoading  = true;

    try {
      const res = await fetch('/api/noterag/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, history: [] }),
      });

      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let preamble       = '';
      let sourcesHandled = false;
      let rafPending     = false;

      const flush = () => {
        if (!rafPending) {
          rafPending = true;
          requestAnimationFrame(() => {
            chatResponse = chatResponse;
            if (chatBodyEl) chatBodyEl.scrollTop = chatBodyEl.scrollHeight;
            rafPending = false;
          });
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });

        if (!sourcesHandled) {
          preamble += chunk;
          const nl = preamble.indexOf('\n');
          if (nl !== -1) {
            sourcesHandled = true;
            const rest = preamble.slice(nl + 1);
            if (rest) chatResponse += rest;
            preamble = '';
          }
        } else {
          chatResponse += chunk;
        }
        flush();
      }
    } catch {
      chatResponse = 'Ollama not reachable.';
    }

    chatLoading  = false;
    chatResponse = chatResponse;
  }
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

    <!-- Row 2 · NoteRAG · F1 Race ────────────────────────────────────────── -->
    <div class="cell chat-cell" style="grid-column:1/9; grid-row:2; --i:3">
      <div class="minichat">

        <div class="mc-hdr">
          <div class="mc-hdr-left">
            <span class="mc-dot"></span>
            <span class="mc-label">NoteRAG</span>
          </div>
          <a href="/#/chat" class="mc-open">full chat →</a>
        </div>

        <div class="mc-body" bind:this={chatBodyEl}>
          {#if !chatUser}
            <div class="mc-idle">
              <p class="mc-sub">Ask anything across your logs, journals, and notes.</p>
              <div class="mc-chips">
                {#each [
                  'What did I dream about recently?',
                  'What music have I been listening to?',
                  'Any habits I\'ve been consistent with?',
                  'What movies have I watched lately?',
                ] as chip}
                  <button class="mc-chip" on:click={() => { chatQuery = chip; askNoteRAG(); }}>
                    {chip}
                  </button>
                {/each}
              </div>
            </div>
          {:else}
            <div class="mc-q">{chatUser}</div>
            {#if chatLoading && !chatResponse}
              <div class="mc-dots"><span></span><span></span><span></span></div>
            {:else if chatResponse}
              <div class="mc-a">{@html marked.parse(chatResponse)}</div>
            {/if}
          {/if}
        </div>

        <div class="mc-input-row">
          <input
            bind:value={chatQuery}
            class="mc-input"
            placeholder="Ask anything about your notes…"
            on:keydown={e => e.key === 'Enter' && askNoteRAG()}
          />
          <button
            class="mc-send {chatLoading || !chatQuery.trim() ? 'dim' : ''}"
            on:click={askNoteRAG}
            disabled={chatLoading || !chatQuery.trim()}
          >↑</button>
        </div>

      </div>
    </div>

    <div class="cell" style="grid-column:9/13; grid-row:2/4; --i:4"><HomeF1Race /></div>

    <!-- Row 3 · Code Commits ────────────────────────────────────────────── -->
    <div class="cell" style="grid-column:1/9; grid-row:3; --i:5"><CodeRecentCommits /></div>

    <!-- Rows 4-6 · F1 News + grid ────────────────────────────────────────── -->
    <div class="cell" style="grid-column:1/5; grid-row:4/7; --i:6"><HomeF1News /></div>

    <div class="cell" style="grid-column:5/9; grid-row:4; --i:7"><HomePeople /></div>
    <div class="cell" style="grid-column:9/13; grid-row:4/6; --i:8"><JournalPhotos monthOnly /></div>

    <div class="cell" style="grid-column:5/9; grid-row:5; --i:9"><HomeMovies /></div>

    <div class="cell" style="grid-column:5/10; grid-row:6; --i:10"><SkyApod /></div>
    <div class="cell" style="grid-column:10/13; grid-row:6; --i:11"><MarketCrypto /></div>

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

  /* ── NoteRAG mini-chat ───────────────────────────────────────────────────── */
  .chat-cell {
    background: var(--surface);
    border: 1px solid var(--border);
    position: relative;
  }

  /* subtle gold left accent line */
  .chat-cell::before {
    content: '';
    position: absolute;
    left: 0;
    top: 16%;
    bottom: 16%;
    width: 2px;
    background: linear-gradient(to bottom, transparent, var(--accent), transparent);
    opacity: 0.5;
    border-radius: 0 2px 2px 0;
  }

  .minichat {
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 14px 16px 12px;
    gap: 8px;
  }

  .mc-hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }

  .mc-hdr-left {
    display: flex;
    align-items: center;
    gap: 7px;
  }

  .mc-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    opacity: 0.7;
    flex-shrink: 0;
  }

  .mc-label {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-secondary);
  }

  .mc-open {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.65rem;
    color: var(--text-secondary);
    text-decoration: none;
    opacity: 0.4;
    transition: opacity 0.15s;
    letter-spacing: 0.03em;
  }

  .mc-open:hover { opacity: 0.9; }

  .mc-body {
    flex: 1;
    overflow-y: auto;
    scrollbar-width: none;
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-height: 0;
  }

  .mc-body::-webkit-scrollbar { display: none; }

  .mc-idle {
    display: flex;
    flex-direction: column;
    gap: 9px;
    padding-top: 2px;
  }

  .mc-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.7rem;
    color: var(--text-secondary);
    opacity: 0.45;
    margin: 0;
    letter-spacing: 0.01em;
  }

  .mc-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .mc-chip {
    padding: 4px 11px;
    border-radius: 20px;
    border: 1px solid #252018;
    background: #181410;
    color: #5a5048;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.68rem;
    cursor: pointer;
    transition: border-color 0.15s, color 0.15s, background 0.15s;
    white-space: nowrap;
  }

  .mc-chip:hover {
    border-color: rgba(200, 169, 122, 0.3);
    color: #a09070;
    background: #1c1812;
  }

  .mc-q {
    align-self: flex-end;
    max-width: 80%;
    background: #271f14;
    border: 1px solid #352a1a;
    border-radius: 12px 12px 3px 12px;
    padding: 6px 11px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.75rem;
    color: var(--text-primary);
    line-height: 1.5;
  }

  .mc-dots {
    display: flex;
    gap: 4px;
    padding: 6px 0;
    align-items: center;
  }

  .mc-dots span {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: #352a1a;
    animation: dotPulse 1.3s ease-in-out infinite;
  }

  .mc-dots span:nth-child(2) { animation-delay: 0.18s; }
  .mc-dots span:nth-child(3) { animation-delay: 0.36s; }

  @keyframes dotPulse {
    0%, 80%, 100% { opacity: 0.3; transform: scale(0.75); }
    40%           { opacity: 1;   transform: scale(1.1); }
  }

  .mc-a {
    font-family: 'Lora', serif;
    font-size: 0.74rem;
    color: #c8b89a;
    line-height: 1.65;
  }

  :global(.mc-a p)      { margin: 0 0 0.4em; }
  :global(.mc-a p:last-child) { margin-bottom: 0; }
  :global(.mc-a strong) { color: var(--text-primary); font-weight: 600; }
  :global(.mc-a em)     { color: #b09878; }
  :global(.mc-a code)   {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82em;
    background: #0d0b09;
    color: var(--accent);
    padding: 0.1em 0.3em;
    border-radius: 3px;
  }
  :global(.mc-a ul, .mc-a ol) { margin: 0.3em 0 0.4em 1.2em; }
  :global(.mc-a li) { margin: 0.1em 0; }

  /* Input row */
  .mc-input-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    background: #181410;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 5px 5px 5px 12px;
    transition: border-color 0.15s;
  }

  .mc-input-row:focus-within {
    border-color: rgba(200, 169, 122, 0.25);
  }

  .mc-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    color: var(--text-primary);
    min-width: 0;
  }

  .mc-input::placeholder {
    color: #352a1a;
    font-style: italic;
  }

  .mc-send {
    flex-shrink: 0;
    width: 26px;
    height: 26px;
    border-radius: 6px;
    border: none;
    background: var(--accent);
    color: #13100e;
    font-size: 13px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s, opacity 0.15s;
    line-height: 1;
    padding-bottom: 1px;
  }

  .mc-send.dim { background: #252018; color: #3a3028; cursor: default; }
  .mc-send:not(.dim):hover { background: #d8b98a; }
</style>
