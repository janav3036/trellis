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
      error = 'Needs a WhatsApp .txt export — Chat → Export Chat → Without Media';
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

  function downloadReport(name) {
    const a = document.createElement('a');
    a.href = `/api/chats/${encodeURIComponent(name)}/report?download=1`;
    a.download = `${name}.html`;
    a.click();
  }

  function fmtDateRange(from_, to_) {
    if (!from_ || !to_) return '—';
    const f = new Date(from_).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
    const t = new Date(to_).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
    return f === t ? f : `${f} – ${t}`;
  }

  function participants(raw) {
    try { return JSON.parse(raw || '[]'); } catch { return []; }
  }

  const COLORS = ['#a07850','#6b8c6b','#7080a8','#a87060','#6b8c88','#9a7888','#8a9860','#c4944a'];

  function personColor(idx) {
    return COLORS[idx % COLORS.length];
  }

  function initials(name) {
    return name.trim().split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase();
  }

  function monthsActive(from_, to_) {
    if (!from_ || !to_) return 0;
    const a = new Date(from_), b = new Date(to_);
    return (b.getFullYear() - a.getFullYear()) * 12 + (b.getMonth() - a.getMonth()) + 1;
  }

  onMount(loadChats);
</script>

<div class="page">

  <!-- ── Header ── -->
  <header>
    <div class="header-text">
      <span class="eyebrow">Personal Archive</span>
      <h1>Chats</h1>
    </div>
    {#if chats.length > 0}
      <span class="count-pill">{chats.length} export{chats.length !== 1 ? 's' : ''}</span>
    {/if}
  </header>

  <!-- ── Upload Zone ── -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div
    class="drop-zone"
    class:drag-over={dragOver}
    class:uploading
    on:dragover|preventDefault={() => dragOver = true}
    on:dragleave={() => dragOver = false}
    on:drop={onDrop}
    on:click={() => !uploading && fileInput.click()}
  >
    {#if uploading}
      <div class="scan-wrap">
        <div class="scan-line"></div>
        <svg class="doc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="8" y1="13" x2="16" y2="13"/>
          <line x1="8" y1="17" x2="13" y2="17"/>
        </svg>
      </div>
      <span class="drop-label">Parsing messages<span class="dots"></span></span>
    {:else}
      <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" y1="3" x2="12" y2="15"/>
      </svg>
      <span class="drop-label">Drop a WhatsApp <code>.txt</code> export</span>
      <span class="drop-hint">or click · iOS &amp; Android · without media</span>
    {/if}
    <div class="corner c-tl"></div>
    <div class="corner c-tr"></div>
    <div class="corner c-bl"></div>
    <div class="corner c-br"></div>
  </div>

  <input type="file" accept=".txt" bind:this={fileInput} on:change={onFileInput} style="display:none" />

  {#if error}
    <p class="error">{error}</p>
  {/if}

  <!-- ── Chat List ── -->
  {#if chats.length === 0 && !uploading}
    <div class="empty">
      <div class="empty-rule"></div>
      <span>No exports yet</span>
      <div class="empty-rule"></div>
    </div>
  {:else}
    <ul class="chat-list">
      {#each chats as chat, i}
        {@const people = participants(chat.participants)}
        {@const primaryColor = personColor(0)}
        <li class="chat-row" style="--delay:{i * 55}ms">
          <!-- Left accent -->
          <div class="row-accent">
            {#each people.slice(0, 4) as _, pi}
              <div class="accent-slice" style="background:{personColor(pi)};flex:{1}"></div>
            {/each}
          </div>

          <!-- Main content -->
          <div class="row-body">
            <div class="row-top">
              <span class="chat-name">{chat.chat_name}</span>
              <span class="msg-count">{chat.message_count.toLocaleString()}</span>
              <span class="msg-unit">msgs</span>
            </div>
            <div class="row-bottom">
              <!-- Participants -->
              <div class="avatars">
                {#each people.slice(0, 6) as person, pi}
                  <div class="avatar" style="--ac:{personColor(pi)}" title={person}>
                    {initials(person)}
                  </div>
                {/each}
                {#if people.length > 6}
                  <div class="avatar avatar-more">+{people.length - 6}</div>
                {/if}
              </div>
              <!-- Meta -->
              <span class="row-meta">{fmtDateRange(chat.date_from, chat.date_to)}</span>
              <span class="row-meta dim">{monthsActive(chat.date_from, chat.date_to)} mo · {people.length} people</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="row-actions">
            <button class="btn-report" on:click={() => viewReport(chat.chat_name)}>
              Report
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
              </svg>
            </button>
            <button class="btn-icon" on:click={() => downloadReport(chat.chat_name)} title="Download HTML">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </button>
            <button class="btn-del" on:click={() => deleteChat(chat.chat_name)} title="Remove">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                <path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
              </svg>
            </button>
          </div>
        </li>
      {/each}
    </ul>
  {/if}

</div>

<style>
  .page {
    max-width: 820px;
    margin: 0 auto;
    padding: 40px 28px 80px;
    font-family: 'DM Mono', 'Courier New', monospace;
  }

  /* ── Header ── */
  header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    margin-bottom: 32px;
  }
  .eyebrow {
    display: block;
    font-size: 9px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent, #c8813a);
    margin-bottom: 6px;
  }
  h1 {
    font-size: 28px;
    font-weight: 500;
    color: var(--text-primary, #e8e0d0);
    letter-spacing: -0.5px;
    margin: 0;
    font-family: 'DM Mono', monospace;
  }
  .count-pill {
    font-size: 10px;
    color: var(--text-secondary, #9a9080);
    border: 1px solid color-mix(in srgb, var(--text-secondary, #9a9080) 28%, transparent);
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 3px;
  }

  /* ── Drop Zone ── */
  .drop-zone {
    position: relative;
    border: 1px dashed color-mix(in srgb, var(--text-secondary, #9a9080) 32%, transparent);
    border-radius: 10px;
    padding: 40px 24px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 7px;
    cursor: pointer;
    transition: border-color 0.18s, background 0.18s;
    margin-bottom: 14px;
    overflow: hidden;
  }
  .drop-zone:hover, .drag-over {
    border-color: var(--accent, #c8813a);
    background: color-mix(in srgb, var(--accent, #c8813a) 4%, transparent);
  }
  .uploading { cursor: default; pointer-events: none; }

  .upload-icon {
    width: 26px; height: 26px;
    color: var(--text-secondary, #9a9080);
    transition: color 0.18s;
    margin-bottom: 2px;
  }
  .drop-zone:hover .upload-icon { color: var(--accent, #c8813a); }

  .drop-label {
    font-size: 13px;
    color: var(--text-primary, #e8e0d0);
  }
  .drop-label code {
    color: var(--accent, #c8813a);
    font-family: inherit;
  }
  .drop-hint {
    font-size: 10px;
    color: var(--text-secondary, #9a9080);
    letter-spacing: 0.3px;
  }

  /* scan animation */
  .scan-wrap {
    position: relative;
    width: 36px;
    height: 44px;
    margin-bottom: 4px;
  }
  .doc-icon {
    width: 36px; height: 44px;
    color: color-mix(in srgb, var(--accent, #c8813a) 50%, var(--text-secondary, #9a9080));
  }
  .scan-line {
    position: absolute;
    top: 0; left: -4px; right: -4px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent, #c8813a), transparent);
    animation: scan 1.2s ease-in-out infinite;
    border-radius: 1px;
  }
  @keyframes scan {
    0%   { top: 4px;  opacity: 0; }
    15%  { opacity: 1; }
    85%  { opacity: 1; }
    100% { top: 40px; opacity: 0; }
  }

  .dots::after {
    content: '';
    animation: dotdot 1.4s steps(4, end) infinite;
  }
  @keyframes dotdot {
    0%   { content: ''; }
    25%  { content: '.'; }
    50%  { content: '..'; }
    75%  { content: '...'; }
    100% { content: ''; }
  }

  /* corner brackets */
  .corner {
    position: absolute;
    width: 10px;
    height: 10px;
    border-color: var(--accent, #c8813a);
    border-style: solid;
    opacity: 0.4;
    transition: opacity 0.18s;
  }
  .drop-zone:hover .corner { opacity: 0.9; }
  .c-tl { top: 7px;    left: 7px;   border-width: 1.5px 0 0 1.5px; }
  .c-tr { top: 7px;    right: 7px;  border-width: 1.5px 1.5px 0 0; }
  .c-bl { bottom: 7px; left: 7px;   border-width: 0 0 1.5px 1.5px; }
  .c-br { bottom: 7px; right: 7px;  border-width: 0 1.5px 1.5px 0; }

  /* ── Error ── */
  .error {
    font-size: 11px;
    color: #c47a5a;
    padding: 7px 12px;
    background: color-mix(in srgb, #c47a5a 7%, var(--surface, #242019));
    border: 1px solid color-mix(in srgb, #c47a5a 28%, transparent);
    border-radius: 6px;
    margin-bottom: 12px;
  }

  /* ── Empty ── */
  .empty {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-top: 44px;
    font-size: 11px;
    color: var(--text-secondary, #9a9080);
  }
  .empty-rule {
    flex: 1;
    height: 1px;
    background: color-mix(in srgb, var(--text-secondary, #9a9080) 18%, transparent);
  }

  /* ── Chat List ── */
  .chat-list {
    list-style: none;
    margin-top: 28px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .chat-row {
    display: flex;
    align-items: stretch;
    background: var(--surface, #242019);
    border: 1px solid color-mix(in srgb, var(--text-secondary, #9a9080) 16%, transparent);
    border-radius: 10px;
    overflow: hidden;
    animation: rowIn 0.32s ease both;
    animation-delay: var(--delay, 0ms);
    transition: border-color 0.16s, transform 0.12s;
  }
  .chat-row:hover {
    border-color: color-mix(in srgb, var(--accent, #c8813a) 35%, transparent);
    transform: translateX(2px);
  }
  @keyframes rowIn {
    from { opacity: 0; transform: translateX(-8px); }
    to   { opacity: 1; transform: translateX(0); }
  }

  /* Left multi-color accent bar */
  .row-accent {
    width: 4px;
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
  }
  .accent-slice { min-height: 4px; }

  /* Row body */
  .row-body {
    flex: 1;
    padding: 14px 16px;
    min-width: 0;
  }
  .row-top {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 8px;
    flex-wrap: wrap;
  }
  .chat-name {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary, #e8e0d0);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 260px;
  }
  .msg-count {
    font-size: 20px;
    font-weight: 400;
    color: var(--accent, #c8813a);
    letter-spacing: -0.5px;
    line-height: 1;
  }
  .msg-unit {
    font-size: 9px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--text-secondary, #9a9080);
    margin-left: -4px;
  }

  .row-bottom {
    display: flex;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
  }

  /* Avatar stack */
  .avatars {
    display: flex;
    align-items: center;
  }
  .avatar {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--ac, #8a7a6a);
    color: #0e0c09;
    font-size: 8px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1.5px solid var(--surface, #242019);
    flex-shrink: 0;
    margin-left: -6px;
  }
  .avatar:first-child { margin-left: 0; }
  .avatar-more {
    background: color-mix(in srgb, var(--text-secondary, #9a9080) 25%, var(--surface, #242019));
    color: var(--text-secondary, #9a9080);
    font-size: 7px;
  }

  .row-meta {
    font-size: 10px;
    color: var(--text-secondary, #9a9080);
    white-space: nowrap;
  }
  .row-meta.dim { opacity: 0.6; }

  /* Row actions */
  .row-actions {
    display: flex;
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    border-left: 1px solid color-mix(in srgb, var(--text-secondary, #9a9080) 12%, transparent);
    flex-shrink: 0;
  }
  .btn-report {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    padding: 0 18px;
    border: none;
    cursor: pointer;
    background: transparent;
    color: var(--accent, #c8813a);
    font-size: 11px;
    font-family: 'DM Mono', 'Courier New', monospace;
    font-weight: 500;
    transition: background 0.14s;
    white-space: nowrap;
    border-bottom: 1px solid color-mix(in srgb, var(--text-secondary, #9a9080) 12%, transparent);
  }
  .btn-report:hover {
    background: color-mix(in srgb, var(--accent, #c8813a) 10%, transparent);
  }
  .btn-icon {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px 14px;
    border: none;
    cursor: pointer;
    background: transparent;
    color: var(--text-secondary, #9a9080);
    transition: color 0.14s, background 0.14s;
    border-bottom: 1px solid color-mix(in srgb, var(--text-secondary, #9a9080) 12%, transparent);
  }
  .btn-icon:hover {
    color: var(--accent, #c8813a);
    background: color-mix(in srgb, var(--accent, #c8813a) 8%, transparent);
  }
  .btn-del {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px 14px;
    border: none;
    cursor: pointer;
    background: transparent;
    color: var(--text-secondary, #9a9080);
    transition: color 0.14s, background 0.14s;
  }
  .btn-del:hover {
    color: #c47a5a;
    background: color-mix(in srgb, #c47a5a 8%, transparent);
  }

  @media (max-width: 580px) {
    .page { padding: 24px 16px 60px; }
    h1 { font-size: 22px; }
    .chat-name { max-width: 140px; }
    .btn-report { padding: 0 12px; }
    .btn-del { padding: 10px 12px; }
  }
</style>
