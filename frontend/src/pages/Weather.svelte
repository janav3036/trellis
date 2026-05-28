<script>
    import { onMount } from "svelte";
    import Plotly from "plotly.js-dist-min";
    import { daysAgoIST } from "../lib/ist.js";

    let chartEl;
    let range = "30d";
    let days = [];
    let backfillDate = "";
    let backfillStatus = "";
    let forecast = [];

    function weatherIcon(code) {
        if (code === 0) return "☀";
        if (code <= 1) return "🌤";
        if (code <= 3) return "⛅";
        if (code <= 48) return "🌫";
        if (code <= 57) return "🌦";
        if (code <= 67) return "🌧";
        if (code <= 77) return "❄";
        if (code <= 82) return "🌦";
        if (code <= 86) return "🌨";
        return "⛈";
    }

    function weatherLabel(code) {
        if (code === 0) return "Clear sky";
        if (code <= 3) return "Partly cloudy";
        if (code <= 48) return "Fog";
        if (code <= 57) return "Drizzle";
        if (code <= 67) return "Rain";
        if (code <= 77) return "Snow";
        if (code <= 82) return "Rain showers";
        if (code <= 86) return "Snow showers";
        return "Thunderstorm";
    }

    function uvInfo(uv) {
        if (uv <= 2) return { label: "Low", color: "#4a9b6b" };
        if (uv <= 5) return { label: "Moderate", color: "#c8a941" };
        if (uv <= 7) return { label: "High", color: "#c87941" };
        if (uv <= 10) return { label: "Very High", color: "#c85a41" };
        return { label: "Extreme", color: "#9b41c8" };
    }

    function tempColor(t) {
        const clamped = Math.max(0, Math.min(35, t));
        const ratio = clamped / 35;
        const r = Math.round(60 + ratio * 160);
        const g = Math.round(80 + ratio * 60);
        const b = Math.round(160 - ratio * 120);
        return `rgb(${r},${g},${b})`;
    }

    function tempColorAlpha(t, alpha) {
        const clamped = Math.max(0, Math.min(35, t));
        const ratio = clamped / 35;
        const r = Math.round(60 + ratio * 160);
        const g = Math.round(80 + ratio * 60);
        const b = Math.round(160 - ratio * 120);
        return `rgba(${r},${g},${b},${alpha})`;
    }

    function fmtTime(isoStr) {
        if (!isoStr) return "--";
        const timePart = isoStr.split("T")[1];
        if (!timePart) return "--";
        const [h, m] = timePart.split(":").map(Number);
        const period = h >= 12 ? "PM" : "AM";
        const h12 = h % 12 || 12;
        return `${h12}:${String(m).padStart(2, "0")} ${period}`;
    }

    const RANGES = [
        { key: "30d", label: "30d", n: 30 },
        { key: "90d", label: "90d", n: 90 },
        { key: "180d", label: "180d", n: 180 },
    ];

    async function loadChart(r) {
        range = r.key;
        const res = await fetch(
            `/api/events?source=weather&event_type=daily&date_from=${daysAgoIST(r.n)}`,
        );
        const events = await res.json();
        const x = events.map((e) => e.timestamp.split("T")[0]).reverse();
        const yMax = events.map((e) => e.metadata.temp_max).reverse();
        const yMin = events.map((e) => e.metadata.temp_min).reverse();
        const precip = events.map((e) => e.metadata.precipitation).reverse();

        Plotly.react(
            chartEl,
            [
                {
                    x, y: yMax, name: "High",
                    type: "scatter", mode: "lines",
                    line: { color: "#c87941", width: 2 },
                },
                {
                    x, y: yMin, name: "Low",
                    type: "scatter", mode: "lines",
                    line: { color: "#6b9ecc", width: 2 },
                },
                {
                    x, y: precip, name: "Precip",
                    type: "bar", yaxis: "y2",
                    marker: { color: "#4a7a9b", opacity: 0.4 },
                },
            ],
            {
                paper_bgcolor: "#1c1b17",
                plot_bgcolor: "#1c1b17",
                font: { color: "#e8e0d0", family: "system-ui, sans-serif", size: 11 },
                xaxis: { gridcolor: "#252320", tickcolor: "#9a9080" },
                yaxis: { gridcolor: "#252320", tickcolor: "#9a9080", title: "°C" },
                yaxis2: { overlaying: "y", side: "right", title: "mm", showgrid: false },
                legend: { bgcolor: "transparent" },
                margin: { t: 16, r: 55, b: 50, l: 45 },
            },
            { responsive: true },
        );
    }

    $: today = forecast.length ? forecast[0] : null;

    $: stats = (() => {
        if (!days.length) return null;
        const now = new Date();
        const thisMonth = days.filter((d) => {
            const t = new Date(d.timestamp);
            return t.getMonth() === now.getMonth() && t.getFullYear() === now.getFullYear();
        });
        const hottest = [...days].sort((a, b) => b.metadata.temp_max - a.metadata.temp_max)[0];
        const coldest = [...days].sort((a, b) => a.metadata.temp_min - b.metadata.temp_min)[0];
        const rainiest = [...days].sort((a, b) => b.metadata.precipitation - a.metadata.precipitation)[0];

        let maxDry = 0, curDry = 0;
        for (const d of days) {
            if ((d.metadata.precipitation || 0) < 1) { curDry++; maxDry = Math.max(maxDry, curDry); }
            else curDry = 0;
        }

        const avgHigh = thisMonth.length
            ? Math.round(thisMonth.reduce((s, d) => s + d.metadata.temp_max, 0) / thisMonth.length)
            : null;
        const totalRain = thisMonth.reduce((s, d) => s + (d.metadata.precipitation || 0), 0).toFixed(1);

        return { hottest, coldest, rainiest, maxDry, avgHigh, totalRain };
    })();

    $: precipDays = days.slice(-30);
    $: maxPrecip = precipDays.length
        ? Math.max(...precipDays.map((d) => d.metadata.precipitation || 0), 0.1)
        : 1;
    $: totalPrecip30 = precipDays.reduce((s, d) => s + (d.metadata.precipitation || 0), 0).toFixed(1);
    $: rainyDays30 = precipDays.filter((d) => (d.metadata.precipitation || 0) >= 1).length;

    $: monthGroups = (() => {
        const groups = {};
        for (const d of days) {
            const key = new Date(d.timestamp).toLocaleDateString("en-US", { month: "long", year: "numeric" });
            if (!groups[key]) groups[key] = [];
            groups[key].push(d);
        }
        return Object.entries(groups).map(([month, mDays]) => ({
            month,
            days: mDays,
            offset: new Date(mDays[0].timestamp).getDay(),
        }));
    })();

    onMount(async () => {
        const [calRes, forecastRes] = await Promise.all([
            fetch(`/api/events?source=weather&event_type=daily&date_from=${daysAgoIST(89)}`),
            fetch("/api/weather/forecast"),
            loadChart(RANGES[0]),
        ]);
        days = (await calRes.json()).reverse();
        forecast = await forecastRes.json();
    });
</script>

<main class="min-h-screen p-6" style="background:#13120f; color:#e8e0d0; font-family:system-ui,sans-serif">

    <!-- Header -->
    <div class="flex items-center justify-between mb-5">
        <h1 class="text-2xl font-semibold tracking-tight">Weather</h1>
        <div class="flex items-center gap-2">
            <input
                type="date"
                bind:value={backfillDate}
                class="rounded-lg px-3 py-1.5 text-sm border"
                style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823"
            />
            <button
                on:click={async () => {
                    if (!backfillDate) return;
                    backfillStatus = "running…";
                    const res = await fetch("/api/backfill/weather", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ date_from: backfillDate }),
                    });
                    const data = await res.json();
                    backfillStatus = `${data.count} days loaded`;
                    days = (
                        await (
                            await fetch(`/api/events?source=weather&event_type=daily&date_from=${daysAgoIST(89)}`)
                        ).json()
                    ).reverse();
                }}
                class="px-3 py-1.5 rounded-lg text-sm font-medium"
                style="background:#2a4a2a; color:#a8d0a8; border:1px solid #3a5a3a"
            >Backfill</button>
            {#if backfillStatus}
                <span class="text-sm" style="color:#9a9080">{backfillStatus}</span>
            {/if}
        </div>
    </div>

    <!-- Top bento: Today + 14-day forecast -->
    <div class="grid gap-4 mb-4" style="grid-template-columns: 300px 1fr">

        <!-- Today card -->
        {#if today}
            {@const m = today.metadata}
            {@const uv = uvInfo(m.uv_index || 0)}
            <div class="rounded-2xl p-5 flex flex-col" style="background:#1c1b17; border:1px solid #2a2823">
                <div class="text-xs mb-4" style="color:#9a9080">
                    {new Date(today.timestamp).toLocaleDateString("en-US", {
                        weekday: "long", month: "long", day: "numeric",
                    })}
                </div>

                <div class="text-6xl font-semibold mb-1 leading-none" style="color:{tempColor(m.temp_max)}">
                    {Math.round(m.temp_max)}°
                </div>
                <div class="text-sm mb-3" style="color:#9a9080">
                    Feels like {m.feels_like_max != null ? Math.round(m.feels_like_max) + "°" : "--"}
                </div>

                <div class="flex items-center gap-2 mb-5">
                    <span class="text-2xl leading-none">{weatherIcon(m.weathercode)}</span>
                    <span class="text-sm font-medium">{weatherLabel(m.weathercode)}</span>
                </div>

                <div class="grid grid-cols-2 gap-2 mb-4">
                    {#each [
                        { label: "Wind", value: Math.round(m.windspeed_max) + " km/h" },
                        { label: "Gusts", value: m.windgusts_max != null ? Math.round(m.windgusts_max) + " km/h" : "--" },
                        { label: "Rain", value: (m.precipitation ?? 0) + " mm" },
                        { label: "Low", value: Math.round(m.temp_min) + "°", color: tempColor(m.temp_min) },
                    ] as stat}
                        <div class="rounded-xl p-3" style="background:#151411">
                            <div class="text-[10px] uppercase tracking-wider mb-1" style="color:#6a6058">{stat.label}</div>
                            <div class="text-sm font-medium" style="color:{stat.color || '#e8e0d0'}">{stat.value}</div>
                        </div>
                    {/each}
                </div>

                {#if m.uv_index != null}
                    <div class="mb-4">
                        <div class="flex justify-between text-[10px] mb-1.5" style="color:#9a9080">
                            <span>UV Index</span>
                            <span style="color:{uv.color}">{uv.label} · {Math.round(m.uv_index)}</span>
                        </div>
                        <div class="h-1.5 rounded-full overflow-hidden" style="background:#252320">
                            <div class="h-full rounded-full"
                                style="width:{Math.min(100, (m.uv_index / 12) * 100)}%; background:{uv.color}"></div>
                        </div>
                    </div>
                {/if}

                {#if m.sunrise && m.sunset}
                    <div class="flex gap-6 mt-auto pt-4" style="border-top:1px solid #252320">
                        <div>
                            <div class="text-[10px] mb-0.5" style="color:#6a6058">Sunrise</div>
                            <div class="text-sm">{fmtTime(m.sunrise)}</div>
                        </div>
                        <div>
                            <div class="text-[10px] mb-0.5" style="color:#6a6058">Sunset</div>
                            <div class="text-sm">{fmtTime(m.sunset)}</div>
                        </div>
                    </div>
                {/if}
            </div>
        {:else}
            <div class="rounded-2xl" style="background:#1c1b17; border:1px solid #2a2823"></div>
        {/if}

        <!-- 14-day forecast -->
        <div class="rounded-2xl p-5" style="background:#1c1b17; border:1px solid #2a2823">
            <div class="text-[11px] font-medium uppercase tracking-widest mb-4" style="color:#6a6058">14-Day Forecast</div>
            <div class="grid grid-cols-7 gap-2">
                {#each forecast.slice(0, 14) as d, i}
                    {@const m = d.metadata}
                    <div
                        class="rounded-xl p-2.5 flex flex-col items-center gap-1 text-center"
                        style="background:{i === 0 ? tempColorAlpha(m.temp_max, 0.14) : '#151411'};
                               border:1px solid {i === 0 ? tempColorAlpha(m.temp_max, 0.28) : 'transparent'}"
                    >
                        <div class="text-[10px] font-semibold" style="color:{i === 0 ? '#e8e0d0' : '#9a9080'}">
                            {i === 0 ? "Today" : new Date(d.timestamp).toLocaleDateString("en-US", { weekday: "short" })}
                        </div>
                        <div class="text-[9px]" style="color:#6a6058">
                            {new Date(d.timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                        </div>
                        <div class="text-lg leading-none my-0.5">{weatherIcon(m.weathercode)}</div>
                        <div class="text-sm font-semibold" style="color:{tempColor(m.temp_max)}">{Math.round(m.temp_max)}°</div>
                        <div class="text-[10px]" style="color:#6a6058">{Math.round(m.temp_min)}°</div>
                        {#if (m.precipitation || 0) > 1}
                            <div class="text-[9px]" style="color:#6b9ecc">{m.precipitation}mm</div>
                        {/if}
                    </div>
                {/each}
            </div>
        </div>
    </div>

    <!-- Stats strip -->
    {#if stats}
        {@const statCards = [
            { label: "Avg High · Month", value: stats.avgHigh != null ? stats.avgHigh + "°" : "--", sub: "this month" },
            { label: "Total Rain · Month", value: stats.totalRain + " mm", sub: "this month" },
            { label: "Hottest Day", value: Math.round(stats.hottest.metadata.temp_max) + "°", sub: new Date(stats.hottest.timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" }) },
            { label: "Coldest Day", value: Math.round(stats.coldest.metadata.temp_min) + "°", sub: new Date(stats.coldest.timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" }) },
            { label: "Rainiest Day", value: stats.rainiest.metadata.precipitation + " mm", sub: new Date(stats.rainiest.timestamp).toLocaleDateString("en-US", { month: "short", day: "numeric" }) },
            { label: "Dry Streak", value: stats.maxDry + " days", sub: "longest in 90d" },
        ]}
        <div class="grid grid-cols-6 gap-3 mb-4">
            {#each statCards as s}
                <div class="rounded-xl p-4" style="background:#1c1b17; border:1px solid #2a2823">
                    <div class="text-[10px] uppercase tracking-wider mb-2" style="color:#6a6058">{s.label}</div>
                    <div class="text-xl font-semibold">{s.value}</div>
                    <div class="text-[10px] mt-1" style="color:#9a9080">{s.sub}</div>
                </div>
            {/each}
        </div>
    {/if}

    <!-- 90-day heatmap + Precip calendar -->
    <div class="grid gap-4 mb-4" style="grid-template-columns: 1fr 300px">

        <!-- 90-day heatmap -->
        <div class="rounded-2xl p-5" style="background:#1c1b17; border:1px solid #2a2823">
            <div class="text-[11px] font-medium uppercase tracking-widest mb-5" style="color:#6a6058">Last 90 Days</div>
            {#each monthGroups as { month, days: mDays, offset }, gi}
                <div class="{gi < monthGroups.length - 1 ? 'mb-7' : ''}">
                    <div class="text-sm font-semibold mb-3" style="color:#c8bfb0">{month}</div>
                    <!-- Weekday headers -->
                    <div class="grid grid-cols-7 gap-1 mb-1.5">
                        {#each ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'] as h}
                            <div class="text-[9px] text-center font-medium" style="color:#3a3428">{h}</div>
                        {/each}
                    </div>
                    <!-- Calendar grid -->
                    <div class="grid grid-cols-7 gap-1.5">
                        {#each Array(offset) as _}
                            <div></div>
                        {/each}
                        {#each mDays as d}
                            {@const m = d.metadata}
                            <div
                                class="rounded-xl p-2 flex flex-col items-center gap-0.5"
                                style="background:{tempColorAlpha(m.temp_max, 0.15)}; border:1px solid {tempColorAlpha(m.temp_max, 0.28)}"
                                title="{new Date(d.timestamp).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })} · {weatherLabel(m.weathercode)} · {m.precipitation ?? 0}mm"
                            >
                                <div class="text-[9px]" style="color:#5a5248">
                                    {new Date(d.timestamp).getDate()}
                                </div>
                                <div class="text-sm font-bold leading-none" style="color:{tempColor(m.temp_max)}">
                                    {Math.round(m.temp_max)}°
                                </div>
                                <div class="text-[9px]" style="color:#4a4238">
                                    {Math.round(m.temp_min)}°
                                </div>
                                {#if (m.precipitation || 0) > 1}
                                    <div class="w-2 rounded-full mt-0.5" style="height:2px; background:#4a7a9b"></div>
                                {/if}
                            </div>
                        {/each}
                    </div>
                </div>
            {/each}
        </div>

        <!-- Precipitation bar chart -->
        <div class="rounded-2xl p-5 flex flex-col" style="background:#1c1b17; border:1px solid #2a2823">
            <div class="text-[11px] font-medium uppercase tracking-widest mb-4" style="color:#6a6058">Rain · Last 30 Days</div>

            <!-- Mini stats -->
            <div class="grid grid-cols-3 gap-2 mb-4 shrink-0">
                <div class="rounded-lg p-2.5 text-center" style="background:#151411">
                    <div class="text-[9px] uppercase tracking-wider mb-1" style="color:#6a6058">Total</div>
                    <div class="text-sm font-semibold" style="color:#6b9ecc">{totalPrecip30}mm</div>
                </div>
                <div class="rounded-lg p-2.5 text-center" style="background:#151411">
                    <div class="text-[9px] uppercase tracking-wider mb-1" style="color:#6a6058">Rainy Days</div>
                    <div class="text-sm font-semibold">{rainyDays30}</div>
                </div>
                <div class="rounded-lg p-2.5 text-center" style="background:#151411">
                    <div class="text-[9px] uppercase tracking-wider mb-1" style="color:#6a6058">Peak</div>
                    <div class="text-sm font-semibold" style="color:#6b9ecc">{maxPrecip.toFixed(1)}mm</div>
                </div>
            </div>

            <!-- Grid fills remaining height — 6 cols × 5 rows = 30 cells -->
            <div class="flex-1" style="min-height:0">
                <div style="display:grid; grid-template-columns:repeat(6,1fr); grid-template-rows:repeat(5,1fr); gap:5px; height:100%">
                    {#each precipDays as d}
                        {@const p = d.metadata.precipitation || 0}
                        {@const alpha = p < 0.5 ? 0.06 : Math.min(0.88, 0.15 + (p / maxPrecip) * 0.73)}
                        <div
                            class="rounded-lg flex flex-col items-center justify-center gap-0.5"
                            style="background:rgba(74,122,155,{alpha}); border:1px solid rgba(74,122,155,{Math.min(1, alpha + 0.09)})"
                            title="{new Date(d.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}: {p}mm"
                        >
                            <div class="text-[9px]" style="color:{p > 0.5 ? '#9bc8e0' : '#4a4238'}">
                                {new Date(d.timestamp).getDate()}
                            </div>
                            {#if p >= 1}
                                <div class="text-[8px]" style="color:#6aabcc">{p}mm</div>
                            {/if}
                        </div>
                    {/each}
                </div>
            </div>
        </div>
    </div>

    <!-- Temperature trend chart -->
    <div class="rounded-2xl p-5" style="background:#1c1b17; border:1px solid #2a2823">
        <div class="flex items-center justify-between mb-4">
            <div class="text-[11px] font-medium uppercase tracking-widest" style="color:#6a6058">Temperature Trend</div>
            <div class="flex gap-1.5">
                {#each RANGES as r}
                    <button
                        on:click={() => loadChart(r)}
                        class="px-3 py-1 rounded-lg text-xs font-medium"
                        style="background:{range === r.key ? '#2e2b24' : 'transparent'};
                               color:{range === r.key ? '#e8e0d0' : '#6a6058'};
                               border:1px solid {range === r.key ? '#3e3830' : '#252320'}"
                    >{r.label}</button>
                {/each}
            </div>
        </div>
        <div bind:this={chartEl} style="height:220px"></div>
    </div>

</main>

<style>
  @media (max-width: 768px) {
    main {
      padding: 14px 14px 0 !important;
    }
    main div[style*="grid-template-columns: 300px"],
    main div[style*="grid-template-columns: 1fr 300px"],
    main div[style*="grid-template-columns: 1fr"] {
      display: flex !important;
      flex-direction: column !important;
      gap: 10px !important;
    }
    main > div.flex.items-center.justify-between {
      flex-wrap: wrap;
      gap: 8px;
    }
    /* Chart containers: prevent overflow */
    main div[style*="grid-template-rows"],
    main > .grid {
      display: flex !important;
      flex-direction: column !important;
      gap: 10px !important;
    }
    main > .grid > div {
      grid-column: unset !important;
      grid-row: unset !important;
      height: auto !important;
    }
  }
</style>
