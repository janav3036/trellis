<script>
  import { onMount } from 'svelte';

  let chats   = [];
  let loading = true;

  onMount(async () => {
    try {
      const res = await fetch('/api/chats/');
      chats = await res.json();
    } catch {}
    loading = false;
  });

  const COLORS = ['#a07850','#6b8c6b','#7080a8','#a87060','#6b8c88','#9a7888'];

  function participants(raw) {
    try { return JSON.parse(raw || '[]'); } catch { return []; }
  }

  function fmtRange(from_, to_) {
    if (!from_ || !to_) return '—';
    const opts = { month: 'short', year: '2-digit' };
    const f = new Date(from_).toLocaleDateString('en-IN', opts);
    const t = new Date(to_).toLocaleDateString('en-IN', opts);
    return f === t ? f : `${f} – ${t}`;
  }

  function initials(name) {
    return name.trim().split(/\s+/).map(w => w[0]).join('').slice(0, 2).toUpperCase();
  }

  function openReport(name) {
    window.open(`/api/chats/${encodeURIComponent(name)}/report`, '_blank');
  }
</script>

<div class="panel">
  <div class="hdr">
    <span class="lbl">ChatStats</span>
    <a href="/#/chatstats" class="open-link">view all →</a>
  </div>

  <div class="body">
    {#if loading}
      <p class="empty">—</p>
    {:else if chats.length === 0}
      <p class="empty">No chats yet.<br/>Upload a WhatsApp export on the ChatStats page.</p>
    {:else}
      <ul class="list">
        {#each chats.slice(0, 5) as chat, i}
          <li>
            <button class="row" on:click={() => openReport(chat.chat_name)} style="--i:{i}">
              <div class="avatars">
                {#each participants(chat.participants).slice(0, 2) as p, j}
                  <span
                    class="av"
                    style="background:{COLORS[j % COLORS.length]}; left:{j * 11}px; z-index:{2 - j}"
                  >{initials(p)}</span>
                {/each}
              </div>

              <div class="info">
                <span class="name">{chat.chat_name}</span>
                <span class="meta">
                  {(chat.message_count || 0).toLocaleString()} msgs · {fmtRange(chat.date_from, chat.date_to)}
                </span>
              </div>

              <span class="arr">↗</span>
            </button>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>

<style>
  .panel {
    height: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 0;
    overflow: hidden;
  }

  /* ── header ── */
  .hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
    margin-bottom: 10px;
  }

  .lbl {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.67rem;
    font-weight: 500;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    color: var(--text-secondary);
  }

  .open-link {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.64rem;
    color: var(--text-secondary);
    text-decoration: none;
    opacity: 0.38;
    letter-spacing: 0.03em;
    transition: opacity 0.15s;
  }
  .open-link:hover { opacity: 0.9; }

  /* ── body ── */
  .body {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
  }

  .empty {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.7rem;
    color: var(--text-secondary);
    opacity: 0.32;
    margin: auto;
    text-align: center;
    line-height: 1.6;
  }

  /* ── list ── */
  .list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .row {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 7px 8px;
    border-radius: 8px;
    border: 1px solid transparent;
    background: transparent;
    cursor: pointer;
    text-align: left;
    transition: background 0.15s, border-color 0.15s;
    animation: slideIn 0.3s ease both;
    animation-delay: calc(var(--i) * 45ms);
  }

  .row:hover {
    background: rgba(200, 169, 122, 0.05);
    border-color: rgba(200, 169, 122, 0.13);
  }

  @keyframes slideIn {
    from { opacity: 0; transform: translateX(-5px); }
    to   { opacity: 1; transform: translateX(0); }
  }

  /* ── avatars ── */
  .avatars {
    position: relative;
    width: 30px;
    height: 22px;
    flex-shrink: 0;
  }

  .av {
    position: absolute;
    top: 0;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.52rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.88);
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1.5px solid var(--bg);
  }

  /* ── info ── */
  .info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1px;
    min-width: 0;
  }

  .name {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.73rem;
    font-weight: 500;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .meta {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.61rem;
    color: var(--text-secondary);
    opacity: 0.45;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .arr {
    font-size: 0.72rem;
    color: var(--text-secondary);
    opacity: 0.2;
    flex-shrink: 0;
    transition: opacity 0.15s;
  }

  .row:hover .arr { opacity: 0.65; }
</style>
