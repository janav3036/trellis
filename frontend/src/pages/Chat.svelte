<script>
  import { onMount, tick } from 'svelte';
  import { marked } from 'marked';
  import hljs from 'highlight.js';

  marked.setOptions({
    highlight(code, lang) {
      const language = hljs.getLanguage(lang) ? lang : 'plaintext';
      return hljs.highlight(code, { language }).value;
    },
    langPrefix: 'hljs language-',
    breaks: true,
  });

  function renderMarkdown(text) {
    return marked.parse(text || '');
  }

  // ── Source maps ──────────────────────────────────────────────────────────────
  const SOURCE_ICONS = {
    spotify: '♪', github: '⌥', dreams: '◎', movies: '▶',
    people:  '◉', letters: '✦', quotes: '❝', habits: '◇',
    gym:     '△', calendar: '□', weather: '◌', photos: '⬡',
  };

  const SOURCE_ROUTES = {
    spotify: '/music', github: '/code', dreams: '/journal', movies: '/life',
    people:  '/life',  letters: '/journal', quotes: '/journal', habits: '/journal',
    gym:     '/life',  calendar: '/life',   weather: '/weather', photos: '/journal',
  };

  function sourceIcon(s) { return SOURCE_ICONS[s] || '·'; }
  function sourceRoute(s) { return SOURCE_ROUTES[s] || '/'; }

  // ── State ────────────────────────────────────────────────────────────────────
  let sessions     = [];
  let activeId     = null;
  let messages     = [];
  let query        = '';
  let loading      = false;
  let totalChunks  = 0;
  let indexing     = false;
  let indexMsg     = '';
  let msgsEl;
  let inputEl;
  let hoveredId    = null;
  let editingId    = null;
  let editTitle    = '';
  let editEl;

  // Settings drawer
  let showSettings     = false;
  let settingsTab      = 'profile';
  let profile          = '';
  let customPrompt     = '';
  let profileDirty     = false;
  let promptDirty      = false;
  let generatingProfile = false;
  let savingPrompt     = false;

  // ── Status ───────────────────────────────────────────────────────────────────
  async function loadStatus() {
    try {
      const d = await fetch('/api/noterag/status').then(r => r.json());
      totalChunks = d.total_chunks;
    } catch { totalChunks = 0; }
  }

  async function runIndex() {
    indexing = true;
    indexMsg = '';
    try {
      const d = await fetch('/api/noterag/index', { method: 'POST' }).then(r => r.json());
      indexMsg = `+${d.indexed} indexed`;
      await loadStatus();
    } catch { indexMsg = 'failed'; }
    indexing = false;
    setTimeout(() => indexMsg = '', 3500);
  }

  // ── Sessions ─────────────────────────────────────────────────────────────────
  async function loadSessions() {
    try {
      sessions = await fetch('/api/noterag/sessions').then(r => r.json());
    } catch { sessions = []; }
  }

  async function newChat() {
    try {
      const s = await fetch('/api/noterag/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Chat' }),
      }).then(r => r.json());
      sessions = [s, ...sessions];
      activeId = s.id;
      messages = [];
      await tick();
      inputEl?.focus();
    } catch {}
  }

  async function loadSession(id) {
    if (id === activeId) return;
    try {
      const data = await fetch(`/api/noterag/sessions/${id}`).then(r => r.json());
      activeId = id;
      messages = data.messages || [];
      await tick();
      scrollToBottom();
      inputEl?.focus();
    } catch {}
  }

  async function deleteSession(id, e) {
    e.stopPropagation();
    await fetch(`/api/noterag/sessions/${id}`, { method: 'DELETE' });
    sessions = sessions.filter(s => s.id !== id);
    if (activeId === id) {
      if (sessions.length > 0) {
        await loadSession(sessions[0].id);
      } else {
        await newChat();
      }
    }
  }

  async function autoTitle(sessionId, firstUserText) {
    const title = firstUserText.slice(0, 50).trim();
    await fetch(`/api/noterag/sessions/${sessionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    sessions = sessions.map(s => s.id === sessionId ? { ...s, title } : s);
  }

  async function startRename(s, e) {
    e.stopPropagation();
    editingId = s.id;
    editTitle = s.title;
    await tick();
    editEl?.select();
  }

  async function commitRename(id) {
    const title = editTitle.trim();
    editingId = null;
    if (!title) return;
    await fetch(`/api/noterag/sessions/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    sessions = sessions.map(s => s.id === id ? { ...s, title } : s);
  }

  function cancelRename() { editingId = null; }

  async function persistMessages(sessionId, userMsg, assistantMsg) {
    await fetch(`/api/noterag/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify([
        { role: 'user',      text: userMsg.text,      sources: [] },
        { role: 'assistant', text: assistantMsg.text, sources: assistantMsg.sources || [] },
      ]),
    });
  }

  // ── Settings ─────────────────────────────────────────────────────────────────
  async function loadSettings() {
    const [pRes, cRes] = await Promise.all([
      fetch('/api/noterag/profile'),
      fetch('/api/noterag/custom-prompt'),
    ]);
    profile      = (await pRes.json()).profile       || '';
    customPrompt = (await cRes.json()).custom_prompt || '';
  }

  async function saveProfile() {
    await fetch('/api/noterag/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile }),
    });
    profileDirty = false;
  }

  async function generateProfile() {
    generatingProfile = true;
    try {
      const d = await fetch('/api/noterag/profile/generate', { method: 'POST' }).then(r => r.json());
      profile      = d.profile || '';
      profileDirty = false;
    } catch {}
    generatingProfile = false;
  }

  async function saveCustomPrompt() {
    savingPrompt = true;
    await fetch('/api/noterag/custom-prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ custom_prompt: customPrompt }),
    });
    promptDirty  = false;
    savingPrompt = false;
  }

  // ── Chat ─────────────────────────────────────────────────────────────────────
  const UPDATE_CONTEXT_RE = /^(update context|\/update|update my profile|remember this)\b/i;

  async function sendMessage() {
    const text = query.trim();
    if (!text || loading || !activeId) return;
    query = '';

    // Context update command — regenerate profile from events
    if (UPDATE_CONTEXT_RE.test(text)) {
      await handleContextUpdate(text);
      return;
    }

    const isFirst = messages.length === 0;
    const history = messages.slice(-10).map(m => ({ role: m.role, text: m.text }));

    const userMsg = { role: 'user', text };
    messages = [...messages, userMsg];
    loading  = true;

    const assistantMsg = { role: 'assistant', text: '', sources: [] };
    messages = [...messages, assistantMsg];
    const idx = messages.length - 1;

    await tick();
    scrollToBottom();

    try {
      const res = await fetch('/api/noterag/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, history }),
      });

      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let preamble       = '';
      let sourcesHandled = false;
      // Batch DOM updates to one per animation frame — prevents per-token flicker
      let rafPending = false;
      const scheduleRender = () => {
        if (!rafPending) {
          rafPending = true;
          requestAnimationFrame(() => {
            messages = messages;
            scrollToBottom();
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
            const firstLine = preamble.slice(0, nl);
            const rest      = preamble.slice(nl + 1);
            if (firstLine.startsWith('SOURCES:')) {
              try {
                messages[idx].sources = JSON.parse(firstLine.slice(8));
              } catch {}
            }
            sourcesHandled = true;
            if (rest) messages[idx].text += rest;
            preamble = '';
          }
        } else {
          // Mutate in place — avoids object churn that triggers key-based DOM teardown
          messages[idx].text += chunk;
        }

        scheduleRender();
      }
    } catch {
      messages[idx] = { ...messages[idx], text: 'Something went wrong. Is Ollama running?' };
      messages = messages;
    }

    loading = false;

    await persistMessages(activeId, userMsg, messages[idx]);
    if (isFirst) await autoTitle(activeId, text);

    await tick();
    inputEl?.focus();
  }

  async function handleContextUpdate(text) {
    const userMsg = { role: 'user', text };
    messages = [...messages, userMsg];
    loading  = true;
    const assistantMsg = { role: 'assistant', text: '', sources: [] };
    messages = [...messages, assistantMsg];
    const idx = messages.length - 1;
    await tick();
    scrollToBottom();

    try {
      const d = await fetch('/api/noterag/profile/generate', { method: 'POST' }).then(r => r.json());
      profile = d.profile || '';
      messages[idx] = {
        ...messages[idx],
        text: `I've updated my understanding of you based on your recent logs.\n\n${profile}`,
      };
    } catch {
      messages[idx] = { ...messages[idx], text: 'Failed to update context. Try again.' };
    }

    messages = messages;
    loading  = false;
    const isFirst = messages.filter(m => m.role === 'user').length === 1;
    await persistMessages(activeId, userMsg, messages[idx]);
    if (isFirst) await autoTitle(activeId, text);
    await tick();
    inputEl?.focus();
  }

  function scrollToBottom() {
    if (msgsEl) msgsEl.scrollTop = msgsEl.scrollHeight;
  }

  function fmtDate(str) {
    if (!str) return '';
    const d = new Date(str), now = new Date(), diff = now - d;
    if (diff < 86400000)  return 'today';
    if (diff < 172800000) return 'yesterday';
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }

  onMount(async () => {
    await Promise.all([loadSessions(), loadStatus(), loadSettings()]);
    if (sessions.length > 0) {
      await loadSession(sessions[0].id);
    } else {
      await newChat();
    }
  });
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400&family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet">
</svelte:head>

<div class="shell">

  <!-- ═══ SIDEBAR ══════════════════════════════════════════════════════════════ -->
  <aside class="sidebar">
    <div class="sidebar-top">
      <button class="new-btn" on:click={newChat}>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
          <line x1="6" y1="1" x2="6" y2="11"/><line x1="1" y1="6" x2="11" y2="6"/>
        </svg>
        New chat
      </button>
    </div>

    <div class="session-scroll">
      {#each sessions as s, i (s.id)}
        <button
          class="session-row {s.id === activeId ? 'is-active' : ''}"
          style="animation-delay:{i * 25}ms"
          on:click={() => loadSession(s.id)}
          on:dblclick={e => startRename(s, e)}
          on:mouseenter={() => hoveredId = s.id}
          on:mouseleave={() => hoveredId = null}
        >
          {#if editingId === s.id}
            <input
              bind:this={editEl}
              bind:value={editTitle}
              class="s-rename-input"
              on:keydown={e => {
                if (e.key === 'Enter')  { e.preventDefault(); commitRename(s.id); }
                if (e.key === 'Escape') { e.preventDefault(); cancelRename(); }
              }}
              on:blur={() => commitRename(s.id)}
              on:click={e => e.stopPropagation()}
            />
          {:else}
            <span class="s-title">{s.title}</span>
            <span class="s-date">{fmtDate(s.updated_at)}</span>
            {#if hoveredId === s.id || s.id === activeId}
              <span
                class="s-del"
                role="button"
                tabindex="0"
                title="Delete"
                on:click={e => deleteSession(s.id, e)}
                on:keydown={e => e.key === 'Enter' && deleteSession(s.id, e)}
              >×</span>
            {/if}
          {/if}
        </button>
      {/each}

      {#if sessions.length === 0}
        <p class="no-sessions">No conversations yet</p>
      {/if}
    </div>

    <div class="sidebar-foot">
      <button class="gear-btn" on:click={() => { showSettings = true; settingsTab = 'profile'; }}>
        <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor" opacity=".7">
          <path d="M9.405 1.05c-.413-1.4-2.397-1.4-2.81 0l-.1.34a1.464 1.464 0 0 1-2.105.872l-.31-.17c-1.283-.698-2.686.705-1.987 1.987l.169.311c.446.82.023 1.841-.872 2.105l-.34.1c-1.4.413-1.4 2.397 0 2.81l.34.1a1.464 1.464 0 0 1 .872 2.105l-.17.31c-.698 1.283.705 2.686 1.987 1.987l.311-.169a1.464 1.464 0 0 1 2.105.872l.1.34c.413 1.4 2.397 1.4 2.81 0l.1-.34a1.464 1.464 0 0 1 2.105-.872l.31.17c1.283.698 2.686-.705 1.987-1.987l-.169-.311a1.464 1.464 0 0 1 .872-2.105l.34-.1c1.4-.413 1.4-2.397 0-2.81l-.34-.1a1.464 1.464 0 0 1-.872-2.105l.17-.31c.698-1.283-.705-2.686-1.987-1.987l-.311.169a1.464 1.464 0 0 1-2.105-.872l-.1-.34zM8 10.93a2.929 2.929 0 1 1 0-5.86 2.929 2.929 0 0 1 0 5.858z"/>
        </svg>
        Settings
      </button>
    </div>
  </aside>

  <!-- ═══ MAIN CHAT ══════════════════════════════════════════════════════════════ -->
  <div class="chat-col">

    <!-- Header -->
    <header class="chat-hdr">
      <div class="hdr-left">
        <span class="hdr-name">NoteRAG</span>
        <span class="hdr-pill">
          {totalChunks > 0 ? `${totalChunks.toLocaleString()} chunks` : 'not indexed'}
        </span>
        {#if indexMsg}
          <span class="hdr-feedback">{indexMsg}</span>
        {/if}
      </div>
      <button class="reindex-btn" on:click={runIndex} disabled={indexing}>
        {indexing ? 'indexing…' : 'reindex'}
      </button>
    </header>

    <!-- Messages -->
    <div bind:this={msgsEl} class="msgs">
      {#if messages.length === 0}
        <div class="empty">
          <div class="empty-mark">◎</div>
          <p class="empty-heading">What's on your mind?</p>
          <p class="empty-sub">Ask about your dreams, music, movies, habits — anything in your logs.</p>
          <div class="hints">
            {#each ['What did I dream about last month?', 'Which movies have I watched this year?', 'Update context'] as h}
              <button class="hint" on:click={() => { query = h; sendMessage(); }}>{h}</button>
            {/each}
          </div>
        </div>
      {/if}

      {#each messages as msg, i (i)}
        <div class="row {msg.role}">
          {#if msg.role === 'user'}
            <div class="bubble-user">{msg.text}</div>
          {:else}
            <div class="bubble-ai">
              {#if msg.text}
                <div class="prose-chat">{@html renderMarkdown(msg.text)}</div>
              {:else}
                <div class="thinking"><span></span><span></span><span></span></div>
              {/if}
              {#if msg.sources && msg.sources.length > 0}
                <div class="cites">
                  {#each msg.sources as src}
                    <a href={sourceRoute(src.source)} class="cite">
                      <span class="cite-icon">{sourceIcon(src.source)}</span>
                      <span class="cite-src">{src.source}</span>
                      {#if src.date}<span class="cite-dt">{src.date}</span>{/if}
                    </a>
                  {/each}
                </div>
              {/if}
            </div>
          {/if}
        </div>
      {/each}
    </div>

    <!-- Input -->
    <div class="input-dock">
      <div class="input-wrap">
        <textarea
          bind:this={inputEl}
          bind:value={query}
          placeholder="Ask anything about your notes…"
          rows="1"
          on:keydown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
          on:input={e => {
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
          }}
        ></textarea>
        <button
          class="send {loading || !query.trim() ? 'off' : ''}"
          on:click={sendMessage}
          disabled={loading || !query.trim()}
        >
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <line x1="7" y1="13" x2="7" y2="1"/><polyline points="2,6 7,1 12,6"/>
          </svg>
        </button>
      </div>
      <p class="input-hint">Enter · send &nbsp;·&nbsp; Shift+Enter · newline</p>
    </div>
  </div>

  <!-- ═══ SETTINGS DRAWER ═══════════════════════════════════════════════════════ -->
  {#if showSettings}
    <div class="backdrop" on:click={() => showSettings = false} role="presentation"></div>
    <div class="drawer">
      <div class="drawer-hdr">
        <h2 class="drawer-title">Settings</h2>
        <button class="close" on:click={() => showSettings = false}>×</button>
      </div>

      <div class="dtabs">
        <button class="dtab {settingsTab === 'profile' ? 'on' : ''}" on:click={() => settingsTab = 'profile'}>Profile</button>
        <button class="dtab {settingsTab === 'context' ? 'on' : ''}" on:click={() => settingsTab = 'context'}>Extra context</button>
      </div>

      {#if settingsTab === 'profile'}
        <div class="dpane">
          <p class="dlabel">Auto-generated from your logs. You can also edit it manually or say <em>"update context"</em> in chat to regenerate.</p>
          <textarea
            class="dtextarea"
            bind:value={profile}
            on:input={() => profileDirty = true}
            placeholder="Your profile will appear here once generated, or write your own…"
            rows="12"
          ></textarea>
          <div class="dactions">
            {#if profileDirty}
              <button class="dact primary" on:click={saveProfile}>Save</button>
            {/if}
            <button class="dact" on:click={generateProfile} disabled={generatingProfile}>
              {generatingProfile ? 'Generating… (~30s)' : 'Regenerate from logs'}
            </button>
          </div>
        </div>
      {:else}
        <div class="dpane">
          <p class="dlabel">Things you always want the AI to know — injected into every conversation alongside your profile.</p>
          <textarea
            class="dtextarea"
            bind:value={customPrompt}
            on:input={() => promptDirty = true}
            placeholder="e.g. I prefer concise answers. Always suggest next steps. I'm a developer who likes technical depth."
            rows="10"
          ></textarea>
          <div class="dactions">
            <button class="dact primary" on:click={saveCustomPrompt} disabled={savingPrompt || !promptDirty}>
              {savingPrompt ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}

</div>

<style>
  /* ── Reset & shell ──────────────────────────────────────────────────────────── */
  .shell {
    display: flex;
    height: 100vh;
    background: #13100e;
    color: #e8e0d5;
    font-family: 'Lora', Georgia, serif;
    position: relative;
    overflow: hidden;
  }

  /* ── Sidebar ────────────────────────────────────────────────────────────────── */
  .sidebar {
    width: 232px;
    flex-shrink: 0;
    background: #0f0d0b;
    border-right: 1px solid #1c1814;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .sidebar-top {
    padding: 14px 10px 10px;
    border-bottom: 1px solid #1c1814;
  }

  .new-btn {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 7px;
    border: 1px solid #252018;
    background: transparent;
    color: #a09070;
    font-family: 'Lora', serif;
    font-size: 12.5px;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
  }

  .new-btn:hover {
    background: #1a1610;
    border-color: #c8a97a33;
    color: #c8b89a;
  }

  .new-btn svg { color: #c8a97a; flex-shrink: 0; }

  .session-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 6px 6px;
    scrollbar-width: none;
  }

  .session-scroll::-webkit-scrollbar { display: none; }

  .session-row {
    position: relative;
    display: block;
    width: 100%;
    text-align: left;
    padding: 8px 10px;
    border-radius: 6px;
    border: 1px solid transparent;
    background: transparent;
    cursor: pointer;
    margin-bottom: 1px;
    opacity: 0;
    animation: fadeUp 0.22s ease forwards;
    transition: background 0.12s, border-color 0.12s;
  }

  .session-row:hover {
    background: #181410;
    border-color: #252018;
  }

  .session-row.is-active {
    background: #1c1814;
    border-color: #252018;
  }

  .session-row.is-active::before {
    content: '';
    position: absolute;
    left: 0;
    top: 22%;
    bottom: 22%;
    width: 2px;
    background: #c8a97a;
    border-radius: 0 2px 2px 0;
  }

  .s-title {
    display: block;
    font-size: 12px;
    color: #9a8878;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    padding-right: 18px;
    line-height: 1.45;
    transition: color 0.1s;
  }

  .session-row.is-active .s-title { color: #d8c8b8; }
  .session-row:hover .s-title     { color: #b8a898; }

  .s-date {
    display: block;
    font-size: 10px;
    color: #3e3428;
    margin-top: 2px;
  }

  .s-rename-input {
    display: block;
    width: 100%;
    background: #252018;
    border: 1px solid #c8a97a55;
    border-radius: 4px;
    padding: 2px 6px;
    color: #d8c8b0;
    font-family: 'Lora', serif;
    font-size: 12px;
    outline: none;
  }

  .s-del {
    position: absolute;
    right: 7px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 15px;
    line-height: 1;
    color: #4e4438;
    padding: 1px 3px;
    border-radius: 3px;
    cursor: pointer;
    transition: color 0.1s, background 0.1s;
    user-select: none;
  }

  .s-del:hover { color: #c87a7a; background: #281818; }

  .no-sessions {
    text-align: center;
    color: #3a3028;
    font-size: 12px;
    padding: 28px 12px;
    font-style: italic;
  }

  .sidebar-foot {
    padding: 10px;
    border-top: 1px solid #1c1814;
  }

  .gear-btn {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 7px 10px;
    background: none;
    border: none;
    color: #4a4038;
    font-family: 'Lora', serif;
    font-size: 12px;
    cursor: pointer;
    border-radius: 6px;
    transition: color 0.15s, background 0.15s;
  }

  .gear-btn:hover { color: #8a7868; background: #181410; }

  /* ── Chat column ────────────────────────────────────────────────────────────── */
  .chat-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-width: 0;
  }

  /* Header */
  .chat-hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 13px 22px;
    border-bottom: 1px solid #1c1814;
    flex-shrink: 0;
  }

  .hdr-left { display: flex; align-items: center; gap: 10px; }

  .hdr-name {
    font-family: 'DM Serif Display', 'Lora', serif;
    font-size: 15px;
    color: #d8c8b0;
    letter-spacing: 0.03em;
  }

  .hdr-pill {
    font-size: 10.5px;
    color: #3e3428;
    background: #181410;
    padding: 2px 9px;
    border-radius: 20px;
    border: 1px solid #252018;
  }

  .hdr-feedback {
    font-size: 11px;
    color: #8abf8a;
    font-style: italic;
    animation: fadeIn 0.2s ease;
  }

  .reindex-btn {
    font-size: 11px;
    padding: 5px 13px;
    border-radius: 6px;
    border: 1px solid #252018;
    background: #181410;
    color: #5a5048;
    cursor: pointer;
    font-family: 'Lora', serif;
    transition: color 0.15s, border-color 0.15s;
  }

  .reindex-btn:not(:disabled):hover { color: #c8a97a; border-color: #c8a97a44; }
  .reindex-btn:disabled { opacity: 0.45; cursor: default; }

  /* Messages */
  .msgs {
    flex: 1;
    overflow-y: auto;
    padding: 28px 0 12px;
    scrollbar-width: none;
    display: flex;
    flex-direction: column;
  }

  .msgs::-webkit-scrollbar { display: none; }

  /* Empty state */
  .empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 48px 32px;
    text-align: center;
    gap: 0;
  }

  .empty-mark {
    font-size: 32px;
    color: #252018;
    margin-bottom: 18px;
  }

  .empty-heading {
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    color: #3e3428;
    margin: 0 0 10px;
    font-weight: 400;
  }

  .empty-sub {
    font-size: 13px;
    color: #2e2820;
    margin: 0 0 26px;
    font-style: italic;
    max-width: 300px;
    line-height: 1.7;
  }

  .hints {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    max-width: 460px;
  }

  .hint {
    padding: 7px 15px;
    border-radius: 20px;
    border: 1px solid #222018;
    background: #181410;
    color: #4a4038;
    font-size: 12px;
    cursor: pointer;
    font-family: 'Lora', serif;
    font-style: italic;
    transition: all 0.15s;
  }

  .hint:hover { border-color: #c8a97a33; color: #8a7868; background: #1c1814; }

  /* Rows */
  .row {
    padding: 5px 22px;
    display: flex;
    animation: msgIn 0.18s ease;
  }

  .row.user      { justify-content: flex-end; }
  .row.assistant { justify-content: flex-start; }

  .bubble-user {
    max-width: 58%;
    padding: 10px 16px;
    background: #271f14;
    border: 1px solid #352a1a;
    border-radius: 17px 17px 4px 17px;
    font-size: 14px;
    line-height: 1.65;
    color: #d8c8b0;
    white-space: pre-wrap;
  }

  .bubble-ai {
    max-width: 76%;
  }

  /* Thinking dots */
  .thinking {
    display: flex;
    gap: 5px;
    padding: 14px 2px 8px;
    align-items: center;
  }

  .thinking span {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #352a1a;
    animation: pulseDot 1.3s ease-in-out infinite;
  }

  .thinking span:nth-child(2) { animation-delay: 0.18s; }
  .thinking span:nth-child(3) { animation-delay: 0.36s; }

  /* Citations */
  .cites {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-top: 10px;
  }

  .cite {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 9px;
    border-radius: 5px;
    border: 1px solid #222018;
    background: #181410;
    text-decoration: none;
    font-size: 10px;
    transition: border-color 0.15s;
  }

  .cite:hover { border-color: #c8a97a33; }

  .cite-icon { color: #c8a97a; font-style: normal; }
  .cite-src  { color: #5a5048; font-family: 'Lora', serif; }
  .cite-dt   { color: #3a3028; font-family: 'Lora', serif; }

  /* Input */
  .input-dock {
    padding: 14px 22px 10px;
    border-top: 1px solid #1c1814;
    flex-shrink: 0;
  }

  .input-wrap {
    display: flex;
    align-items: flex-end;
    gap: 9px;
    background: #181410;
    border: 1px solid #252018;
    border-radius: 11px;
    padding: 9px 9px 9px 15px;
    transition: border-color 0.15s;
  }

  .input-wrap:focus-within { border-color: #c8a97a33; }

  .input-wrap textarea {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    resize: none;
    font-family: 'Lora', serif;
    font-size: 14px;
    color: #d8c8b0;
    line-height: 1.6;
    max-height: 120px;
    scrollbar-width: none;
  }

  .input-wrap textarea::placeholder { color: #352a1a; font-style: italic; }

  .send {
    flex-shrink: 0;
    width: 30px;
    height: 30px;
    border-radius: 7px;
    border: none;
    background: #c8a97a;
    color: #13100e;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s, opacity 0.15s;
  }

  .send.off { background: #252018; color: #3a3028; cursor: default; }
  .send:not(.off):hover { background: #d8b98a; }

  .input-hint {
    text-align: center;
    font-size: 10px;
    color: #252018;
    margin: 5px 0 0;
    font-family: 'Lora', serif;
  }

  /* ── Settings Drawer ────────────────────────────────────────────────────────── */
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(5, 4, 3, 0.55);
    z-index: 40;
    animation: fadeIn 0.2s ease;
  }

  .drawer {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: 360px;
    background: #0f0d0b;
    border-left: 1px solid #252018;
    z-index: 50;
    display: flex;
    flex-direction: column;
    animation: slideRight 0.22s ease;
    overflow: hidden;
  }

  .drawer-hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 18px 14px;
    border-bottom: 1px solid #1c1814;
    flex-shrink: 0;
  }

  .drawer-title {
    font-family: 'DM Serif Display', serif;
    font-size: 17px;
    color: #c8b89a;
    font-weight: 400;
    margin: 0;
  }

  .close {
    background: none;
    border: none;
    color: #4a4038;
    font-size: 20px;
    cursor: pointer;
    padding: 1px 5px;
    border-radius: 4px;
    line-height: 1;
    transition: color 0.1s;
  }

  .close:hover { color: #8a7868; }

  .dtabs {
    display: flex;
    padding: 10px 14px 0;
    gap: 2px;
    border-bottom: 1px solid #1c1814;
    flex-shrink: 0;
  }

  .dtab {
    padding: 6px 14px 10px;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    color: #4a4038;
    font-family: 'Lora', serif;
    font-size: 12.5px;
    cursor: pointer;
    transition: color 0.15s, border-color 0.15s;
  }

  .dtab:hover { color: #8a7868; }
  .dtab.on    { color: #c8a97a; border-bottom-color: #c8a97a; }

  .dpane {
    flex: 1;
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    overflow-y: auto;
    scrollbar-width: none;
  }

  .dlabel {
    font-size: 12px;
    color: #3e3428;
    font-style: italic;
    margin: 0;
    line-height: 1.6;
  }

  .dtextarea {
    flex: 1;
    background: #181410;
    border: 1px solid #252018;
    border-radius: 8px;
    padding: 12px 14px;
    color: #b8a888;
    font-family: 'Lora', serif;
    font-size: 13px;
    line-height: 1.75;
    resize: none;
    outline: none;
    transition: border-color 0.15s;
    scrollbar-width: none;
    min-height: 140px;
  }

  .dtextarea:focus           { border-color: #c8a97a33; }
  .dtextarea::placeholder    { color: #2e2820; font-style: italic; }

  .dactions {
    display: flex;
    gap: 8px;
    flex-shrink: 0;
  }

  .dact {
    padding: 7px 16px;
    border-radius: 7px;
    font-family: 'Lora', serif;
    font-size: 12.5px;
    cursor: pointer;
    border: 1px solid #252018;
    background: #181410;
    color: #6a5f54;
    transition: all 0.15s;
  }

  .dact:not(:disabled):hover { color: #c8a97a; border-color: #c8a97a44; }

  .dact.primary {
    background: #c8a97a;
    color: #13100e;
    border-color: #c8a97a;
  }

  .dact.primary:not(:disabled):hover { background: #d8b98a; }
  .dact:disabled { opacity: 0.35; cursor: default; }

  /* ── Markdown prose ─────────────────────────────────────────────────────────── */
  :global(.prose-chat) {
    font-family: 'Lora', serif;
    font-size: 14px;
    line-height: 1.8;
    color: #d8c8b0;
  }

  :global(.prose-chat p)              { margin: 0 0 0.65em; }
  :global(.prose-chat p:last-child)   { margin-bottom: 0; }
  :global(.prose-chat ul, .prose-chat ol) { margin: 0.4em 0 0.65em 1.3em; }
  :global(.prose-chat li)             { margin: 0.2em 0; }

  :global(.prose-chat h1, .prose-chat h2, .prose-chat h3) {
    font-family: 'DM Serif Display', serif;
    color: #e0d0b8;
    font-weight: 400;
    margin: 1em 0 0.35em;
  }

  :global(.prose-chat h1) { font-size: 1.2em; }
  :global(.prose-chat h2) { font-size: 1.05em; }
  :global(.prose-chat h3) { font-size: 0.95em; font-style: italic; }

  :global(.prose-chat strong) { color: #e0d0b8; font-weight: 600; }
  :global(.prose-chat em)     { color: #c0a888; }
  :global(.prose-chat a)      { color: #c8a97a; text-underline-offset: 2px; }

  :global(.prose-chat code:not(pre code)) {
    background: #0d0b09;
    color: #c8a97a;
    padding: 0.1em 0.35em;
    border-radius: 4px;
    font-size: 0.84em;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    border: 1px solid #252018;
  }

  :global(.prose-chat pre) {
    background: #0d0b09;
    border: 1px solid #252018;
    border-radius: 8px;
    padding: 1em;
    margin: 0.75em 0;
    overflow-x: auto;
    scrollbar-width: none;
  }

  :global(.prose-chat pre code) {
    font-size: 0.82em;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    background: none;
    padding: 0;
    color: #d8c8b0;
    border: none;
  }

  :global(.hljs-keyword)  { color: #c8a97a; }
  :global(.hljs-string)   { color: #8abf8a; }
  :global(.hljs-comment)  { color: #5a5048; font-style: italic; }
  :global(.hljs-number)   { color: #b8a09a; }
  :global(.hljs-function) { color: #9ab0cc; }
  :global(.hljs-title)    { color: #9ab0cc; }
  :global(.hljs-built_in) { color: #c8a97a; }
  :global(.hljs-type)     { color: #b09ab8; }
  :global(.hljs-variable) { color: #d8c8b0; }
  :global(.hljs-attr)     { color: #c8a97a; }
  :global(.hljs-tag)      { color: #c87a7a; }

  /* ── Animations ─────────────────────────────────────────────────────────────── */
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(5px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  @keyframes msgIn {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
  }

  @keyframes slideRight {
    from { transform: translateX(32px); opacity: 0; }
    to   { transform: translateX(0);    opacity: 1; }
  }

  @keyframes pulseDot {
    0%, 80%, 100% { transform: scale(0.75); opacity: 0.35; }
    40%           { transform: scale(1.15); opacity: 1; }
  }
</style>
