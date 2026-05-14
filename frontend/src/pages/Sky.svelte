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

<main class="p-8 bg-[#1a1714] min-h-screen text-[#e8e0d0]">

  <h1 class="text-3xl font-semibold mb-8">Sky</h1>

  <!-- Star Map -->
  <div class="bg-[#242019] rounded-xl p-4 mb-6">
    <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">
      Star Map · Real-time · {observerLat.toFixed(2)}° {observerLon.toFixed(2)}°
    </h2>
    <div class="flex justify-center">
      {#if stars.length}
        <canvas bind:this={canvas} width="560" height="560" />
      {:else}
        <div class="w-[560px] h-[560px] flex items-center justify-center text-[#9a9080] text-sm animate-pulse">
          Loading sky…
        </div>
      {/if}
    </div>
  </div>

  <!-- Flight Radar + Space Events -->
  <div class="grid grid-cols-2 gap-6">

    <!-- Flight Radar -->
    <div class="bg-[#242019] rounded-xl p-4">
      <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">
        Flight Radar · {planes.filter(p => !p.on_ground).length} airborne · 15s
      </h2>
      <div bind:this={mapEl} class="w-full rounded-lg overflow-hidden" style="height:340px"></div>
    </div>

    <!-- Space Events -->
    <div class="flex flex-col gap-4">

      <!-- APOD -->
      <div class="bg-[#242019] rounded-xl p-4">
        <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Astronomy Picture of the Day</h2>
        {#if apod}
          {#if apod.media_type === "image"}
            <div class="flex gap-3">
              <img src={apod.url} alt={apod.title} class="w-28 h-20 object-cover rounded-lg flex-shrink-0" />
              <div>
                <div class="text-sm font-medium mb-1">{apod.title}</div>
                <div class="text-xs text-[#9a9080] leading-relaxed line-clamp-3">{apod.explanation}</div>
              </div>
            </div>
          {:else}
            <div class="text-sm font-medium">{apod.title}</div>
            <div class="text-xs text-[#9a9080] mt-1">Video · {apod.date}</div>
          {/if}
        {:else}
          <div class="h-20 flex items-center justify-center text-[#9a9080] text-sm animate-pulse">Loading…</div>
        {/if}
      </div>

      <!-- ISS -->
      <div class="bg-[#242019] rounded-xl p-4">
        <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">ISS · Live</h2>
        {#if iss}
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div>
              <div class="text-[#9a9080] text-xs">Position</div>
              <div class="font-mono tabular-nums">{iss.lat.toFixed(2)}° {iss.lon.toFixed(2)}°</div>
            </div>
            <div>
              <div class="text-[#9a9080] text-xs">Altitude</div>
              <div class="font-mono tabular-nums">{iss.altitude_km} km</div>
            </div>
            <div>
              <div class="text-[#9a9080] text-xs">Speed</div>
              <div class="font-mono tabular-nums">{fmtNum(iss.velocity_kmh)} km/h</div>
            </div>
            <div>
              <div class="text-[#9a9080] text-xs">Visibility</div>
              <div class="capitalize">{iss.visibility || "—"}</div>
            </div>
          </div>
        {:else}
          <div class="h-16 flex items-center justify-center text-[#9a9080] text-sm animate-pulse">Loading…</div>
        {/if}
      </div>

      <!-- NEO -->
      <div class="bg-[#242019] rounded-xl p-4 flex-1">
        <h2 class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">Near-Earth Objects · Next 7 Days</h2>
        {#if neos.length}
          <div class="space-y-1.5">
            {#each neos.slice(0, 5) as neo}
              <div class="flex items-center gap-2 text-xs">
                {#if neo.hazardous}
                  <span class="text-[#ff6b6b]">⚠</span>
                {:else}
                  <span class="text-[#3a3530]">·</span>
                {/if}
                <span class="flex-1 truncate">{neo.name}</span>
                <span class="text-[#9a9080] tabular-nums">{neo.date}</span>
                <span class="text-[#9a9080] tabular-nums w-24 text-right">{fmtNum(neo.miss_km)} km</span>
              </div>
            {/each}
          </div>
        {:else}
          <div class="h-16 flex items-center justify-center text-[#9a9080] text-sm animate-pulse">Loading…</div>
        {/if}
      </div>

    </div>
  </div>

</main>

<style>
  :global(.leaflet-tooltip) {
    background: #1a1714;
    border: 1px solid #3a3530;
    color: #9a9080;
    font-size: 10px;
    padding: 2px 6px;
    box-shadow: none;
  }
</style>
