<script>
import Router from 'svelte-spa-router'
import { themeStore } from './lib/themeStore.js';
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

let bgMedia = null, bgMediaType = null;
themeStore.subscribe(v => {
  bgMedia     = v.preset === 'custom' ? v.custom.bgMedia     : null;
  bgMediaType = v.preset === 'custom' ? v.custom.bgMediaType : null;
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
}
</script>

{#if bgMedia && bgMediaType === 'image'}
  <div class="fixed inset-0 -z-10 bg-cover bg-center bg-no-repeat"
       style="background-image: url({bgMedia})" />
{:else if bgMedia && bgMediaType === 'video'}
  <div class="fixed inset-0 -z-10 overflow-hidden">
    <video src={bgMedia} autoplay loop muted playsinline
           class="w-full h-full object-cover" />
  </div>
{/if}

<Router {routes} />
