<script>
import Router from 'svelte-spa-router'
import Home from './pages/Home.svelte'
import Music from './pages/Music.svelte'
import Code from './pages/Code.svelte'
import Life from './pages/Life.svelte'
import Weather from './pages/Weather.svelte'

const routes = {
  '/': Home,
  '/music': Music,
  '/code': Code,
  '/life': Life,
  '/weather': Weather,
}

</script>

<Router {routes} />