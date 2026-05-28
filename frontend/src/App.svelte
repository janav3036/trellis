<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
  <link href="https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,400&display=swap" rel="stylesheet">
</svelte:head>

<script>
import Router from 'svelte-spa-router'
import { themeStore } from './lib/themeStore.js';
import MobileNav from './lib/MobileNav.svelte'
import Login   from './pages/Login.svelte'
import Home    from './pages/Home.svelte'
import Music   from './pages/Music.svelte'
import Code    from './pages/Code.svelte'
import Life    from './pages/Life.svelte'
import Weather from './pages/Weather.svelte'
import Edit    from './pages/Edit.svelte'
import F1      from './pages/F1.svelte'
import Journal from './pages/Journal.svelte'
import Market  from './pages/Market.svelte'
import Sky     from './pages/Sky.svelte'
import Chat      from './pages/Chat.svelte'
import ChatStats from './pages/ChatStats.svelte'

let authed = !!sessionStorage.getItem('trellis_authed');
let authChecked = true;

let bgMedia = null, bgMediaType = null;
themeStore.subscribe(v => {
  bgMedia     = v.preset === 'custom' ? v.custom.bgMedia     : null;
  bgMediaType = v.preset === 'custom' ? v.custom.bgMediaType : null;
  document.documentElement.classList.toggle('has-wallpaper', !!bgMedia);
});

const routes = {
  '/':        Home,
  '/music':   Music,
  '/code':    Code,
  '/life':    Life,
  '/weather': Weather,
  '/edit':    Edit,
  '/f1':      F1,
  '/journal': Journal,
  '/market':  Market,
  '/sky':     Sky,
  '/chat':      Chat,
  '/chatstats': ChatStats,
}
</script>

{#if !authChecked}
  <!-- blank while session check runs -->
{:else if !authed}
  <Login on:authed={() => { sessionStorage.setItem('trellis_authed', '1'); authed = true; }} />
{:else}
  {#if bgMedia && bgMediaType === 'image'}
    <div class="wp-bg" style="background-image: url({bgMedia})" />
  {:else if bgMedia && bgMediaType === 'video'}
    <div class="wp-bg wp-vid-wrap">
      {#key bgMedia}
        <video class="wp-vid" src={bgMedia} autoplay loop muted playsinline
               on:canplay={e => e.target.play().catch(() => {})} />
      {/key}
    </div>
  {/if}
  <Router {routes} />
  <MobileNav />
{/if}

<style>
  .wp-bg {
    position: fixed;
    inset: 0;
    z-index: -10;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
  }

  .wp-vid-wrap {
    overflow: hidden;
  }

  .wp-vid {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  /* Rotate landscape wallpapers to fill portrait screen */
  @media (max-width: 768px) and (orientation: portrait) {
    .wp-bg {
      inset: auto;
      top: 50%;
      left: 50%;
      width: 100vh;
      height: 100vw;
      transform: translate(-50%, -50%) rotate(90deg);
      background-size: cover;
      background-position: center;
    }

    .wp-vid-wrap {
      overflow: visible;
    }
  }
</style>
