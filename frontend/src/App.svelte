<script>
import Router from 'svelte-spa-router'
import { themeStore } from './lib/themeStore.js';
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
import Chat    from './pages/Chat.svelte'

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
  '/chat':    Chat,
}
</script>

{#if !authChecked}
  <!-- blank while session check runs -->
{:else if !authed}
  <Login on:authed={() => { sessionStorage.setItem('trellis_authed', '1'); authed = true; }} />
{:else}
  {#if bgMedia && bgMediaType === 'image'}
    <div class="fixed inset-0 -z-10 bg-cover bg-center bg-no-repeat"
         style="background-image: url({bgMedia})" />
  {:else if bgMedia && bgMediaType === 'video'}
    <div class="fixed inset-0 -z-10 overflow-hidden">
      {#key bgMedia}
        <video src={bgMedia} autoplay loop muted playsinline
               class="w-full h-full object-cover"
               on:canplay={e => e.target.play().catch(() => {})} />
      {/key}
    </div>
  {/if}
  <Router {routes} />
{/if}
