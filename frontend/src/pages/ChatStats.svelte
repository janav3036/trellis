<script>
  import { onMount } from 'svelte';

  let chats = [];
  let uploading = false;
  let error = '';
  let fileInput;
  let dragOver = false;

  async function loadChats() {
    const res = await fetch('/api/chats/');
    chats = await res.json();
  }

  async function handleFile(file) {
    if (!file || !file.name.endsWith('.txt')) {
      error = 'Need a WhatsApp .txt export — export from WhatsApp → Chat → Export Chat';
      return;
    }
    error = '';
    uploading = true;
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch('/api/chats/upload', { method: 'POST', body: fd });
    const data = await res.json();
    uploading = false;
    if (!res.ok) { error = data.error || 'Upload failed'; return; }
    await loadChats();
  }

  function onFileInput(e) { handleFile(e.target.files[0]); e.target.value = ''; }
  function onDrop(e) { e.preventDefault(); dragOver = false; handleFile(e.dataTransfer.files[0]); }

  async function deleteChat(name) {
    await fetch(`/api/chats/${encodeURIComponent(name)}`, { method: 'DELETE' });
    await loadChats();
  }

  function viewReport(name) {
    window.open(`/api/chats/${encodeURIComponent(name)}/report`, '_blank');
  }

  function fmtDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
  }

  function participants(raw) {
    try { return JSON.parse(raw || '[]'); } catch { return []; }
  }

  // deterministic color per name
  const PERSON_COLORS = ['#c8813a','#6b8c6b','#6b7f8c','#8c6b7f','#8c856b','#6b8c82'];
  function personColor(name, idx) {
    return PERSON_COLORS[idx % PERSON_COLORS.length];
  }

  function initials(name) {
    return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  }

  onMount(loadChats);
</script>

<div class="page">

  <!-- ── Header ── -->
  <div class="header">
    <div class="header-left">
      <span class="eyebrow">Personal Archive</span>
      <h1>Chat Stats</h1>
    </div>
    {#if chats.length > 0}
      <div class="total-badge">{chats.length} conversation{chats.length !== 1 ? 's' : ''}</div>
    {/if}
  </div>

  <!-- ── Upload Zone ── -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div
    class="drop-zone"
    class:drag-active={dragOver}
    class:is-uploading={uploading}
    on:dragover|preventDefault={() => (dragOver = true)}
    on:dragleave={() => (dragOver = false)}
    on:drop={onDrop}
    on:click={() => !uploading && fileInput.click()}
  >
    <div class="drop-inner">
      {#if uploading}
        <div class="upload-spinner"></div>
        <span class="drop-label">Parsing messages…</span>
      {:else}
        <div class="drop-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
        </div>
        <span class="drop-label">Drop a WhatsApp <code>.txt</code> export</span>
        <span class="drop-sub">or click to choose · iOS &amp; Android supported</span>
      {/if}
    </div>
    <div class="drop-corner tl"></div>
    <div class="drop-corner tr"></div>
    <div class="drop-corner bl"></div>
    <div class="drop-corner br"></div>
  </div>
  <input type="file" accept=".txt" bind:this={fileInput} on:change={onFileInput} style="display:none" />

  {#if error}
    <div class="error-banner">{error}</div>
  {/if}

  <!-- ── Chat Grid ── -->
  {#if chats.length === 0 && !uploading}
    <div class="empty-state">
      <div class="empty-line"></div>
      <span>No chats yet — upload an export to begin</span>
      <div class="empty-line"></div>
    </div>
  {:else}
    <div class="chat-grid">
      {#each chats as chat, i}
        {@const people = participants(chat.participants)}
        <div class="chat-card" style="animation-delay: {i * 60}ms">

          <!-- Card top: name + delete -->
          <div class="card-top">
            <div class="chat-name">{chat.chat_name}</div>
            <button class="btn-delete" on:click={() => deleteChat(chat.chat_name)} title="Remove">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          <!-- Big stat -->
          <div class="msg-count">{chat.message_count.toLocaleString()}</div>
          <div class="msg-label">messages</div>

          <!-- Divider -->
          <div class="card-divider"></div>

          <!-- Participants -->
          <div class="participants">
            {#each people as person, pi}
              <div class="person-chip" style="--pc: {personColor(person, pi)}">
                <span class="person-avatar">{initials(person)}</span>
                <span class="person-name">{person}</span>
              </div>
            {/each}
          </div>

          <!-- Date range -->
          <div class="date-range">
            <span>{fmtDate(chat.date_from)}</span>
            <span class="date-sep">→</span>
            <span>{fmtDate(chat.date_to)}</span>
          </div>

          <!-- Report button -->
          <button class="btn-report" on:click={() => viewReport(chat.chat_name)}>
            View Report
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              <polyline points="15 3 21 3 21 9"/>
              <line x1="10" y1="14" x2="21" y2="3"/>
            </svg>
          </button>

        </div>
      {/each}
    </div>
  {/if}

</div>

<style>
  .page {
    max-width: 860px;
    margin: 0 auto;
    padding: 40px 28px 80px;
  }

  /* ── Header ── */
  .header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-bottom: 36px;
  }
  .eyebrow {
    display: block;
    font-size: 10px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--accent, #c8813a);
    margin-bottom: 6px;
    font-family: 'Courier New', monospace;
  }
  h1 {
    font-size: 32px;
    font-weight: 700;
    color: var(--text-primary, #e8e0d0);
    letter-spacing: -0.5px;
    margin: 0;
  }
  .total-badge {
    font-size: 11px;
    font-family: 'Courier New', monospace;
    color: var(--text-secondary, #9a9080);
    border: 1px solid color-mix(in srgb, var(--text-secondary, #9a9080) 30%, transparent);
    padding: 4px 10px;
    border-radius: 20px;
    margin-bottom: 4px;
  }

  /* ── Drop Zone ── */
  .drop-zone {
    position: relative;
    border: 1px dashed color-mix(in srgb, var(--text-secondary, #9a9080) 35%, transparent);
    border-radius: 14px;
    padding: 44px 24px;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s;
    margin-bottom: 12px;
    background: color-mix(in srgb, var(--surface, #242019) 60%, transparent);
  }
  .drop-zone:hover, .drag-active {
    border-color: var(--accent, #c8813a);
    background: color-mix(in srgb, var(--accent, #c8813a) 5%, var(--surface, #242019));
  }
  .is-uploading { cursor: default; pointer-events: none; }

  /* corner brackets */
  .drop-corner {
    position: absolute;
    width: 12px;
    height: 12px;
    border-color: var(--accent, #c8813a);
    border-style: solid;
    opacity: 0.5;
    transition: opacity 0.2s;
  }
  .drop-zone:hover .drop-corner { opacity: 1; }
  .tl { top: 8px; left: 8px;   border-width: 1.5px 0 0 1.5px; }
  .tr { top: 8px; right: 8px;  border-width: 1.5px 1.5px 0 0; }
  .bl { bottom: 8px; left: 8px;  border-width: 0 0 1.5px 1.5px; }
  .br { bottom: 8px; right: 8px; border-width: 0 1.5px 1.5px 0; }

  .drop-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
  .drop-icon {
    color: var(--text-secondary, #9a9080);
    margin-bottom: 4px;
    transition: color 0.2s;
  }
  .drop-zone:hover .drop-icon { color: var(--accent, #c8813a); }
  .drop-label {
    font-size: 14px;
    color: var(--text-primary, #e8e0d0);
  }
  .drop-label code {
    font-family: 'Courier New', monospace;
    color: var(--accent, #c8813a);
    font-size: 13px;
  }
  .drop-sub {
    font-size: 11px;
    color: var(--text-secondary, #9a9080);
    font-family: 'Courier New', monospace;
  }

  /* spinner */
  .upload-spinner {
    width: 22px;
    height: 22px;
    border: 2px solid color-mix(in srgb, var(--accent, #c8813a) 25%, transparent);
    border-top-color: var(--accent, #c8813a);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    margin-bottom: 4px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Error ── */
  .error-banner {
    font-size: 12px;
    color: #c47a5a;
    font-family: 'Courier New', monospace;
    padding: 8px 14px;
    background: color-mix(in srgb, #c47a5a 8%, var(--surface, #242019));
    border: 1px solid color-mix(in srgb, #c47a5a 30%, transparent);
    border-radius: 8px;
    margin-bottom: 12px;
  }

  /* ── Empty State ── */
  .empty-state {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-top: 40px;
    color: var(--text-secondary, #9a9080);
    font-size: 12px;
    font-family: 'Courier New', monospace;
  }
  .empty-line {
    flex: 1;
    height: 1px;
    background: color-mix(in srgb, var(--text-secondary, #9a9080) 20%, transparent);
  }

  /* ── Chat Grid ── */
  .chat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px;
    margin-top: 32px;
  }

  .chat-card {
    background: var(--surface, #242019);
    border: 1px solid color-mix(in srgb, var(--text-secondary, #9a9080) 18%, transparent);
    border-radius: 12px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 0;
    animation: cardIn 0.35s ease both;
    transition: border-color 0.2s, transform 0.15s;
  }
  .chat-card:hover {
    border-color: color-mix(in srgb, var(--accent, #c8813a) 40%, transparent);
    transform: translateY(-1px);
  }
  @keyframes cardIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .card-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 14px;
    gap: 8px;
  }
  .chat-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary, #e8e0d0);
    line-height: 1.3;
  }

  .btn-delete {
    flex-shrink: 0;
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-secondary, #9a9080);
    padding: 2px;
    border-radius: 4px;
    transition: color 0.15s;
    display: flex;
    align-items: center;
  }
  .btn-delete:hover { color: #c47a5a; }

  .msg-count {
    font-size: 36px;
    font-weight: 700;
    font-family: 'Courier New', monospace;
    color: var(--text-primary, #e8e0d0);
    letter-spacing: -1px;
    line-height: 1;
    margin-bottom: 2px;
  }
  .msg-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--text-secondary, #9a9080);
    margin-bottom: 16px;
  }

  .card-divider {
    height: 1px;
    background: color-mix(in srgb, var(--text-secondary, #9a9080) 15%, transparent);
    margin-bottom: 14px;
  }

  .participants {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 12px;
  }
  .person-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: color-mix(in srgb, var(--pc) 12%, var(--surface, #242019));
    border: 1px solid color-mix(in srgb, var(--pc) 30%, transparent);
    border-radius: 20px;
    padding: 3px 8px 3px 4px;
  }
  .person-avatar {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: var(--pc);
    color: #13110d;
    font-size: 8px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
  .person-name {
    font-size: 11px;
    color: color-mix(in srgb, var(--pc) 80%, var(--text-primary, #e8e0d0));
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100px;
  }

  .date-range {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-family: 'Courier New', monospace;
    color: var(--text-secondary, #9a9080);
    margin-bottom: 16px;
  }
  .date-sep { color: var(--accent, #c8813a); opacity: 0.6; }

  .btn-report {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    width: 100%;
    padding: 9px 0;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    background: color-mix(in srgb, var(--accent, #c8813a) 15%, var(--surface, #242019));
    color: var(--accent, #c8813a);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
    border: 1px solid color-mix(in srgb, var(--accent, #c8813a) 25%, transparent);
    transition: background 0.15s, color 0.15s;
    margin-top: auto;
  }
  .btn-report:hover {
    background: color-mix(in srgb, var(--accent, #c8813a) 22%, var(--surface, #242019));
    color: var(--text-primary, #e8e0d0);
  }

  @media (max-width: 600px) {
    .page { padding: 24px 16px 60px; }
    h1 { font-size: 26px; }
    .chat-grid { grid-template-columns: 1fr; }
  }
</style>
