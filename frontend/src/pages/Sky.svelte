<script>
  import { onMount, onDestroy } from "svelte";
  import L from "leaflet";
  import "leaflet/dist/leaflet.css";

  let canvas;
  let mapEl;
  let map;
  let stars = [], constelLines = [];
  let observerLat = 40, observerLon = -74;
  let planes = [], planeMarkers = [];
  let apod = null, iss = null, neos = [];
  let starMapTimer, flightTimer, issTimer;

  const SPEC_COLORS = {
    O: "#9bb0ff", B: "#aabfff", A: "#e0e8ff",
    F: "#fff8f0", G: "#ffe8b0", K: "#ffd2a1", M: "#ff9966",
  };

  const D2R = Math.PI / 180;
  const R2D = 180 / Math.PI;

  function getLSTdeg(lonDeg) {
    const JD = Date.now() / 86400000 + 2440587.5;
    const GMST = 280.46061837 + 360.98564736629 * (JD - 2451545.0);
    return ((GMST + lonDeg) % 360 + 360) % 360;
  }

  function raDecToAltAz(raH, decDeg, latDeg, LSTdeg) {
    const H = ((LSTdeg - raH * 15) % 360 + 360) % 360 * D2R;
    const dec = decDeg * D2R, lat = latDeg * D2R;
    const sinAlt = Math.sin(dec) * Math.sin(lat) + Math.cos(dec) * Math.cos(lat) * Math.cos(H);
    const alt = Math.asin(Math.max(-1, Math.min(1, sinAlt)));
    const num = Math.sin(dec) - Math.sin(alt) * Math.sin(lat);
    const den = Math.cos(alt) * Math.cos(lat);
    let az = den === 0 ? 0 : Math.acos(Math.max(-1, Math.min(1, num / den)));
    if (Math.sin(H) > 0) az = 2 * Math.PI - az;
    return { alt: alt * R2D, az: az * R2D };
  }

  function drawStarMap() {
    if (!canvas || !stars.length) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    const cx = W / 2, cy = H / 2, R = Math.min(cx, cy) - 20;

    ctx.clearRect(0, 0, W, H);

    const bg = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
    bg.addColorStop(0, "#0c1220");
    bg.addColorStop(0.6, "#080c18");
    bg.addColorStop(1, "#040608");
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, 2 * Math.PI);
    ctx.clip();
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);
    ctx.restore();

    const LST = getLSTdeg(observerLon);

    const positioned = stars.map(s => {
      const { alt, az } = raDecToAltAz(s.ra, s.dec, observerLat, LST);
      const r = Math.max(0, (90 - alt) / 90) * R;
      const azR = az * D2R;
      return { ...s, alt, x: cx + r * Math.sin(azR), y: cy - r * Math.cos(azR) };
    });
    const byName = Object.fromEntries(positioned.map(s => [s.name, s]));

    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, 2 * Math.PI);
    ctx.clip();

    ctx.strokeStyle = "rgba(80, 110, 160, 0.3)";
    ctx.lineWidth = 0.7;
    for (const [a, b] of constelLines) {
      const sa = byName[a], sb = byName[b];
      if (!sa || !sb || sa.alt < 0 || sb.alt < 0) continue;
      ctx.beginPath();
      ctx.moveTo(sa.x, sa.y);
      ctx.lineTo(sb.x, sb.y);
      ctx.stroke();
    }

    for (const s of positioned) {
      if (s.alt < -5) continue;
      const color = SPEC_COLORS[s.spec] || "#e0e8ff";
      const radius = Math.max(0.7, 3.0 - s.mag * 0.7);
      if (s.mag < 1.5) {
        const grd = ctx.createRadialGradient(s.x, s.y, 0, s.x, s.y, radius * 4);
        grd.addColorStop(0, color + "88");
        grd.addColorStop(1, "transparent");
        ctx.beginPath();
        ctx.arc(s.x, s.y, radius * 4, 0, 2 * Math.PI);
        ctx.fillStyle = grd;
        ctx.fill();
      }
      ctx.beginPath();
      ctx.arc(s.x, s.y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
    }

    ctx.restore();

    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, 2 * Math.PI);
    ctx.strokeStyle = "rgba(80, 120, 90, 0.4)";
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.font = "bold 11px monospace";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    for (const [label, azDeg] of [["N", 0], ["E", 90], ["S", 180], ["W", 270]]) {
      const azR = azDeg * D2R;
      ctx.fillStyle = label === "N" ? "#c8813a" : "#6a7080";
      ctx.fillText(label, cx + (R + 16) * Math.sin(azR), cy - (R + 16) * Math.cos(azR));
    }

    ctx.font = "9px monospace";
    ctx.fillStyle = "#3a4050";
    ctx.textAlign = "right";
    ctx.fillText(new Date().toLocaleTimeString(), W - 6, H - 6);
  }

  function renderPlanes() {
    planeMarkers.forEach(m => m.remove());
    planeMarkers = [];
    if (!map) return;
    for (const p of planes) {
      if (p.on_ground) continue;
      const opacity = 0.25 + Math.min(0.75, (p.altitude || 0) / 12000);
      const m = L.circleMarker([p.lat, p.lon], {
        radius: 2.5,
        color: "#4dabf7",
        fillColor: "#4dabf7",
        fillOpacity: opacity,
        weight: 0,
      });
      if (p.callsign) m.bindTooltip(p.callsign, { permanent: false });
      m.addTo(map);
      planeMarkers.push(m);
    }
  }

  async function refreshFlights() {
    try {
      const r = await fetch("/api/sky/flights");
      if (!r.ok) return;
      planes = (await r.json()).planes;
      renderPlanes();
    } catch {}
  }

  onMount(async () => {
    const sRes = await fetch("/api/sky/stars");
    const sData = await sRes.json();
    stars = sData.stars;
    constelLines = sData.constellations;
    observerLat = sData.lat;
    observerLon = sData.lon;
    drawStarMap();
    starMapTimer = setInterval(drawStarMap, 30000);

    const fRes = await fetch("/api/sky/flights");
    const fData = await fRes.json();
    planes = fData.planes;
    map = L.map(mapEl, { zoomControl: false, attributionControl: false })
      .setView([fData.center_lat, fData.center_lon], 8);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      maxZoom: 14,
    }).addTo(map);
    renderPlanes();
    flightTimer = setInterval(refreshFlights, 15000);

    const [apodRes, issRes, neoRes] = await Promise.all([
      fetch("/api/sky/apod"),
      fetch("/api/sky/iss"),
      fetch("/api/sky/neo"),
    ]);
    if (apodRes.ok) apod = await apodRes.json();
    if (issRes.ok) iss = await issRes.json();
    if (neoRes.ok) neos = await neoRes.json();

    async function pollISS() {
      try {
        const r = await fetch("/api/sky/iss");
        if (r.ok) iss = await r.json();
      } catch {}
      issTimer = setTimeout(pollISS, 15000);
    }
    issTimer = setTimeout(pollISS, 15000);
  });

  onDestroy(() => {
    clearInterval(starMapTimer);
    clearInterval(flightTimer);
    clearTimeout(issTimer);
    map?.remove();
  });

  function fmtNum(n) {
    return n?.toLocaleString() ?? "—";
  }
</script>

<main class="p-6 min-h-screen" style="background:#1a1714; color:#e8e0d0">

  <h1 class="text-2xl font-semibold mb-5">Sky</h1>

  <div class="grid gap-4" style="grid-template-columns:repeat(10,1fr); grid-template-rows:580px 320px">

    <!-- Star Map: cols 1-6, row 1 -->
    <div class="rounded-2xl overflow-hidden relative"
         style="grid-column:1/7; grid-row:1; background:radial-gradient(ellipse at 50% 60%, #0d1220 0%, #070a10 60%, #030507 100%); border:1px solid #141828">
      <div class="absolute top-4 left-5 z-10">
        <div class="text-[11px] font-medium uppercase tracking-widest" style="color:#3a4460">Star Map</div>
        <div class="text-[10px] mt-0.5 font-mono" style="color:#2a3040">{observerLat.toFixed(2)}° {observerLon.toFixed(2)}°</div>
      </div>
      <div class="w-full h-full flex items-center justify-center p-4 pt-10">
        {#if stars.length}
          <canvas bind:this={canvas} width="520" height="520" class="block max-w-full max-h-full" />
        {:else}
          <div class="text-sm animate-pulse" style="color:#2a3040">Loading sky…</div>
        {/if}
      </div>
    </div>

    <!-- Flight Radar: cols 7-10, row 1 -->
    <div class="rounded-2xl flex flex-col overflow-hidden"
         style="grid-column:7/11; grid-row:1; background:#0c0e14; border:1px solid #141828">
      <div class="px-5 pt-4 pb-2 shrink-0">
        <div class="text-[11px] font-medium uppercase tracking-widest" style="color:#3a4460">Flight Radar</div>
        <div class="text-[10px] mt-0.5" style="color:#2a3040">
          {planes.filter(p => !p.on_ground).length} airborne · updates every 15s
        </div>
      </div>
      <div bind:this={mapEl} class="flex-1" style="min-height:0"></div>
    </div>

    <!-- APOD: cols 1-5, row 2 -->
    <div class="rounded-2xl overflow-hidden flex flex-col"
         style="grid-column:1/6; grid-row:2; background:#1c1b17; border:1px solid #2a2823">
      {#if apod}
        {#if apod.media_type === "image"}
          <div class="flex h-full">
            <img src={apod.url} alt={apod.title} class="w-48 shrink-0 object-cover" />
            <div class="flex flex-col p-5 min-w-0">
              <div class="text-[11px] font-medium uppercase tracking-widest mb-2" style="color:#6a6058">Astronomy Picture of the Day</div>
              <div class="text-sm font-medium mb-2 leading-snug">{apod.title}</div>
              <div class="text-xs leading-relaxed flex-1 overflow-hidden" style="color:#9a9080; display:-webkit-box; -webkit-line-clamp:6; -webkit-box-orient:vertical">{apod.explanation}</div>
              <div class="text-[10px] mt-3" style="color:#6a6058">{apod.date}</div>
            </div>
          </div>
        {:else}
          <div class="flex flex-col p-5 h-full">
            <div class="text-[11px] font-medium uppercase tracking-widest mb-2" style="color:#6a6058">Astronomy Picture of the Day</div>
            <div class="text-sm font-medium mb-1">{apod.title}</div>
            <div class="text-xs" style="color:#9a9080">Video · {apod.date}</div>
          </div>
        {/if}
      {:else}
        <div class="flex-1 flex items-center justify-center text-sm animate-pulse p-5" style="color:#9a9080">Loading…</div>
      {/if}
    </div>

    <!-- ISS: cols 6-8, row 2 -->
    <div class="rounded-2xl p-5 flex flex-col"
         style="grid-column:6/9; grid-row:2; background:#1c1b17; border:1px solid #2a2823">
      <div class="flex items-center justify-between mb-4 shrink-0">
        <div class="text-[11px] font-medium uppercase tracking-widest" style="color:#6a6058">ISS</div>
        <div class="flex items-center gap-1.5">
          <span class="w-1.5 h-1.5 rounded-full animate-pulse" style="background:#4dabf7"></span>
          <span class="text-[10px]" style="color:#4dabf7">Live</span>
        </div>
      </div>
      {#if iss}
        <div class="grid grid-cols-2 gap-2 flex-1">
          {#each [
            { label: "Latitude", value: `${iss.lat.toFixed(2)}°` },
            { label: "Longitude", value: `${iss.lon.toFixed(2)}°` },
            { label: "Altitude", value: `${iss.altitude_km} km` },
            { label: "Speed", value: `${fmtNum(iss.velocity_kmh)} km/h` },
          ] as stat}
            <div class="rounded-xl p-3" style="background:#151411">
              <div class="text-[10px] uppercase tracking-wider mb-1.5" style="color:#6a6058">{stat.label}</div>
              <div class="text-sm font-medium font-mono tabular-nums">{stat.value}</div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="flex-1 flex items-center justify-center text-sm animate-pulse" style="color:#9a9080">Loading…</div>
      {/if}
    </div>

    <!-- NEOs: cols 9-10, row 2 -->
    <div class="rounded-2xl p-5 flex flex-col"
         style="grid-column:9/11; grid-row:2; background:#1c1b17; border:1px solid #2a2823">
      <div class="text-[11px] font-medium uppercase tracking-widest mb-3 shrink-0" style="color:#6a6058">
        Near-Earth Objects · 7d
      </div>
      {#if neos.length}
        <div class="flex flex-col gap-2 flex-1 overflow-y-auto">
          {#each neos.slice(0, 8) as neo}
            <div class="flex items-start gap-2 text-xs py-1.5" style="border-bottom:1px solid #252320">
              {#if neo.hazardous}
                <span style="color:#c87a7a" class="shrink-0">⚠</span>
              {:else}
                <span style="color:#3a3530" class="shrink-0">·</span>
              {/if}
              <div class="flex-1 min-w-0">
                <div class="truncate">{neo.name}</div>
                <div class="tabular-nums mt-0.5" style="color:#9a9080">{fmtNum(neo.miss_km)} km</div>
              </div>
              <div class="shrink-0 text-right" style="color:#6a6058">{neo.date}</div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="flex-1 flex items-center justify-center text-sm animate-pulse" style="color:#9a9080">Loading…</div>
      {/if}
    </div>

  </div>

</main>

<style>
  :global(.leaflet-tooltip) {
    background: #0c0e14;
    border: 1px solid #1a1f2e;
    color: #6a7080;
    font-size: 10px;
    padding: 2px 6px;
    box-shadow: none;
  }
</style>
