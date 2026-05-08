<script>
import { onMount } from 'svelte'

const today = new Date().toISOString().split('T')[0]

let music = 0 
let code = 0
let life = 0
let weather = null

onMount(async () => {
    const [mRes, cRes, lRes, wRes] = await Promise.all([
        fetch(`/api/events?source=spotify&date_from=${today}`),
        fetch(`/api/events?source=github&event_type=commit&date_from=${today}`),
        fetch(`/api/events?source=calendar&date_from=${today}`),
        fetch(`/api/events?source=weather&date_from=${today}`)
    ])

    const [m, c, l, w] = await Promise.all([
        mRes.json(), cRes.json(), lRes.json(), wRes.json()
    ])

    music = m.length
    code = c.length
    life = l.length
    weather = w[0] ?? null
})
</script>
<main class="p-8 bg-[#1a1714] min-h-screen text-[#e8e0d0]">
  <h1 class="text-3xl font-semibold mb-8">Trellis</h1>

  <div class="grid grid-cols-2 gap-4 max-w-xl">

    <a href="/#/music" class="block p-6 rounded-xl bg-[#242019] hover:bg-[#2e2a1f]">
      <div class="text-sm text-[#9a9080] mb-1">Music</div>
      <div class="text-2xl font-bold text-[#c8813a]">{music}</div>
      <div class="text-xs text-[#9a9080] mt-1">plays today</div>
    </a>

    <a href="/#/code" class="block p-6 rounded-xl bg-[#242019] hover:bg-[#2e2a1f]">
      <div class="text-sm text-[#9a9080] mb-1">Code</div>
      <div class="text-2xl font-bold text-[#6b8c6b]">{code}</div>
      <div class="text-xs text-[#9a9080] mt-1">commits today</div>
    </a>

    <a href="/#/life" class="block p-6 rounded-xl bg-[#242019] hover:bg-[#2e2a1f]">
      <div class="text-sm text-[#9a9080] mb-1">Life</div>
      <div class="text-2xl font-bold text-[#7a9ab0]">{life}</div>
      <div class="text-xs text-[#9a9080] mt-1">events today</div>
    </a>

    <a href="/#/weather" class="block p-6 rounded-xl bg-[#242019] hover:bg-[#2e2a1f]">
      <div class="text-sm text-[#9a9080] mb-1">Weather</div>
      {#if weather}
        <div class="text-2xl font-bold text-[#b0956b]">{weather.metadata.temp_max}°</div>
        <div class="text-xs text-[#9a9080] mt-1">high today</div>
      {:else}
        <div class="text-2xl font-bold text-[#9a9080]">—</div>
        <div class="text-xs text-[#9a9080] mt-1">no data yet</div>
      {/if}
    </a>

  </div>
</main>
    