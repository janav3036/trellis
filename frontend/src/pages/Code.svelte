<script>
    import { onMount } from "svelte";
    import Plotly from "plotly.js-dist-min";
    import { daysAgoIST, buildDatesIST, groupByDayIST, groupByWeekIST, istTime, fmtDate } from "../lib/ist.js";

    let chartEl;
    let range = "monthly";
    let commits = [];
    let recentCommits = [];
    let prs = [];
    let allRepos = [];
    let backfillDate = "";
    let backfillStatus = "";

    const RANGES = [
        { key: "daily", label: "Today" },
        { key: "monthly", label: "30 days" },
        { key: "6m", label: "6 months" },
        { key: "yearly", label: "Year" },
    ];

    const ACCENT = "#6b9e6b";

    const plotLayout = {
        paper_bgcolor: "#1a1714",
        plot_bgcolor: "#1a1714",
        font: { color: "#e8e0d0" },
        xaxis: { gridcolor: "#242019", tickcolor: "#9a9080" },
        yaxis: {
            gridcolor: "#242019",
            tickcolor: "#9a9080",
            title: "commits",
            rangemode: "tozero",
        },
        margin: { t: 40, r: 20, b: 60, l: 50 },
    };

    function timeAgo(timestamp) {
        const seconds = Math.floor((Date.now() - new Date(timestamp)) / 1000);
        if (seconds < 60) return "just now";
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        if (days < 30) return `${days}d ago`;
        return fmtDate(timestamp);
    }

    async function loadChart(r) {
        range = r;
        commits = [];

        if (r === "daily") {
            const res = await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(0)}`);
            commits = await res.json();
            if (chartEl) Plotly.purge(chartEl);
            return;
        }

        let events, dates, counts, title;

        if (r === "monthly") {
            const res = await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(29)}`);
            events = await res.json();
            dates = buildDatesIST(30);
            counts = groupByDayIST(events);
            title = "GitHub — last 30 days";
        } else if (r === "6m") {
            const res = await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(179)}`);
            events = await res.json();
            dates = buildDatesIST(180);
            counts = groupByDayIST(events);
            title = "GitHub — last 6 months";
        } else {
            const res = await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(364)}`);
            events = await res.json();
            counts = groupByWeekIST(events);
            dates = Object.keys(counts).sort();
            title = "GitHub — last year (by week)";
        }

        Plotly.react(chartEl, [{
            x: dates,
            y: dates.map(d => counts[d] || 0),
            type: "bar",
            marker: { color: ACCENT },
        }], { ...plotLayout, title: { text: title, font: { color: "#e8e0d0" } } });
    }

    onMount(async () => {
        const [recentRes, prRes, reposRes] = await Promise.all([
            fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(29)}`),
            fetch(`/api/events?source=github&event_type=pr`),
            fetch("/api/github/repos"),
            loadChart("monthly"),
        ]);
        recentCommits = await recentRes.json();
        prs = await prRes.json();
        allRepos = await reposRes.json();
    });

    $: totalCommits = recentCommits.length;
    $: repos = [...new Set(recentCommits.map(c => c.metadata.repo))];
    $: openPRs = prs.filter(p => p.metadata.state === "open").length;
</script>

<main class="p-8 bg-[#1a1714] min-h-screen text-[#e8e0d0]">
    <div class="flex items-center justify-between mb-2">
        <h1 class="text-3xl font-semibold">Code</h1>
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
                    const res = await fetch("/api/backfill/github", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ date_from: backfillDate }),
                    });
                    const data = await res.json();
                    backfillStatus = `${data.count} new commits`;
                    const reposRes = await fetch("/api/github/repos");
                    allRepos = await reposRes.json();
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

    <div class="flex gap-6 mb-8 text-sm text-[#9a9080]">
        <span><span class="text-[#e8e0d0] font-medium">{totalCommits}</span> commits (30d)</span>
        <span><span class="text-[#e8e0d0] font-medium">{repos.length}</span> repos</span>
        <span><span class="text-[#e8e0d0] font-medium">{openPRs}</span> open PRs</span>
    </div>

    <div class="flex gap-2 mb-4">
        {#each RANGES as r}
            <button
                on:click={() => loadChart(r.key)}
                class="px-4 py-1.5 rounded-lg text-sm font-medium transition-colors
                    {range === r.key ? 'bg-[#6b9e6b] text-[#1a1714]' : 'bg-[#242019] text-[#9a9080] hover:text-[#e8e0d0]'}"
            >
                {r.label}
            </button>
        {/each}
    </div>

    {#if range === "daily"}
        <div class="flex flex-col gap-2 max-w-2xl">
            {#each commits as c}
                <div class="flex items-center gap-4 px-4 py-2 rounded-lg bg-[#242019]">
                    <span class="text-xs text-[#9a9080] shrink-0">{istTime(c.timestamp)}</span>
                    <span class="text-xs bg-[#1a1714] text-[#6b9e6b] px-2 py-0.5 rounded font-mono shrink-0">{c.metadata.repo.split("/")[1]}</span>
                    <span class="text-sm truncate">{c.metadata.message}</span>
                    <span class="text-xs text-[#9a9080] font-mono shrink-0">{c.metadata.sha}</span>
                </div>
            {:else}
                <p class="text-[#9a9080] text-sm">No commits today.</p>
            {/each}
        </div>
    {:else}
        <div bind:this={chartEl}></div>
    {/if}

    <h2 class="text-xl font-semibold mt-10 mb-4">Recent Commits</h2>
    <div class="flex flex-col gap-2 max-w-2xl">
        {#each recentCommits.slice(0, 25) as c}
            <div class="flex items-start gap-4 px-4 py-3 rounded-lg bg-[#242019]">
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="text-xs bg-[#1a1714] text-[#6b9e6b] px-2 py-0.5 rounded font-mono">{c.metadata.repo.split("/")[1]}</span>
                        <span class="text-xs text-[#9a9080] font-mono">{c.metadata.sha}</span>
                    </div>
                    <div class="text-sm text-[#e8e0d0] truncate">{c.metadata.message}</div>
                </div>
                <span class="text-xs text-[#9a9080] shrink-0 mt-1">{timeAgo(c.timestamp)}</span>
            </div>
        {:else}
            <p class="text-[#9a9080] text-sm">No commits in the last 30 days.</p>
        {/each}
    </div>

    {#if prs.length > 0}
        <h2 class="text-xl font-semibold mt-10 mb-4">Pull Requests</h2>
        <div class="flex flex-col gap-2 max-w-2xl">
            {#each prs.slice(0, 20) as pr}
                <div class="flex items-center gap-4 px-4 py-3 rounded-lg bg-[#242019]">
                    <span class="text-xs px-2 py-0.5 rounded {pr.metadata.state === 'open' ? 'bg-[#2a4a2a] text-[#6b9e6b]' : 'bg-[#2a2a3a] text-[#9a9080]'}">{pr.metadata.state}</span>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm truncate">{pr.metadata.title}</div>
                        <div class="text-xs text-[#9a9080] mt-0.5">{pr.metadata.repo} #{pr.metadata.number}</div>
                    </div>
                    <span class="text-xs text-[#9a9080] shrink-0">{timeAgo(pr.timestamp)}</span>
                </div>
            {/each}
        </div>
    {/if}

    {#if allRepos.length > 0}
        <h2 class="text-xl font-semibold mt-10 mb-4">Repositories</h2>
        <div class="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3 max-w-4xl">
            {#each allRepos as r}
                <div class="bg-[#242019] rounded-xl px-4 py-3">
                    <div class="text-sm font-medium truncate">{r.repo.split("/")[1]}</div>
                    <div class="text-xs text-[#9a9080] mt-1">{r.repo.split("/")[0]}</div>
                    <div class="text-xs text-[#6b9e6b] mt-2">{r.commits} commits</div>
                </div>
            {/each}
        </div>
    {/if}
</main>
