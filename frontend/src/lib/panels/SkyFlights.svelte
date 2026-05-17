<script>
  import { onMount, onDestroy } from 'svelte';
  import L from 'leaflet';
  import 'leaflet/dist/leaflet.css';

  let mapEl, map, planes=[], markers=[], flightTimer, issTimer, iss=null;

  function renderPlanes() {
    markers.forEach(m => m.remove()); markers=[];
    if (!map) return;
    for (const p of planes) {
      if (p.on_ground) continue;
      const opacity = 0.25+Math.min(0.75,(p.altitude||0)/12000);
      const m = L.circleMarker([p.lat,p.lon],{radius:2.5,color:'#4dabf7',fillColor:'#4dabf7',fillOpacity:opacity,weight:0});
      if (p.callsign) m.bindTooltip(p.callsign,{permanent:false});
      m.addTo(map); markers.push(m);
    }
  }

  async function refreshFlights() {
    try {
      const r=await fetch('/api/sky/flights'); if(!r.ok) return;
      planes=(await r.json()).planes; renderPlanes();
    } catch {}
  }

  async function pollISS() {
    try { const r=await fetch('/api/sky/iss'); if(r.ok) iss=await r.json(); } catch {}
    issTimer=setTimeout(pollISS,15000);
  }

  function fmtNum(n) { return n?.toLocaleString()??'—'; }

  onMount(async () => {
    const r=await fetch('/api/sky/flights');
    const data=await r.json();
    planes=data.planes;
    map=L.map(mapEl,{zoomControl:false,attributionControl:false}).setView([data.center_lat,data.center_lon],8);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{maxZoom:14}).addTo(map);
    renderPlanes();
    flightTimer=setInterval(refreshFlights,15000);
    pollISS();
  });
  onDestroy(() => {
    clearInterval(flightTimer); clearTimeout(issTimer); map?.remove();
  });
</script>

<div class="flex flex-col gap-4 w-full">
  <div class="bg-[#242019] rounded-xl p-4">
    <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">
      Flight Radar · {planes.filter(p=>!p.on_ground).length} airborne
    </div>
    <div bind:this={mapEl} class="w-full rounded-lg overflow-hidden" style="height:320px"></div>
  </div>

  {#if iss}
    <div class="bg-[#242019] rounded-xl p-4">
      <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">ISS · Live</div>
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div><div class="text-[#9a9080] text-xs">Position</div>
          <div class="font-mono tabular-nums">{iss.lat.toFixed(2)}° {iss.lon.toFixed(2)}°</div></div>
        <div><div class="text-[#9a9080] text-xs">Altitude</div>
          <div class="font-mono tabular-nums">{iss.altitude_km} km</div></div>
        <div><div class="text-[#9a9080] text-xs">Speed</div>
          <div class="font-mono tabular-nums">{fmtNum(iss.velocity_kmh)} km/h</div></div>
        <div><div class="text-[#9a9080] text-xs">Visibility</div>
          <div class="capitalize">{iss.visibility||'—'}</div></div>
      </div>
    </div>
  {/if}
</div>
