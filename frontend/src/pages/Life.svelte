<script>
    import { onMount } from "svelte";
    import { blur } from "svelte/transition";
    import { istDate, todayIST, fmtDate } from "../lib/ist.js";

    let calendarEvents = [];
    let backfillDate = "";
    let backfillStatus = "";

    const today = new Date();
    let viewYear = today.getFullYear();
    let viewMonth = today.getMonth(); // 0-indexed: 0=Jan, 11=Dec
    let selectedDay = null;

    let gymSessions = [];
    let showGymForm = false;
    let gymDate = isoDate(today);
    let gymType = "workout";
    let gymMuscles = [];
    let gymDistance = "";
    let gymDuration = "";
    let gymNotes = "";
    let gymStatus = "";

    let peopleSummary = [];
    let peopleEvents = [];
    let showPeopleForm = false;
    let meetupDate = isoDate(today);
    let meetupNotes = "";
    let meetupPeople = [{ name: "", tag: "Friend" }];
    let peopleStatus = "";
    let expandedPerson = null;
    let peopleView = "people";

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

    const TMDB_GENRES = {
        28: "Action",
        12: "Adventure",
        16: "Animation",
        35: "Comedy",
        80: "Crime",
        99: "Documentary",
        18: "Drama",
        10751: "Family",
        14: "Fantasy",
        36: "History",
        27: "Horror",
        10402: "Music",
        9648: "Mystery",
        10749: "Romance",
        878: "Sci-Fi",
        53: "Thriller",
        10752: "War",
        37: "Western",
    };

    let movies = [];
    let showMovieForm = false;
    let movieDate = isoDate(today);
    let movieQuery = "";
    let movieResults = [];
    let selectedMovie = null;
    let movieRating = null;
    let movieNotes = "";
    let movieStatus = "";
    let searchTimeout = null;
    let expandedMovie = null;
    let selectedGenres = new Set();

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
        if (new Date(ts) > Date.now()) {
            const secs = Math.floor((new Date(ts) - Date.now()) / 1000);
            if (secs < 86400) return `in ${Math.floor(secs / 3600)}h`;
            return `in ${Math.floor(secs / 86400)}d`;
        }
        const secs = Math.floor((Date.now() - new Date(ts)) / 1000);
        if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
        if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
        const days = Math.floor(secs / 86400);
        if (days < 30) return `${days}d ago`;
        return fmtDate(ts);
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
            const key = istDate(e.timestamp);
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
            days: new Set(evs.map((e) => istDate(e.timestamp))).size,
        };
    })();

    $: meetupsByDate = (() => {
        const map = {};
        for (const e of peopleEvents) {
            const key = istDate(e.timestamp);
            if (!map[key]) map[key] = [];
            map[key].push(e);
        }
        return Object.entries(map).sort(([a], [b]) => b.localeCompare(a));
    })();

    $: availableGenres = [
        ...new Set(movies.flatMap((m) => m.metadata.genres || [])),
    ].filter((id) => TMDB_GENRES[id]);

    $: filteredMovies =
        selectedGenres.size == 0
            ? movies
            : movies.filter((m) =>
                  (m.metadata.genres || []).some((id) =>
                      selectedGenres.has(id),
                  ),
              );

    onMount(async () => {
        const [calRes, gymRes, peopleRes, peopleSumRes, moviesRes] =
            await Promise.all([
                fetch(`/api/events?source=calendar&event_type=event`),
                fetch(`/api/events?source=gym&event_type=session`),
                fetch(`/api/events?source=people&event_type=meetup`),
                fetch(`/api/people/summary`),
                fetch(`/api/events?source=movies&event_type=watch`),
            ]);
        calendarEvents = await calRes.json();
        gymSessions = await gymRes.json();
        peopleEvents = await peopleRes.json();
        peopleSummary = await peopleSumRes.json();
        movies = await moviesRes.json();
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
                        {new Date(selectedDay + "T12:00:00").toLocaleDateString(
                            "en-US",
                            {
                                timeZone: "Asia/Kolkata",
                                weekday: "long",
                                month: "long",
                                day: "numeric",
                            },
                        )}
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
                                    <div
                                        class="text-sm font-medium truncate"
                                        style="color:{color.text}"
                                    >
                                        {e.metadata.title}
                                    </div>
                                    <div class="text-xs text-[#9a9080] mt-0.5">
                                        {e.metadata
                                            .calendar_name}{#if e.metadata.duration_minutes}
                                            · {formatDuration(
                                                e.metadata.duration_minutes,
                                            )}{/if}
                                    </div>
                                </div>
                                {#if e.metadata.duration_minutes}
                                    <span
                                        class="text-xs shrink-0"
                                        style="color:{color.text}"
                                    >
                                        {formatDuration(
                                            e.metadata.duration_minutes,
                                        )}
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
                {#each calendarEvents
                    .filter((e) => new Date(e.timestamp) <= Date.now())
                    .slice(0, 15) as e}
                    <div
                        class="flex items-center gap-4 px-4 py-3 rounded-lg bg-[#242019]"
                    >
                        <div class="flex-1 min-w-0">
                            <div class="text-sm font-medium truncate">
                                {e.metadata.title}
                            </div>
                            <div class="text-xs text-[#9a9080] mt-0.5">
                                {e.metadata
                                    .calendar_name}{#if e.metadata.duration_minutes}
                                    · {formatDuration(
                                        e.metadata.duration_minutes,
                                    )}{/if}
                            </div>
                        </div>
                        <span class="text-xs text-[#9a9080] shrink-0"
                            >{timeAgo(e.timestamp)}</span
                        >
                    </div>
                {/each}
            </div>
        {/if}
    </section>
    <section class="mb-10">
        <div class="flex items-center gap-4 mb-4">
            <h2 class="text-xl font-semibold">Gym</h2>
            <button
                on:click={() => (showGymForm = !showGymForm)}
                class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-3 py-1 rounded-lg text-sm"
            >
                {showGymForm ? "Cancel" : "+ Log session"}
            </button>
            {#if gymStatus}
                <span class="text-sm text-[#9a9080]">{gymStatus}</span>
            {/if}
        </div>

        {#if showGymForm}
            <div class="max-w-xl bg-[#242019] rounded-xl p-5 mb-6">
                <div class="flex flex-col gap-4">
                    <div class="flex gap-4">
                        <div class="flex flex-col gap-1 flex-1">
                            <label class="text-xs text-[#9a9080]">Date</label>
                            <input
                                type="date"
                                bind:value={gymDate}
                                class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
                            />
                        </div>
                        <div class="flex flex-col gap-1">
                            <label class="text-xs text-[#9a9080]">Type</label>
                            <div class="flex gap-2">
                                <button
                                    on:click={() => (gymType = "workout")}
                                    class="px-3 py-2 rounded-lg text-sm {gymType ===
                                    'workout'
                                        ? 'bg-[#6b9e6b] text-[#1a1714]'
                                        : 'bg-[#1a1714] text-[#9a9080]'}"
                                >
                                    Workout
                                </button>
                                <button
                                    on:click={() => (gymType = "run")}
                                    class="px-3 py-2 rounded-lg text-sm {gymType ===
                                    'run'
                                        ? 'bg-[#6b9e6b] text-[#1a1714]'
                                        : 'bg-[#1a1714] text-[#9a9080]'}"
                                >
                                    Run
                                </button>
                            </div>
                        </div>
                    </div>

                    {#if gymType === "workout"}
                        <div class="flex flex-col gap-2">
                            <label class="text-xs text-[#9a9080]"
                                >Muscle groups</label
                            >
                            <div class="flex flex-wrap gap-2">
                                {#each ["Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs", "Core", "Forearms", "Calisthenics", "Boxing"] as muscle}
                                    <button
                                        on:click={() =>
                                            (gymMuscles = gymMuscles.includes(
                                                muscle,
                                            )
                                                ? gymMuscles.filter(
                                                      (m) => m !== muscle,
                                                  )
                                                : [...gymMuscles, muscle])}
                                        class="px-3 py-1 rounded-full text-xs {gymMuscles.includes(
                                            muscle,
                                        )
                                            ? 'bg-[#3d2e1a] text-[#c89a5a]'
                                            : 'bg-[#1a1714] text-[#9a9080]'}"
                                    >
                                        {muscle}
                                    </button>
                                {/each}
                            </div>
                        </div>
                    {:else}
                        <div class="flex flex-col gap-1">
                            <label class="text-xs text-[#9a9080]"
                                >Distance (km)</label
                            >
                            <input
                                type="number"
                                bind:value={gymDistance}
                                placeholder="5.0"
                                step="0.1"
                                class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530] w-32"
                            />
                        </div>
                    {/if}

                    <div class="flex gap-4">
                        <div class="flex flex-col gap-1">
                            <label class="text-xs text-[#9a9080]"
                                >Duration (min)</label
                            >
                            <input
                                type="number"
                                bind:value={gymDuration}
                                placeholder="60"
                                class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530] w-24"
                            />
                        </div>
                        <div class="flex flex-col gap-1 flex-1">
                            <label class="text-xs text-[#9a9080]">Notes</label>
                            <input
                                type="text"
                                bind:value={gymNotes}
                                placeholder="Optional"
                                class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
                            />
                        </div>
                    </div>

                    <button
                        on:click={async () => {
                            gymStatus = "saving…";
                            const res = await fetch("/api/gym/log", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    date: gymDate,
                                    type: gymType,
                                    muscle_groups: gymMuscles,
                                    distance_km: gymDistance
                                        ? parseFloat(gymDistance)
                                        : null,
                                    duration_minutes: gymDuration
                                        ? parseInt(gymDuration)
                                        : null,
                                    notes: gymNotes,
                                }),
                            });
                            const data = await res.json();
                            gymStatus = data.count
                                ? "Saved!"
                                : "Already logged for this date";
                            gymSessions = await (
                                await fetch(
                                    `/api/events?source=gym&event_type=session`,
                                )
                            ).json();
                            gymMuscles = [];
                            gymDistance = "";
                            gymDuration = "";
                            gymNotes = "";
                            showGymForm = false;
                        }}
                        class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-2 rounded-lg text-sm self-start"
                    >
                        Save
                    </button>
                </div>
            </div>
        {/if}

        {#if gymSessions.length === 0}
            <p class="text-sm text-[#9a9080]">No sessions logged yet.</p>
        {:else}
            <div class="flex flex-col gap-2 max-w-2xl">
                {#each gymSessions as s}
                    <div
                        class="flex items-center gap-4 px-4 py-3 rounded-lg bg-[#242019]"
                    >
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2 flex-wrap">
                                <span class="text-sm font-medium capitalize"
                                    >{s.metadata.type}</span
                                >
                                {#each s.metadata.muscle_groups || [] as m}
                                    <span
                                        class="text-xs px-2 py-0.5 rounded-full bg-[#3d2e1a] text-[#c89a5a]"
                                        >{m}</span
                                    >
                                {/each}
                                {#if s.metadata.distance_km}
                                    <span class="text-xs text-[#9a9080]"
                                        >{s.metadata.distance_km} km</span
                                    >
                                {/if}
                            </div>
                            {#if s.metadata.notes}
                                <div class="text-xs text-[#9a9080] mt-0.5">
                                    {s.metadata.notes}
                                </div>
                            {/if}
                        </div>
                        <div class="text-right shrink-0">
                            {#if s.metadata.duration_minutes}
                                <div class="text-xs text-[#c89a5a]">
                                    {formatDuration(
                                        s.metadata.duration_minutes,
                                    )}
                                </div>
                            {/if}
                            <div class="text-xs text-[#9a9080]">
                                {timeAgo(s.timestamp)}
                            </div>
                        </div>
                    </div>
                {/each}
            </div>
        {/if}
    </section>

    <section class="mb-10">
        <div class="flex items-center gap-4 mb-4">
            <h2 class="text-xl font-semibold">People Log</h2>
            <button
                on:click={() => (showPeopleForm = !showPeopleForm)}
                class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-3 py-1 rounded-lg text-sm"
                >{showPeopleForm ? "Cancel" : "+ Log meetup"}</button
            >

            <div class="flex gap-1 ml-2">
                <button
                    on:click={() => (peopleView = "people")}
                    class="px-3 py-1 rounded-lg text-sm {peopleView === 'people'
                        ? 'bg-[#3a3530] text-[#e8e0d0]'
                        : 'text-[#9a9080] hover:text-[#e8e0d0]'}">People</button
                >
                <button
                    on:click={() => (peopleView = "events")}
                    class="px-3 py-1 rounded-lg text-sm {peopleView === 'events'
                        ? 'bg-[#3a3530] text-[#e8e0d0]'
                        : 'text-[#9a9080] hover:text-[#e8e0d0]'}">Events</button
                >
            </div>
            {#if peopleStatus}
                <span class="text-sm text-[#9a9080]">{peopleStatus}</span>
            {/if}
        </div>

        {#if showPeopleForm}
            <div class="max-w-xl bg-[#242019] rounded-xl p-5 mb-6">
                <div class="flex flex-col gap-4">
                    <div class="flex gap-4">
                        <div class="flex flex-col gap-1">
                            <label class="text-xs text-[#9a9080]">Date</label>
                            <input
                                type="date"
                                bind:value={meetupDate}
                                class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
                            />
                        </div>
                        <div class="flex flex-col gap-1 flex-1">
                            <label class="text-xs text-[#9a9080]">Notes</label>
                            <input
                                type="text"
                                bind:value={meetupNotes}
                                placeholder="Coffee at Blue Tokai…"
                                class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
                            />
                        </div>
                    </div>

                    <div class="flex flex-col gap-2">
                        <label class="text-xs text-[#9a9080]">People</label>
                        {#each meetupPeople as person, i}
                            <div class="flex gap-2 items-center">
                                <input
                                    type="text"
                                    bind:value={person.name}
                                    placeholder="Name"
                                    class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530] flex-1"
                                />
                                <select
                                    bind:value={person.tag}
                                    class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
                                >
                                    {#each ["Friend", "Family", "Colleague", "Other"] as t}
                                        <option>{t}</option>
                                    {/each}
                                </select>
                                {#if meetupPeople.length > 1}
                                    <button
                                        on:click={() =>
                                            (meetupPeople = meetupPeople.filter(
                                                (_, j) => j !== i,
                                            ))}
                                        class="text-[#9a9080] hover:text-[#e8e0d0] text-sm px-2"
                                        >✕</button
                                    >
                                {/if}
                            </div>
                        {/each}
                        <button
                            on:click={() =>
                                (meetupPeople = [
                                    ...meetupPeople,
                                    { name: "", tag: "Friend" },
                                ])}
                            class="text-xs text-[#6b9e6b] hover:text-[#8abf8a] self-start"
                            >+ Add person</button
                        >
                    </div>

                    <button
                        on:click={async () => {
                            const valid = meetupPeople.filter((p) =>
                                p.name.trim(),
                            );
                            if (!valid.length) return;
                            peopleStatus = "saving…";
                            const res = await fetch("/api/people/log", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    date: meetupDate,
                                    notes: meetupNotes,
                                    people: valid,
                                }),
                            });
                            const data = await res.json();
                            peopleStatus = `${data.count} logged`;
                            const [evRes, sumRes] = await Promise.all([
                                fetch(
                                    `/api/events?source=people&event_type=meetup`,
                                ),
                                fetch(`/api/people/summary`),
                            ]);
                            peopleEvents = await evRes.json();
                            peopleSummary = await sumRes.json();
                            meetupPeople = [{ name: "", tag: "Friend" }];
                            meetupNotes = "";
                            showPeopleForm = false;
                        }}
                        class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-2 rounded-lg text-sm self-start"
                    >
                        Save
                    </button>
                </div>
            </div>
        {/if}

        {#if peopleView === "people"}
            {#if peopleSummary.length === 0}
                <p class="text-sm text-[#9a9080]">No meetups logged yet.</p>
            {:else}
                <div class="flex flex-col gap-2 max-w-2xl">
                    {#each peopleSummary as person}
                        {@const days = Math.floor(
                            (Date.now() - new Date(person.last_seen)) /
                                86400000,
                        )}
                        {@const urgency =
                            days < 30
                                ? "text-[#6b9e6b]"
                                : days < 90
                                  ? "text-[#c8a84b]"
                                  : "text-[#c87a7a]"}
                        {@const history = peopleEvents.filter(
                            (e) => e.metadata.name === person.name,
                        )}
                        <div class="bg-[#242019] rounded-xl overflow-hidden">
                            <button
                                class="w-full flex items-center gap-4 px-4 py-3 text-left hover:bg-[#2a2520]"
                                on:click={() =>
                                    (expandedPerson =
                                        expandedPerson === person.name
                                            ? null
                                            : person.name)}
                            >
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center gap-2">
                                        <span class="text-sm font-medium"
                                            >{person.name}</span
                                        >
                                        <span
                                            class="text-xs px-2 py-0.5 rounded-full bg-[#1a1714] text-[#9a9080]"
                                            >{person.tag}</span
                                        >
                                    </div>
                                    {#if person.last_notes}
                                        <div
                                            class="text-xs text-[#9a9080] mt-0.5 truncate"
                                        >
                                            {person.last_notes}
                                        </div>
                                    {/if}
                                </div>
                                <div class="text-right shrink-0">
                                    <div class="text-xs {urgency} font-medium">
                                        {days === 0 ? "today" : `${days}d ago`}
                                    </div>
                                    <div class="text-xs text-[#9a9080]">
                                        {person.total_meetups} meetup{person.total_meetups !==
                                        1
                                            ? "s"
                                            : ""}
                                    </div>
                                </div>
                            </button>
                            {#if expandedPerson === person.name}
                                <div
                                    class="border-t border-[#3a3530] px-4 py-3 flex flex-col gap-2"
                                >
                                    {#each history as e}
                                        <div class="flex items-start gap-3">
                                            <span
                                                class="text-xs text-[#9a9080] shrink-0 mt-0.5"
                                            >
                                                {new Date(
                                                    e.timestamp,
                                                ).toLocaleDateString("en-US", {
                                                    timeZone: "Asia/Kolkata",
                                                    month: "short",
                                                    day: "numeric",
                                                    year: "numeric",
                                                })}
                                            </span>
                                            <span class="text-xs text-[#c8c0b0]"
                                                >{e.metadata.notes || "—"}</span
                                            >
                                            <button
                                                on:click={async () => {
                                                    await fetch(
                                                        `/api/events/${e.id}`,
                                                        { method: "DELETE" },
                                                    );
                                                    const [evRes, sumRes] =
                                                        await Promise.all([
                                                            fetch(
                                                                `/api/events?source=people&event_type=meetup`,
                                                            ),
                                                            fetch(
                                                                `/api/people/summary`,
                                                            ),
                                                        ]);
                                                    peopleEvents =
                                                        await evRes.json();
                                                    peopleSummary =
                                                        await sumRes.json();
                                                }}
                                                class="ml-auto text-xs text-[#c87a7a] hover:text-[#e87a7a] shrink-0"
                                                >✕</button
                                            >
                                        </div>
                                    {/each}
                                </div>
                            {/if}
                        </div>
                    {/each}
                </div>
            {/if}
        {:else if meetupsByDate.length === 0}
            <p class="text-sm text-[#9a9080]">No meetups logged yet.</p>
        {:else}
            <div class="flex flex-col gap-3 max-w-2xl">
                {#each meetupsByDate as [date, events]}
                    <div class="bg-[#242019] rounded-xl px-4 py-3">
                        <div class="text-xs text-[#9a9080] mb-2">
                            {new Date(date + "T12:00:00").toLocaleDateString(
                                "en-US",
                                {
                                    timeZone: "Asia/Kolkata",
                                    weekday: "long",
                                    month: "long",
                                    day: "numeric",
                                    year: "numeric",
                                },
                            )}
                        </div>
                        <div class="flex flex-col gap-1">
                            {#each events as e}
                                <div class="flex items-center gap-2">
                                    <span class="text-sm"
                                        >{e.metadata.name}</span
                                    >
                                    <span
                                        class="text-xs px-2 py-0.5 rounded-full bg-[#1a1714] text-[#9a9080]"
                                        >{e.metadata.tag}</span
                                    >
                                    {#if e.metadata.notes}
                                        <span
                                            class="text-xs text-[#9a9080] truncate"
                                            >{e.metadata.notes}</span
                                        >
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    </div>
                {/each}
            </div>
        {/if}
    </section>

    <section class="mb-10">
        <div class="flex items-center gap-4 mb-4">
            <h2 class="text-xl font-semibold">Movie Diary</h2>
            <button
                on:click={() => (showMovieForm = !showMovieForm)}
                class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-3 py-1 rounded-lg text-sm"
                >{showMovieForm ? "Cancel" : "+ Log movie"}</button
            >
            {#if movieStatus}
                <span class="text-sm text-[#9a9080]">{movieStatus}</span>
            {/if}
        </div>

        {#if showMovieForm}
            <div class="max-w-xl bg-[#242019] rounded-xl p-5 mb-6">
                <div class="flex flex-col gap-4">
                    <div class="flex gap-4">
                        <div class="flex flex-col gap-1">
                            <label class="text-xs text-[#9a9080]"
                                >Date watched</label
                            >
                            <input
                                type="date"
                                bind:value={movieDate}
                                class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
                            />
                        </div>
                        <div class="flex flex-col gap-1">
                            <label class="text-xs text-[#9a9080]">Rating</label>
                            <div class="flex gap-1 mt-1">
                                {#each [1, 2, 3, 4, 5] as n}
                                    <button
                                        on:click={() =>
                                            (movieRating =
                                                movieRating === n ? null : n)}
                                        class="text-lg {movieRating >= n
                                            ? 'text-[#c8a84b]'
                                            : 'text-[#3a3530]'}">★</button
                                    >
                                {/each}
                            </div>
                        </div>
                    </div>

                    <div class="flex flex-col gap-1 relative">
                        <label class="text-xs text-[#9a9080]"
                            >Search movie</label
                        >
                        <input
                            type="text"
                            bind:value={movieQuery}
                            on:input={() => {
                                clearTimeout(searchTimeout);
                                selectedMovie = null;
                                if (movieQuery.length < 2) {
                                    movieResults = [];
                                    return;
                                }
                                searchTimeout = setTimeout(async () => {
                                    const res = await fetch(
                                        `/api/movies/search?q=${encodeURIComponent(movieQuery)}`,
                                    );
                                    movieResults = await res.json();
                                }, 300);
                            }}
                            placeholder="Start typing a title…"
                            class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
                        />
                        {#if movieResults.length > 0 && !selectedMovie}
                            <div
                                class="absolute top-full left-0 right-0 mt-1 bg-[#2a2520] rounded-lg border border-[#3a3530] z-10 overflow-hidden"
                            >
                                {#each movieResults as r}
                                    <button
                                        class="w-full flex items-center gap-3 px-3 py-2 hover:bg-[#342f28] text-left"
                                        on:click={() => {
                                            selectedMovie = r;
                                            movieQuery = r.title;
                                            movieResults = [];
                                        }}
                                    >
                                        {#if r.poster_path}
                                            <img
                                                src="/api/img?url={encodeURIComponent(
                                                    'https://image.tmdb.org/t/p/w92' +
                                                        r.poster_path,
                                                )}"
                                                alt={r.title}
                                                class="w-8 h-12 object-cover rounded"
                                            />
                                        {:else}
                                            <div
                                                class="w-8 h-12 bg-[#1a1714] rounded"
                                            />
                                        {/if}
                                        <div>
                                            <div class="text-sm text-[#e8e0d0]">
                                                {r.title}
                                            </div>
                                            <div class="text-xs text-[#9a9080]">
                                                {r.year}
                                            </div>
                                        </div>
                                    </button>
                                {/each}
                            </div>
                        {/if}
                    </div>

                    <div class="flex flex-col gap-1">
                        <label class="text-xs text-[#9a9080]">Notes</label>
                        <input
                            type="text"
                            bind:value={movieNotes}
                            placeholder="Optional"
                            class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
                        />
                    </div>

                    <button
                        on:click={async () => {
                            if (!selectedMovie) {
                                movieStatus =
                                    "Pick a movie from the search results";
                                return;
                            }
                            movieStatus = "saving…";
                            const res = await fetch("/api/movies/log", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    date: movieDate,
                                    title: selectedMovie.title,
                                    tmdb_id: selectedMovie.tmdb_id,
                                    year: selectedMovie.year,
                                    poster_path: selectedMovie.poster_path,
                                    genres: selectedMovie.genre_ids,
                                    rating: movieRating,
                                    notes: movieNotes,
                                    overview: selectedMovie.overview,
                                }),
                            });
                            const data = await res.json();
                            movieStatus = data.count
                                ? "Saved!"
                                : "Error saving";
                            movies = await (
                                await fetch(
                                    `/api/events?source=movies&event_type=watch`,
                                )
                            ).json();
                            movieQuery = "";
                            selectedMovie = null;
                            movieRating = null;
                            movieNotes = "";
                            showMovieForm = false;
                        }}
                        class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-2 rounded-lg text-sm self-start"
                        >Save</button
                    >
                </div>
            </div>
        {/if}
        {#if availableGenres.length > 0}
            <div class="flex flex-wrap gap-2 mb-4 max-w-2xl">
                {#each availableGenres as id}
                    <button
                        on:click={() => {
                            if (selectedGenres.has(id)) {
                                selectedGenres.delete(id);
                            } else {
                                selectedGenres.add(id);
                            }
                            selectedGenres = selectedGenres;
                        }}
                        class="px-3 py-1 rounded-full text-xs {selectedGenres.has(
                            id,
                        )
                            ? 'bg-[#3d2e1a] text-[#c89a5a]'
                            : 'bg-[#242019] text-[#9a9080] hover:text-[#e8e0d0]'}"
                        >{TMDB_GENRES[id]}</button
                    >
                {/each}
            </div>
        {/if}

        {#if filteredMovies.length === 0}
            <p class="text-sm text-[#9a9080]">No movies logged yet.</p>
        {:else}
            <div class="grid grid-cols-4 gap-3 max-w-2xl">
                {#each filteredMovies as m}
                    <button
                        class="flex flex-col gap-1 text-left"
                        title="{m.metadata.title} ({m.metadata.year})"
                        on:click={() => (expandedMovie = m)}
                    >
                        {#if m.metadata.poster_path}
                            <img
                                src="/api/img?url={encodeURIComponent(
                                    'https://image.tmdb.org/t/p/w342' +
                                        m.metadata.poster_path,
                                )}"
                                alt={m.metadata.title}
                                class="rounded-lg w-full aspect-[2/3] object-cover"
                            />
                        {:else}
                            <div
                                class="rounded-lg w-full aspect-[2/3] bg-[#242019] flex items-center justify-center text-xs text-[#9a9080] text-center p-2"
                            >
                                {m.metadata.title}
                            </div>
                        {/if}
                        <div class="text-xs text-[#e8e0d0] truncate">
                            {m.metadata.title}
                        </div>
                        <div class="flex items-center gap-1">
                            {#if m.metadata.rating}
                                <span class="text-xs text-[#c8a84b]"
                                    >{"★".repeat(m.metadata.rating)}</span
                                >
                            {/if}
                            <span class="text-xs text-[#9a9080]"
                                >{m.metadata.year}</span
                            >
                        </div>
                    </button>
                {/each}
            </div>
        {/if}
    </section>
    {#if expandedMovie}
        <div
            class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-8"
            on:click={() => (expandedMovie = null)}
        >
            <div
                class="bg-[#242019] rounded-2xl overflow-hidden max-w-2xl w-full flex gap-0 shadow-2xl"
                on:click|stopPropagation
            >
                {#if expandedMovie.metadata.poster_path}
                    <img
                        src="/api/img?url={encodeURIComponent(
                            'https://image.tmdb.org/t/p/w342' +
                                expandedMovie.metadata.poster_path,
                        )}"
                        alt={expandedMovie.metadata.title}
                        class="w-48 shrink-0 object-cover"
                    />
                {:else}
                    <div class="w-48 shrink-0 bg-[#1a1714]" />
                {/if}
                <div class="flex flex-col gap-3 p-6 flex-1 min-w-0">
                    <div class="flex items-start justify-between gap-2">
                        <div>
                            <div class="text-lg font-semibold">
                                {expandedMovie.metadata.title}
                            </div>
                            <div class="text-sm text-[#9a9080]">
                                {expandedMovie.metadata.year}
                            </div>
                        </div>
                        <button
                            on:click={() => (expandedMovie = null)}
                            class="text-[#9a9080] hover:text-[#e8e0d0] shrink-0"
                            >✕</button
                        >
                    </div>
                    {#if expandedMovie.metadata.rating}
                        <div class="text-[#c8a84b] text-xl">
                            {"★".repeat(
                                expandedMovie.metadata.rating,
                            )}{"☆".repeat(5 - expandedMovie.metadata.rating)}
                        </div>
                    {/if}
                    <div class="text-xs text-[#9a9080]">
                        Watched {new Date(
                            expandedMovie.timestamp,
                        ).toLocaleDateString("en-US", {
                            timeZone: "Asia/Kolkata",
                            month: "long",
                            day: "numeric",
                            year: "numeric",
                        })}
                    </div>
                    {#if expandedMovie.metadata.genres?.length}
                        <div class="flex flex-wrap gap-1">
                            {#each expandedMovie.metadata.genres as id}
                                {#if TMDB_GENRES[id]}
                                    <span
                                        class="text-xs px-2 py-0.5 rounded-full bg-[#1a1714] text-[#9a9080]"
                                        >{TMDB_GENRES[id]}</span
                                    >
                                {/if}
                            {/each}
                        </div>
                    {/if}
                    {#if expandedMovie.metadata.overview}
                        <p class="text-xs text-[#9a9080] leading-relaxed">
                            {expandedMovie.metadata.overview}
                        </p>
                    {/if}
                    {#if expandedMovie.metadata.notes}
                        <p class="text-sm text-[#c8c0b0]">
                            {expandedMovie.metadata.notes}
                        </p>
                    {/if}
                    <button
                        on:click={async () => {
                            await fetch(`/api/events/${expandedMovie.id}`, {
                                method: "DELETE",
                            });
                            movies = await (
                                await fetch(
                                    `/api/events?source=movies&event_type=watch`,
                                )
                            ).json();
                            expandedMovie = null;
                        }}
                        class="mt-auto text-xs text-[#c87a7a] hover:text-[#e87a7a] self-start"
                        >Delete</button
                    >
                </div>
            </div>
        </div>
    {/if}
</main>
