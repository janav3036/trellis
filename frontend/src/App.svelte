<script>
import Router from 'svelte-spa-router'
import Home from './pages/Home.svelte'
import Music from './pages/Music.svelte'
import Code from './pages/Code.svelte'
import Life from './pages/Life.svelte'
import Weather from './pages/Weather.svelte'
import Edit from './pages/Edit.svelte'
import F1 from './pages/F1.svelte'
import Journal from './pages/Journal.svelte'
import Market from './pages/Market.svelte'
import Sky from './pages/Sky.svelte'

const routes = {
  '/': Home,
  '/music': Music,
  '/code': Code,
  '/life': Life,
  '/weather': Weather,
  '/edit': Edit,
  '/f1': F1,
  '/journal': Journal,
  '/market': Market,
  '/sky': Sky,
}

</script>

<Router {routes} />