<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
  <link href="https://fonts.googleapis.com/css2?family=Raleway:wght@100;200;300&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&display=swap" rel="stylesheet" />
</svelte:head>

<script>
  import { createEventDispatcher, onMount } from 'svelte';
  import { themeStore } from '../lib/themeStore.js';

  const dispatch = createEventDispatcher();

  let locked = true;
  let password = '';
  let shaking  = false;
  let loading  = false;
  let passwordInput;

  let bgMedia = null, bgMediaType = null;
  themeStore.subscribe(v => {
    bgMedia     = v.preset === 'custom' ? v.custom.bgMedia     : null;
    bgMediaType = v.preset === 'custom' ? v.custom.bgMediaType : null;
  });

  let time = '', dateStr = '';
  function tick() {
    const now = new Date();
    const h   = String(now.getHours()).padStart(2, '0');
    const m   = String(now.getMinutes()).padStart(2, '0');
    time    = `${h}:${m}`;
    dateStr = now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
  }

  onMount(() => {
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  });

  function unlock() {
    if (!locked) return;
    locked = false;
    setTimeout(() => passwordInput?.focus(), 520);
  }

  function handleWheel(e)  { if (e.deltaY < 0) unlock(); }

  let touchY = 0;
  function onTouchStart(e) { touchY = e.touches[0].clientY; }
  function onTouchEnd(e)   { if (touchY - e.changedTouches[0].clientY > 40) unlock(); }

  async function submit() {
    if (!password || loading) return;
    loading = true;
    const res = await fetch('/api/auth/login', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ password }),
    });
    loading = false;
    if (res.ok) {
      dispatch('authed');
    } else {
      shaking  = true;
      password = '';
      setTimeout(() => { shaking = false; passwordInput?.focus(); }, 680);
    }
  }

  function onKey(e) { if (e.key === 'Enter') submit(); }
</script>

<!-- ── Wallpaper ── -->
{#if bgMedia && bgMediaType === 'image'}
  <div class="wall" class:blurred={!locked} style="background-image:url({bgMedia})" />
{:else if bgMedia && bgMediaType === 'video'}
  <div class="wall" class:blurred={!locked}>
    <video src={bgMedia} autoplay loop muted playsinline class="wall-video" />
  </div>
{:else}
  <div class="wall fallback" class:blurred={!locked} />
{/if}

<!-- ── Overlay (darkens on unlock) ── -->
<div class="overlay" class:dark={!locked} />

<!-- ── Full-screen stage ── -->
<div class="stage"
     on:click={unlock}
     on:wheel={handleWheel}
     on:touchstart={onTouchStart}
     on:touchend={onTouchEnd}
     role="button" tabindex="0"
     on:keydown={e => (e.key === 'Enter' || e.key === ' ') && unlock()}>

  <!-- Clock -->
  <div class="clock" class:gone={!locked}>
    <div class="clock-time">{time}</div>
    <div class="clock-date">{dateStr}</div>
  </div>

  <!-- Swipe hint -->
  <div class="hint" class:gone={!locked}>
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
         fill="none" stroke="currentColor" stroke-width="1.5"
         stroke-linecap="round" stroke-linejoin="round">
      <polyline points="18 15 12 9 6 15" />
    </svg>
    <span>swipe up</span>
  </div>

  <!-- Login panel -->
  <div class="panel" class:visible={!locked} class:shake={shaking}
       on:click|stopPropagation role="presentation">

    <div class="avatar" class:pop={!locked}>
      <span>J</span>
    </div>

    <p class="username">Janav</p>

    <div class="input-row">
      <input
        bind:this={passwordInput}
        bind:value={password}
        type="password"
        placeholder="Password"
        autocomplete="current-password"
        on:keydown={onKey}
      />
      <button class="go-btn" on:click={submit} disabled={loading} aria-label="Sign in">
        {#if loading}
          <svg class="spin-icon" width="13" height="13" viewBox="0 0 24 24"
               fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
            <path d="M12 2a10 10 0 0 1 10 10" />
          </svg>
        {:else}
          <svg width="13" height="13" viewBox="0 0 24 24"
               fill="none" stroke="currentColor" stroke-width="2.5"
               stroke-linecap="round" stroke-linejoin="round">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        {/if}
      </button>
    </div>

  </div>
</div>

<style>
  /* ── Wallpaper ─────────────────────────────────────────────────────────── */
  .wall {
    position: fixed;
    inset: 0;
    z-index: 0;
    background-size: cover;
    background-position: center;
    will-change: filter, transform;
    transition:
      filter    0.72s cubic-bezier(0.4, 0, 0.2, 1),
      transform 0.72s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .wall.blurred {
    filter: blur(38px) brightness(0.58) saturate(1.35);
    transform: scale(1.08);
  }
  .fallback {
    background:
      radial-gradient(ellipse at 28% 22%, rgba(100, 65, 20, 0.85) 0%, transparent 52%),
      radial-gradient(ellipse at 72% 78%, rgba(20, 28, 58, 0.8)   0%, transparent 52%),
      radial-gradient(ellipse at 62% 18%, rgba(70, 45, 12, 0.65)  0%, transparent 45%),
      #0b0a08;
  }
  .wall-video {
    position: absolute;
    inset: 0;
    width: 100%; height: 100%;
    object-fit: cover;
  }

  /* ── Overlay ───────────────────────────────────────────────────────────── */
  .overlay {
    position: fixed;
    inset: 0;
    z-index: 1;
    pointer-events: none;
    background: transparent;
    transition: background 0.65s ease;
  }
  .overlay.dark { background: rgba(0, 0, 0, 0.2); }

  /* ── Stage ─────────────────────────────────────────────────────────────── */
  .stage {
    position: fixed;
    inset: 0;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    outline: none;
    user-select: none;
  }

  /* ── Clock ─────────────────────────────────────────────────────────────── */
  .clock {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding-bottom: 6vh;
    pointer-events: none;
    transition: opacity 0.4s ease, transform 0.4s ease;
  }
  .clock.gone {
    opacity: 0;
    transform: translateY(-22px);
  }
  .clock-time {
    font-family: 'Raleway', sans-serif;
    font-weight: 100;
    font-size: clamp(5.5rem, 15vw, 9.5rem);
    color: rgba(255, 255, 255, 0.93);
    letter-spacing: -0.025em;
    line-height: 1;
    text-shadow:
      0 2px 48px rgba(0, 0, 0, 0.55),
      0 0 120px rgba(255, 255, 255, 0.03);
  }
  .clock-date {
    font-family: 'DM Sans', sans-serif;
    font-weight: 300;
    font-size: clamp(0.78rem, 1.4vw, 0.96rem);
    color: rgba(255, 255, 255, 0.52);
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-top: 14px;
  }

  /* ── Swipe hint ─────────────────────────────────────────────────────────── */
  .hint {
    position: absolute;
    bottom: 46px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    color: rgba(255, 255, 255, 0.38);
    pointer-events: none;
    transition: opacity 0.35s ease;
    animation: float 2.8s ease-in-out infinite;
  }
  .hint.gone { opacity: 0; }
  .hint span {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.65rem;
    font-weight: 400;
    letter-spacing: 0.22em;
    text-transform: uppercase;
  }

  @keyframes float {
    0%, 100% { transform: translateX(-50%) translateY(0px); }
    50%       { transform: translateX(-50%) translateY(-9px); }
  }

  /* ── Panel ──────────────────────────────────────────────────────────────── */
  .panel {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 18px;
    padding: 48px 44px 44px;
    width: 296px;

    /* Deep amber-tinted frosted glass — matches Trellis warm palette */
    background: linear-gradient(
      160deg,
      rgba(255, 255, 255, 0.085) 0%,
      rgba(200, 140, 60, 0.045) 100%
    );
    backdrop-filter: blur(52px) saturate(1.7) brightness(1.08);
    -webkit-backdrop-filter: blur(52px) saturate(1.7) brightness(1.08);
    border: 1px solid rgba(255, 255, 255, 0.115);
    border-radius: 30px;
    box-shadow:
      0 48px 120px rgba(0, 0, 0, 0.52),
      0 12px 40px  rgba(0, 0, 0, 0.28),
      inset 0 1px 0 rgba(255, 255, 255, 0.2),
      inset 0 -1px 0 rgba(0, 0, 0, 0.12);

    /* Entry: start below, slightly scaled down */
    opacity: 0;
    transform: translateY(30px) scale(0.975);
    transition:
      opacity   0.58s cubic-bezier(0.32, 0.72, 0, 1) 0.14s,
      transform 0.58s cubic-bezier(0.32, 0.72, 0, 1) 0.14s;
    pointer-events: none;
    cursor: default;
  }
  .panel.visible {
    opacity: 1;
    transform: translateY(0) scale(1);
    pointer-events: all;
  }
  .panel.shake {
    animation: shake 0.62s cubic-bezier(0.36, 0.07, 0.19, 0.97);
  }

  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    12%       { transform: translateX(-10px); }
    28%       { transform: translateX(10px); }
    44%       { transform: translateX(-7px); }
    60%       { transform: translateX(7px); }
    76%       { transform: translateX(-3px); }
    90%       { transform: translateX(3px); }
  }

  /* ── Avatar ─────────────────────────────────────────────────────────────── */
  .avatar {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    /* Radial gradient → 3D lit sphere feel */
    background: radial-gradient(circle at 36% 32%, #ebb86a, #c8813a 48%, #7a4820 82%, #5a3010);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow:
      0 0 0 2.5px rgba(200, 129, 58, 0.5),
      0 0 0 5.5px rgba(200, 129, 58, 0.13),
      0 10px 36px rgba(0, 0, 0, 0.48),
      inset 0 1px 0 rgba(255, 255, 255, 0.22);
    /* Spring-scale in when panel opens */
    transform: scale(0.82);
    transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.22s;
  }
  .avatar.pop { transform: scale(1); }

  .avatar span {
    font-family: 'DM Sans', sans-serif;
    font-size: 2rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.96);
    line-height: 1;
    letter-spacing: -0.01em;
  }

  /* ── Username ────────────────────────────────────────────────────────────── */
  .username {
    margin: 0;
    font-family: 'DM Sans', sans-serif;
    font-size: 1.05rem;
    font-weight: 400;
    color: rgba(255, 255, 255, 0.88);
    letter-spacing: 0.015em;
  }

  /* ── Input row ───────────────────────────────────────────────────────────── */
  .input-row {
    display: flex;
    align-items: center;
    width: 100%;
    background: rgba(0, 0, 0, 0.22);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    overflow: hidden;
    transition:
      border-color 0.25s ease,
      background   0.25s ease,
      box-shadow   0.25s ease;
  }
  .input-row:focus-within {
    border-color: rgba(200, 129, 58, 0.55);
    background:   rgba(0, 0, 0, 0.3);
    box-shadow:   0 0 0 3px rgba(200, 129, 58, 0.13);
  }

  input {
    flex: 1;
    min-width: 0;
    background: transparent;
    border: none;
    padding: 12px 6px 12px 16px;
    color: rgba(255, 255, 255, 0.92);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.9rem;
    font-weight: 400;
    letter-spacing: 0.07em;
    outline: none;
  }
  input::placeholder {
    color: rgba(255, 255, 255, 0.26);
    letter-spacing: 0.01em;
  }

  /* ── Submit button ───────────────────────────────────────────────────────── */
  .go-btn {
    width: 38px;
    height: 38px;
    margin: 4px;
    flex-shrink: 0;
    border: none;
    border-radius: 10px;
    background: linear-gradient(145deg, #d08a42, #b87232);
    color: rgba(255, 255, 255, 0.95);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow:
      0 2px 10px rgba(0, 0, 0, 0.32),
      inset 0 1px 0 rgba(255, 255, 255, 0.18);
    transition:
      background  0.2s ease,
      transform   0.15s ease,
      box-shadow  0.2s ease;
  }
  .go-btn:hover:not(:disabled) {
    background: linear-gradient(145deg, #e09a52, #c88242);
    transform: scale(1.07);
    box-shadow:
      0 4px 16px rgba(0, 0, 0, 0.38),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
  .go-btn:active:not(:disabled) { transform: scale(0.95); }
  .go-btn:disabled { opacity: 0.45; cursor: not-allowed; }

  /* ── Spinner ─────────────────────────────────────────────────────────────── */
  .spin-icon {
    animation: spin 0.72s linear infinite;
    transform-origin: center;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
