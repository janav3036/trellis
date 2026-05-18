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

    function tempColor(tempMax) {
        const t = Math.max(0, Math.min(35, tempMax));
        const ratio = t / 35;
        const r = Math.round(60 + ratio * 160);
        const g = Math.round(80 + ratio * 60);
        const b = Math.round(160 - ratio * 120);
        return `rgb(${r},${g},${b})`;
    }
    function tempColorAlpha(tempMax, alpha) {
        const t = Math.max(0, Math.min(35, tempMax));
        const ratio = t / 35;
        const r = Math.round(60 + ratio * 160);
        const g = Math.round(80 + ratio * 60);
        const b = Math.round(160 - ratio * 120);
        return `rgba(${r},${g},${b},${alpha})`;
    }

    const RANGES = [
        { key: "30d", label: "30 days", n: 30 },
        { key: "90d", label: "90 days", n: 90 },
        { key: "180d", label: "6 months", n: 180 },
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
                    x,
                    y: yMax,
                    name: "High",
                    type: "scatter",
                    mode: "lines",
                    line: { color: "#c87941", width: 2 },
                },
                {
                    x,
                    y: yMin,
                    name: "Low",
                    type: "scatter",
                    mode: "lines",
                    line: { color: "#6b9ecc", width: 2 },
                },
                {
                    x,
                    y: precip,
                    name: "Precip (mm)",
                    type: "bar",
                    yaxis: "y2",
                    marker: { color: "#4a7a9b", opacity: 0.5 },
                },
            ],
            {
                paper_bgcolor: "#1a1714",
                plot_bgcolor: "#1a1714",
                font: { color: "#e8e0d0" },
                xaxis: { gridcolor: "#242019", tickcolor: "#9a9080" },
                yaxis: {
                    gridcolor: "#242019",
                    tickcolor: "#9a9080",
                    title: "°C",
                },
                yaxis2: {
                    overlaying: "y",
                    side: "right",
                    title: "mm",
                    showgrid: false,
                },
                legend: { bgcolor: "#1a1714" },
                margin: { t: 30, r: 60, b: 60, l: 50 },
            },
        );
    }

    let weekOffset = 0;
    let weekDays = [];

    $: {
        const today = new Date();
        const dow = today.getDay();
        const toMonday = dow === 0 ? -6 : 1 - dow;
        const monday = new Date(today);
        monday.setDate(today.getDate() + toMonday + weekOffset * 7);
        monday.setHours(0, 0, 0, 0);
        const sunday = new Date(monday);
        sunday.setDate(monday.getDate() + 6);
        sunday.setHours(23, 59, 59, 0);
        weekDays = [...days, ...forecast].filter((d) => {
            const t = new Date(d.timestamp);
            return t >= monday && t <= sunday;
        });
    }

    $: weekLabel = (() => {
        const today = new Date();
        const dow = today.getDay();
        const toMonday = dow === 0 ? -6 : 1 - dow;
        const monday = new Date(today);
        monday.setDate(today.getDate() + toMonday + weekOffset * 7);
        const sunday = new Date(monday);
        sunday.setDate(monday.getDate() + 6);
        const fmt = (d) =>
            d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
        return `${fmt(monday)} – ${fmt(sunday)}`;
    })();

    onMount(async () => {
        const [calRes, forecastRes] = await Promise.all([
            fetch(
                `/api/events?source=weather&event_type=daily&date_from=${daysAgo(89)}`,
            ),
            fetch("/api/weather/forecast"),
            loadChart(RANGES[0]),
        ]);
        days = (await calRes.json()).reverse();
        forecast = await forecastRes.json();
    });
</script>

<main class="p-8 bg-[#1a1714] min-h-screen text-[#e8e0d0]">
    <div class="flex items-center justify-between mb-6">
        <h1 class="text-3xl font-semibold">Weather</h1>
        <div class="flex items-center gap-2">
            <input
                type="date"
                bind:value={backfillDate}
                class="bg-[#242019] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
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
                            await fetch(
                                `/api/events?source=weather&event_type=daily&date_from=${daysAgo(89)}`,
                            )
                        ).json()
                    ).reverse();
                }}
                class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-2 rounded-lg text-sm"
            >
                Backfill
            </button>
            {#if backfillStatus}
                <span class="text-sm text-[#9a9080]">{backfillStatus}</span>
            {/if}
        </div>
    </div>

    {#if days.length > 0}
        {@const today = days[days.length - 1]}
        <div
            class="rounded-2xl p-6 mb-8 max-w-sm"
            style="background: {tempColorAlpha(
                today.metadata.temp_max,
                0.13,
            )}; border: 1px solid {tempColorAlpha(
                today.metadata.temp_max,
                0.27,
            )}"
        >
            <div class="text-lg font-medium mb-1">
                {new Date(today.timestamp).toLocaleDateString("en-US", {
                    weekday: "long",
                    month: "long",
                    day: "numeric",
                })}
            </div>
            <div
                class="text-4xl font-semibold mb-1"
                style="color: {tempColor(today.metadata.temp_max)}"
            >
                {Math.round(today.metadata.temp_max)}°C
            </div>
            <div class="text-sm text-[#9a9080] mb-3">
                Low {Math.round(today.metadata.temp_min)}°C
            </div>
            <div class="text-sm">
                {weatherLabel(today.metadata.weathercode)}
            </div>
            <div class="flex gap-4 mt-3 text-xs text-[#9a9080]">
                <span>Rain {today.metadata.precipitation} mm</span>
                <span>Wind {Math.round(today.metadata.windspeed_max)} km/h</span
                >
            </div>
        </div>
    {/if}

    <h2 class="text-xl font-semibold mb-4">Last 90 Days</h2>
    <div
        class="grid grid-cols-[repeat(auto-fill,minmax(72px,1fr))] gap-2 max-w-5xl mb-10"
    >
        {#each days as d}
            {@const m = d.metadata}
            <div
                class="rounded-xl p-2 flex flex-col items-center"
                style="background: {tempColorAlpha(
                    m.temp_max,
                    0.18,
                )}; border: 1px solid {tempColorAlpha(m.temp_max, 0.35)}"
                title="{weatherLabel(m.weathercode)} — {m.precipitation}mm rain"
            >
                <div class="text-[10px] text-[#9a9080] mb-1">
                    {new Date(d.timestamp).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                    })}
                </div>
                <div
                    class="text-sm font-semibold"
                    style="color: {tempColor(m.temp_max)}"
                >
                    {Math.round(m.temp_max)}°
                </div>
                <div class="text-[10px] text-[#9a9080]">
                    {Math.round(m.temp_min)}°
                </div>
                {#if m.precipitation > 1}
                    <div class="text-[10px] mt-1 text-[#6b9ecc]">💧</div>
                {:else if m.weathercode >= 95}
                    <div class="text-[10px] mt-1">⚡</div>
                {/if}
            </div>
        {/each}
    </div>

    <h2 class="text-xl font-semibold mb-4">This Week</h2>
    <div class="flex items-center gap-4 mb-4">
        <button
            on:click={() => (weekOffset -= 1)}
            class="bg-[#242019] hover:bg-[#2e2923] text-[#e8e0d0] px-3 py-1.5 rounded-lg text-sm"
            >←</button
        >
        <span class="text-sm text-[#9a9080]">{weekLabel}</span>
        <button
            on:click={() => (weekOffset = Math.min(1, weekOffset + 1))}
            class="bg-[#242019] hover:bg-[#2e2923] text-[#e8e0d0] px-3 py-1.5 rounded-lg text-sm disabled:opacity-30"
            disabled={weekOffset >= 1}>→</button
        >
    </div>

    {#if weekDays.length > 0}
        <div class="grid grid-cols-7 gap-2 max-w-3xl mb-10">
            {#each weekDays as d}
                {@const m = d.metadata}
                <div
                    class="rounded-xl p-3 flex flex-col items-center gap-1"
                    style="background: {tempColorAlpha(
                        m.temp_max,
                        0.18,
                    )}; border: 1px solid {tempColorAlpha(m.temp_max, 0.35)}"
                >
                    <div class="text-[10px] text-[#9a9080]">
                        {new Date(d.timestamp).toLocaleDateString("en-US", {
                            weekday: "short",
                        })}
                    </div>
                    <div class="text-[10px] text-[#9a9080]">
                        {new Date(d.timestamp).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                        })}
                    </div>
                    <div
                        class="text-base font-semibold"
                        style="color: {tempColor(m.temp_max)}"
                    >
                        {Math.round(m.temp_max)}°
                    </div>
                    <div class="text-[10px] text-[#9a9080]">
                        {Math.round(m.temp_min)}°
                    </div>
                    <div
                        class="text-[10px] text-center text-[#c8c0b0] mt-1 leading-tight"
                    >
                        {weatherLabel(m.weathercode)}
                    </div>
                    {#if m.precipitation > 1}
                        <div class="text-[10px] text-[#6b9ecc]">
                            💧 {m.precipitation}mm
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    {:else}
        <p class="text-sm text-[#9a9080] mb-10">No data for this week yet.</p>
    {/if}

    <h2 class="text-xl font-semibold mb-4">Temperature Trend</h2>
    <div class="flex gap-2 mb-4">
        {#each RANGES as r}
            <button
                on:click={() => loadChart(r)}
                class="px-4 py-1.5 rounded-lg text-sm font-medium transition-colors
                    {range === r.key
                    ? 'bg-[#6b9e6b] text-[#1a1714]'
                    : 'bg-[#242019] text-[#9a9080] hover:text-[#e8e0d0]'}"
            >
                {r.label}
            </button>
        {/each}
    </div>
    <div bind:this={chartEl} class="max-w-5xl"></div>
</main>
