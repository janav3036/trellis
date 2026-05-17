<script>
  import { onMount, onDestroy } from 'svelte';
  let canvas, stars=[], constelLines=[], observerLat=40, observerLon=-74, timer;

  const SPEC_COLORS = { O:'#9bb0ff',B:'#aabfff',A:'#e0e8ff',F:'#fff8f0',G:'#ffe8b0',K:'#ffd2a1',M:'#ff9966' };
  const D2R = Math.PI/180, R2D = 180/Math.PI;

  function getLSTdeg(lonDeg) {
    const JD = Date.now()/86400000+2440587.5;
    const GMST = 280.46061837+360.98564736629*(JD-2451545.0);
    return ((GMST+lonDeg)%360+360)%360;
  }
  function raDecToAltAz(raH,decDeg,latDeg,LSTdeg) {
    const H = ((LSTdeg-raH*15)%360+360)%360*D2R;
    const dec=decDeg*D2R, lat=latDeg*D2R;
    const sinAlt = Math.sin(dec)*Math.sin(lat)+Math.cos(dec)*Math.cos(lat)*Math.cos(H);
    const alt = Math.asin(Math.max(-1,Math.min(1,sinAlt)));
    const num = Math.sin(dec)-Math.sin(alt)*Math.sin(lat);
    const den = Math.cos(alt)*Math.cos(lat);
    let az = den===0?0:Math.acos(Math.max(-1,Math.min(1,num/den)));
    if (Math.sin(H)>0) az = 2*Math.PI-az;
    return { alt:alt*R2D, az:az*R2D };
  }

  function drawStarMap() {
    if (!canvas||!stars.length) return;
    const ctx=canvas.getContext('2d'), W=canvas.width, H=canvas.height;
    const cx=W/2, cy=H/2, R=Math.min(cx,cy)-20;
    ctx.clearRect(0,0,W,H);
    const bg=ctx.createRadialGradient(cx,cy,0,cx,cy,R);
    bg.addColorStop(0,'#0c1220'); bg.addColorStop(0.6,'#080c18'); bg.addColorStop(1,'#040608');
    ctx.save(); ctx.beginPath(); ctx.arc(cx,cy,R,0,2*Math.PI); ctx.clip();
    ctx.fillStyle=bg; ctx.fillRect(0,0,W,H); ctx.restore();
    const LST=getLSTdeg(observerLon);
    const positioned=stars.map(s=>{
      const {alt,az}=raDecToAltAz(s.ra,s.dec,observerLat,LST);
      const r=Math.max(0,(90-alt)/90)*R, azR=az*D2R;
      return {...s,alt,x:cx+r*Math.sin(azR),y:cy-r*Math.cos(azR)};
    });
    const byName=Object.fromEntries(positioned.map(s=>[s.name,s]));
    ctx.save(); ctx.beginPath(); ctx.arc(cx,cy,R,0,2*Math.PI); ctx.clip();
    ctx.strokeStyle='rgba(80,110,160,0.3)'; ctx.lineWidth=0.7;
    for (const [a,b] of constelLines) {
      const sa=byName[a],sb=byName[b];
      if (!sa||!sb||sa.alt<0||sb.alt<0) continue;
      ctx.beginPath(); ctx.moveTo(sa.x,sa.y); ctx.lineTo(sb.x,sb.y); ctx.stroke();
    }
    for (const s of positioned) {
      if (s.alt<-5) continue;
      const color=SPEC_COLORS[s.spec]||'#e0e8ff';
      const radius=Math.max(0.7,3.0-s.mag*0.7);
      if (s.mag<1.5) {
        const grd=ctx.createRadialGradient(s.x,s.y,0,s.x,s.y,radius*4);
        grd.addColorStop(0,color+'88'); grd.addColorStop(1,'transparent');
        ctx.beginPath(); ctx.arc(s.x,s.y,radius*4,0,2*Math.PI); ctx.fillStyle=grd; ctx.fill();
      }
      ctx.beginPath(); ctx.arc(s.x,s.y,radius,0,2*Math.PI); ctx.fillStyle=color; ctx.fill();
    }
    ctx.restore();
    ctx.beginPath(); ctx.arc(cx,cy,R,0,2*Math.PI);
    ctx.strokeStyle='rgba(80,120,90,0.4)'; ctx.lineWidth=2; ctx.stroke();
    ctx.font='bold 11px monospace'; ctx.textAlign='center'; ctx.textBaseline='middle';
    for (const [label,azDeg] of [['N',0],['E',90],['S',180],['W',270]]) {
      const azR=azDeg*D2R;
      ctx.fillStyle=label==='N'?'#c8813a':'#6a7080';
      ctx.fillText(label,cx+(R+16)*Math.sin(azR),cy-(R+16)*Math.cos(azR));
    }
  }

  onMount(async () => {
    const r = await fetch('/api/sky/stars');
    const data = await r.json();
    stars=data.stars; constelLines=data.constellations; observerLat=data.lat; observerLon=data.lon;
    drawStarMap();
    timer = setInterval(drawStarMap, 30000);
  });
  onDestroy(() => clearInterval(timer));
</script>

<div class="bg-[#242019] rounded-xl p-4">
  <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider mb-3">
    Star Map · {observerLat.toFixed(2)}° {observerLon.toFixed(2)}°
  </div>
  <div class="flex justify-center">
    {#if stars.length}
      <canvas bind:this={canvas} width="480" height="480"></canvas>
    {:else}
      <div class="w-[480px] h-[480px] flex items-center justify-center text-[#9a9080] text-sm animate-pulse">Loading sky…</div>
    {/if}
  </div>
</div>
