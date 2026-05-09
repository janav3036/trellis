<script>
    import { onMount } from "svelte";

    let calendarEvents = [];
    let backfillDate = "";
    let backfillStatus = "";

    const today = new Date();
    let viewYear = today.getFullYear();
    let viewMonth = today.getMonth(); // 0-indexed: 0=Jan, 11=Dec
    let selectedDay = null;

    const MONTH_NAMES = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ];
    const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

    const CAL_COLORS = {
        Projects: { bg: "#2a3d2a", text: "#8abf8a" },
        "Gym / Sports": { bg: "#3d2e1a", text: "#c89a5a" },
        College: { bg: "#1a2a3d", text: "#6b9ecc" },
        Slots: { bg: "#2e1a1a", text: "#c87a7a" },
        "Side projects": { bg: "#2a1a3d", text: "#9b7ec8" },
        "Courses & Studies": { bg: "#2e2a1a", text: "#c8a84b" },
        "Test & ICAs": { bg: "#1a2e2e", text: "#5abfbf" },
    };
    const DEFAULT_COLOR = { bg: "#2a2a2a", text: "#9a9080" };

    function calColor(name) {
        return CAL_COLORS[name] || DEFAULT_COLOR;
    }

    function isoDate(d) {
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    }

    function isToday(d) {
        return isoDate(d) === isoDate(today);
    }

    function formatDuration(mins) {
        if (!mins) return "";
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        if (h === 0) return `${m}m`;
        if (m === 0) return `${h}h`;
        return `${h}h ${m}m`;
    }

    function timeAgo(ts) {
        const secs = Math.floor((Date.now() - new Date(ts)) / 1000);
        if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
        if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
        const days = Math.floor(secs / 86400);
        if (days < 30) return `${days}d ago`;
        return new Date(ts).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
        });
    }

    function prevMonth() {
        if (viewMonth === 0) {
            viewMonth = 11;
            viewYear--;
        } else viewMonth--;
    }

    function nextMonth() {
        if (viewMonth === 11) {
            viewMonth = 0;
            viewYear++;
        } else viewMonth++;
    }

    $: calendarGrid = (() => {
        const first = new Date(viewYear, viewMonth, 1);
        const last = new Date(viewYear, viewMonth + 1, 0);
        const startDow = first.getDay(); // 0=Sun
        const prefix = startDow === 0 ? 6 : startDow - 1;
        const cells = [];
        for (let i = prefix; i > 0; i--)
            cells.push({
                date: new Date(viewYear, viewMonth, 1 - i),
                inMonth: false,
            });
        for (let d = 1; d <= last.getDate(); d++)
            cells.push({
                date: new Date(viewYear, viewMonth, d),
                inMonth: true,
            });
        while (cells.length % 7 !== 0) {
            const n = cells.length - last.getDate() - prefix + 1;
            cells.push({
                date: new Date(viewYear, viewMonth + 1, n),
                inMonth: false,
            });
        }
        return cells;
    })();

    $: eventsByDate = (() => {
        const map = {};
        for (const e of calendarEvents) {
            const key = e.timestamp.slice(0, 10);
            if (!map[key]) map[key] = [];
            map[key].push(e);
        }
        return map;
    })();

    $: monthStats = (() => {
        const evs = calendarEvents.filter((e) => {
            const d = new Date(e.timestamp);
            return d.getMonth() === viewMonth && d.getFullYear() === viewYear;
        });
        return {
            sessions: evs.length,
            hours:
                evs.reduce(
                    (s, e) => s + (e.metadata.duration_minutes || 0),
                    0,
                ) / 60,
            days: new Set(evs.map((e) => e.timestamp.slice(0, 10))).size,
        };
    })();

    onMount(async () => {
        const res = await fetch(`/api/events?source=calendar&event_type=event`);
        calendarEvents = await res.json();
    });
</script>

<main class="p-8 bg-[#1a1714] min-h-screen text-[#e8e0d0]">
    <div class="flex items-center justify-between mb-6">
        <h1 class="text-3xl font-semibold">Life</h1>
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
                    const res = await fetch("/api/backfill/calendar", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ date_from: backfillDate }),
                    });
                    const data = await res.json();
                    backfillStatus = `${data.count} events loaded`;
                    const evRes = await fetch(
                        `/api/events?source=calendar&event_type=event`,
                    );
                    calendarEvents = await evRes.json();
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
    <section class="mb-10">
        <div class="flex items-center gap-4 mb-4">
            <button
                on:click={prevMonth}
                class="bg-[#242019] hover:bg-[#2e2923] px-3 py-1.5 rounded-lg text-sm"
                >←</button
            >
            <h2 class="text-xl font-semibold">
                {MONTH_NAMES[viewMonth]}
                {viewYear}
            </h2>
            <button
                on:click={nextMonth}
                class="bg-[#242019] hover:bg-[#2e2923] px-3 py-1.5 rounded-lg text-sm"
                >→</button
            >
            {#if monthStats.sessions > 0}
                <span class="text-sm text-[#9a9080] ml-2">
                    {monthStats.sessions} sessions · {monthStats.hours.toFixed(
                        1,
                    )}h · {monthStats.days} days active
                </span>
            {/if}
        </div>

        <div class="grid grid-cols-7 gap-1 max-w-4xl mb-1">
            {#each DOW as dow}
                <div class="text-center text-xs text-[#9a9080] py-1">{dow}</div>
            {/each}
        </div>

        <div class="grid grid-cols-7 gap-1 max-w-4xl">
            {#each calendarGrid as cell}
                {@const dateKey = isoDate(cell.date)}
                {@const events = eventsByDate[dateKey] || []}
                {@const todayCell = isToday(cell.date)}
                <div
                    class="rounded-lg p-1.5 min-h-[64px] flex flex-col cursor-pointer
                    {cell.inMonth ? 'bg-[#242019]' : 'bg-[#1e1c19]'}
                    {todayCell ? 'ring-1 ring-[#6b9e6b]' : ''}
                    {selectedDay === dateKey ? 'ring-1 ring-[#c8a84b]' : ''}"
                    on:click={() =>
                        (selectedDay =
                            selectedDay === dateKey ? null : dateKey)}
                >
                    <div
                        class="text-xs mb-1
                        {todayCell
                            ? 'text-[#6b9e6b] font-semibold'
                            : cell.inMonth
                              ? 'text-[#9a9080]'
                              : 'text-[#4a4540]'}"
                    >
                        {cell.date.getDate()}
                    </div>
                    {#each events.slice(0, 2) as e}
                        <div
                            class="text-[9px] rounded px-1 py-0.5 mb-0.5 truncate leading-tight"
                            style="background:{calColor(
                                e.metadata.calendar_name,
                            ).bg}; color:{calColor(e.metadata.calendar_name)
                                .text}"
                            title="{e.metadata.title} ({formatDuration(
                                e.metadata.duration_minutes,
                            )})"
                        >
                            {e.metadata.title}
                        </div>
                    {/each}
                    {#if events.length > 2}
                        <div class="text-[9px] text-[#9a9080]">
                            +{events.length - 2} more
                        </div>
                    {/if}
                </div>
            {/each}
        </div>

        {#if selectedDay}
            {@const dayEvents = eventsByDate[selectedDay] || []}
            <div class="mt-4 max-w-4xl bg-[#242019] rounded-xl p-4">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-sm font-medium">
                        {new Date(selectedDay + "T12:00:00").toLocaleDateString("en-US", {
                            weekday: "long", month: "long", day: "numeric",
                        })}
                    </span>
                    <button
                        on:click={() => (selectedDay = null)}
                        class="text-xs text-[#9a9080] hover:text-[#e8e0d0]"
                        >✕</button
                    >
                </div>
                {#if dayEvents.length === 0}
                    <p class="text-xs text-[#9a9080]">No events</p>
                {:else}
                    <div class="flex flex-col gap-2">
                        {#each dayEvents as e}
                            {@const color = calColor(e.metadata.calendar_name)}
                            <div
                                class="flex items-center gap-3 px-3 py-2 rounded-lg"
                                style="background:{color.bg}"
                            >
                                <div class="flex-1 min-w-0">
                                    <div class="text-sm font-medium truncate" style="color:{color.text}">
                                        {e.metadata.title}
                                    </div>
                                    <div class="text-xs text-[#9a9080] mt-0.5">
                                        {e.metadata.calendar_name}{#if e.metadata.duration_minutes} · {formatDuration(e.metadata.duration_minutes)}{/if}
                                    </div>
                                </div>
                                {#if e.metadata.duration_minutes}
                                    <span class="text-xs shrink-0" style="color:{color.text}">
                                        {formatDuration(e.metadata.duration_minutes)}
                                    </span>
                                {/if}
                            </div>
                        {/each}
                    </div>
                {/if}
            </div>
        {/if}
    </section>

    <section class="mb-10">
        <h2 class="text-xl font-semibold mb-4">Recent Sessions</h2>
        {#if calendarEvents.length === 0}
            <p class="text-sm text-[#9a9080]">
                No events yet — use Backfill to import from Google Calendar.
            </p>
        {:else}
            <div class="flex flex-col gap-2 max-w-2xl">
                {#each calendarEvents.slice(0, 15) as e}
                    <div class="flex items-center gap-4 px-4 py-3 rounded-lg bg-[#242019]">
                        <div class="flex-1 min-w-0">
                            <div class="text-sm font-medium truncate">{e.metadata.title}</div>
                            <div class="text-xs text-[#9a9080] mt-0.5">
                                {e.metadata.calendar_name}{#if e.metadata.duration_minutes} · {formatDuration(e.metadata.duration_minutes)}{/if}
                            </div>
                        </div>
                        <span class="text-xs text-[#9a9080] shrink-0">{timeAgo(e.timestamp)}</span>
                    </div>
                {/each}
            </div>
        {/if}
    </section>
    <section class="mb-10">
        <h2 class="text-xl font-semibold mb-4">Gym</h2>
        <div
            class="max-w-2xl rounded-xl bg-[#242019] border border-dashed border-[#3a3530] px-6 py-8 text-center"
        >
            <div class="text-sm font-medium mb-1">No gym data yet</div>
            <div class="text-xs text-[#9a9080]">
                Connect a fitness tracker or log workouts manually to see your
                gym history.
            </div>
        </div>
    </section>

    <section class="mb-10">
        <h2 class="text-xl font-semibold mb-4">People Log</h2>
        <div
            class="max-w-2xl rounded-xl bg-[#242019] border border-dashed border-[#3a3530] px-6 py-8 text-center"
        >
            <div class="text-sm font-medium mb-1">No people log yet</div>
            <div class="text-xs text-[#9a9080]">
                Relationship timeline and "haven't seen X in N months" alerts —
                coming soon.
            </div>
        </div>
    </section>

    <section class="mb-10">
        <h2 class="text-xl font-semibold mb-4">Movie Diary</h2>
        <div
            class="max-w-2xl rounded-xl bg-[#242019] border border-dashed border-[#3a3530] px-6 py-8 text-center"
        >
            <div class="text-sm font-medium mb-1">No movies logged yet</div>
            <div class="text-xs text-[#9a9080]">
                Poster-grid timeline filterable by genre and mood — coming when
                the Letterboxd ingester is ready.
            </div>
        </div>
    </section>
</main>
