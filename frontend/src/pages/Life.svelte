<script>
    import { onMount } from "svelte";
    import { istDate, todayIST, fmtDate } from "../lib/ist.js";

    let calendarEvents = [];
    let backfillDate = "";
    let backfillStatus = "";

    const today = new Date();
    let viewYear = today.getFullYear();
    let viewMonth = today.getMonth();
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

    const MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

    const CAL_COLORS = {
        Projects:          { bg: "#1f2c1c", text: "#8aab84" },
        "Gym / Sports":    { bg: "#2e2a1a", text: "#c8a84b" },
        College:           { bg: "#1c2630", text: "#8aaabb" },
        Slots:             { bg: "#2c1c18", text: "#c4948a" },
        "Side projects":   { bg: "#22182a", text: "#a898b8" },
        "Courses & Studies": { bg: "#2a2818", text: "#c4b87a" },
        "Test & ICAs":     { bg: "#182626", text: "#7aacaa" },
    };
    const DEFAULT_COLOR = { bg: "#252220", text: "#9a8878" };

    const TMDB_GENRES = {
        28:"Action",12:"Adventure",16:"Animation",35:"Comedy",80:"Crime",
        99:"Documentary",18:"Drama",10751:"Family",14:"Fantasy",36:"History",
        27:"Horror",10402:"Music",9648:"Mystery",10749:"Romance",878:"Sci-Fi",
        53:"Thriller",10752:"War",37:"Western",
    };

    let movies = [];
    let watchlist = [];
    let movieView = 'watched';
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

    let watchlistQuery = "";
    let watchlistResults = [];
    let watchlistSearchTimeout = null;
    let selectedWatchlistMovie = null;
    let watchlistStatus = "";

    let editNotes = "";
    let editRating = null;
    let editSaving = false;
    let markingWatched = false;

    $: if (expandedMovie) {
        editNotes  = expandedMovie.metadata.notes  ?? "";
        editRating = expandedMovie.metadata.rating ?? null;
    }

    function calColor(name) { return CAL_COLORS[name] || DEFAULT_COLOR; }

    function isoDate(d) {
        return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
    }

    function isToday(d) { return isoDate(d) === isoDate(today); }

    function formatDuration(mins) {
        if (!mins) return "";
        const h = Math.floor(mins / 60), m = mins % 60;
        if (h === 0) return `${m}m`;
        if (m === 0) return `${h}h`;
        return `${h}h ${m}m`;
    }

    function timeAgo(ts) {
        if (new Date(ts) > Date.now()) {
            const secs = Math.floor((new Date(ts) - Date.now()) / 1000);
            if (secs < 86400) return `in ${Math.floor(secs/3600)}h`;
            return `in ${Math.floor(secs/86400)}d`;
        }
        const secs = Math.floor((Date.now() - new Date(ts)) / 1000);
        if (secs < 3600) return `${Math.floor(secs/60)}m ago`;
        if (secs < 86400) return `${Math.floor(secs/3600)}h ago`;
        const days = Math.floor(secs / 86400);
        if (days < 30) return `${days}d ago`;
        return fmtDate(ts);
    }

    function prevMonth() {
        if (viewMonth === 0) { viewMonth = 11; viewYear--; } else viewMonth--;
    }
    function nextMonth() {
        if (viewMonth === 11) { viewMonth = 0; viewYear++; } else viewMonth++;
    }

    $: calendarGrid = (() => {
        const first = new Date(viewYear, viewMonth, 1);
        const last  = new Date(viewYear, viewMonth + 1, 0);
        const startDow = first.getDay();
        const prefix = startDow === 0 ? 6 : startDow - 1;
        const cells = [];
        for (let i = prefix; i > 0; i--) cells.push({ date: new Date(viewYear, viewMonth, 1-i), inMonth: false });
        for (let d = 1; d <= last.getDate(); d++) cells.push({ date: new Date(viewYear, viewMonth, d), inMonth: true });
        while (cells.length % 7 !== 0) {
            const n = cells.length - last.getDate() - prefix + 1;
            cells.push({ date: new Date(viewYear, viewMonth+1, n), inMonth: false });
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
        const evs = calendarEvents.filter(e => {
            const d = new Date(e.timestamp);
            return d.getMonth() === viewMonth && d.getFullYear() === viewYear;
        });
        return {
            sessions: evs.length,
            hours: evs.reduce((s,e) => s + (e.metadata.duration_minutes || 0), 0) / 60,
            days: new Set(evs.map(e => istDate(e.timestamp))).size,
        };
    })();

    $: meetupsByDate = (() => {
        const map = {};
        for (const e of peopleEvents) {
            const key = istDate(e.timestamp);
            if (!map[key]) map[key] = [];
            map[key].push(e);
        }
        return Object.entries(map).sort(([a],[b]) => b.localeCompare(a));
    })();

    $: availableGenres = [...new Set(movies.flatMap(m => m.metadata.genres || []))].filter(id => TMDB_GENRES[id]);

    $: filteredMovies = selectedGenres.size === 0
        ? movies
        : movies.filter(m => (m.metadata.genres || []).some(id => selectedGenres.has(id)));

    onMount(async () => {
        const [calRes, gymRes, peopleRes, peopleSumRes, moviesRes] = await Promise.all([
            fetch("/api/events?source=calendar&event_type=event"),
            fetch("/api/events?source=gym&event_type=session"),
            fetch("/api/events?source=people&event_type=meetup"),
            fetch("/api/people/summary"),
            fetch("/api/events?source=movies&event_type=watch"),
        ]);
        calendarEvents = await calRes.json();
        gymSessions    = await gymRes.json();
        peopleEvents   = await peopleRes.json();
        peopleSummary  = await peopleSumRes.json();
        movies         = await moviesRes.json();
        watchlist      = await (await fetch("/api/events?source=movies&event_type=watchlist")).json();
    });
</script>

<main class="p-6 min-h-screen" style="background:#13120f; color:#e8e0d0; font-family:system-ui,sans-serif">

    <!-- Header -->
    <div class="flex items-center justify-between mb-5">
        <h1 class="text-2xl font-semibold tracking-tight">Life</h1>
        <div class="flex items-center gap-2">
            <input type="date" bind:value={backfillDate}
                class="rounded-lg px-3 py-1.5 text-sm border"
                style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823" />
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
                    calendarEvents = await (await fetch("/api/events?source=calendar&event_type=event")).json();
                }}
                class="px-3 py-1.5 rounded-lg text-sm font-medium"
                style="background:#2e2a1a; color:#c8a84b; border:1px solid #3e3a2a">
                Backfill
            </button>
            {#if backfillStatus}
                <span class="text-sm" style="color:#9a9080">{backfillStatus}</span>
            {/if}
        </div>
    </div>

    <!-- Bento grid -->
    <div class="grid gap-4" style="grid-template-columns: repeat(10, 1fr)">

        <!-- ── Calendar ── col 1-7 -->
        <div class="rounded-2xl p-5 flex flex-col h-[560px]"
             style="grid-column:1/8; background:#1c1b17; border:1px solid #2a2823">

            <!-- Panel header -->
            <div class="flex items-center justify-between mb-4">
                <div class="text-[11px] font-medium uppercase tracking-widest" style="color:#6a6058">Calendar</div>
                <div class="flex items-center gap-4">
                    {#if monthStats.sessions > 0}
                        <span class="text-[11px]" style="color:#9a9080">
                            {monthStats.sessions} events · {monthStats.hours.toFixed(1)}h · {monthStats.days}d active
                        </span>
                    {/if}
                    <div class="flex items-center gap-2">
                        <button on:click={prevMonth}
                            class="w-7 h-7 flex items-center justify-center rounded-lg text-sm transition-colors"
                            style="background:#151411; color:#9a9080">←</button>
                        <span class="text-sm font-medium w-32 text-center">{MONTH_NAMES[viewMonth]} {viewYear}</span>
                        <button on:click={nextMonth}
                            class="w-7 h-7 flex items-center justify-center rounded-lg text-sm"
                            style="background:#151411; color:#9a9080">→</button>
                    </div>
                </div>
            </div>

            <div class="overflow-y-auto flex-1 min-h-0 no-scroll">
            <!-- DOW row -->
            <div class="grid grid-cols-7 gap-1 mb-1.5">
                {#each DOW as dow}
                    <div class="text-center text-[10px] font-medium" style="color:#3a3428">{dow}</div>
                {/each}
            </div>

            <!-- Calendar grid -->
            <div class="grid grid-cols-7 gap-1">
                {#each calendarGrid as cell}
                    {@const dateKey = isoDate(cell.date)}
                    {@const events = eventsByDate[dateKey] || []}
                    {@const todayCell = isToday(cell.date)}
                    <div
                        class="rounded-xl p-1.5 min-h-[64px] flex flex-col cursor-pointer transition-colors"
                        style="background:{cell.inMonth ? '#151411' : '#111009'};
                               {todayCell ? 'outline:1.5px solid #c8a84b;' : ''}
                               {selectedDay === dateKey ? 'outline:1.5px solid #c8a84b;' : ''}"
                        on:click={() => selectedDay = selectedDay === dateKey ? null : dateKey}
                    >
                        <div class="text-[10px] mb-0.5 font-medium"
                             style="color:{todayCell ? '#c8a84b' : cell.inMonth ? '#5a5248' : '#252220'}">
                            {cell.date.getDate()}
                        </div>
                        {#each events.slice(0, 2) as e}
                            <div class="text-[9px] rounded px-1 py-0.5 mb-0.5 truncate leading-tight"
                                 style="background:{calColor(e.metadata.calendar_name).bg}; color:{calColor(e.metadata.calendar_name).text}"
                                 title="{e.metadata.title} ({formatDuration(e.metadata.duration_minutes)})">
                                {e.metadata.title}
                            </div>
                        {/each}
                        {#if events.length > 2}
                            <div class="text-[9px]" style="color:#4a4238">+{events.length - 2}</div>
                        {/if}
                    </div>
                {/each}
            </div>

            <!-- Day detail -->
            {#if selectedDay}
                {@const dayEvents = eventsByDate[selectedDay] || []}
                <div class="mt-3 rounded-xl p-4" style="background:#151411">
                    <div class="flex items-center justify-between mb-3">
                        <span class="text-xs font-medium">
                            {new Date(selectedDay + "T12:00:00").toLocaleDateString("en-US", {
                                timeZone: "Asia/Kolkata", weekday: "long", month: "long", day: "numeric",
                            })}
                        </span>
                        <button on:click={() => selectedDay = null} class="text-xs" style="color:#6a6058">✕</button>
                    </div>
                    {#if dayEvents.length === 0}
                        <p class="text-xs" style="color:#6a6058">No events</p>
                    {:else}
                        <div class="flex flex-col gap-2">
                            {#each dayEvents as e}
                                {@const color = calColor(e.metadata.calendar_name)}
                                <div class="flex items-center gap-3 px-3 py-2 rounded-xl" style="background:{color.bg}">
                                    <div class="flex-1 min-w-0">
                                        <div class="text-xs font-medium truncate" style="color:{color.text}">{e.metadata.title}</div>
                                        <div class="text-[10px] mt-0.5" style="color:#9a9080">
                                            {e.metadata.calendar_name}{#if e.metadata.duration_minutes} · {formatDuration(e.metadata.duration_minutes)}{/if}
                                        </div>
                                    </div>
                                    {#if e.metadata.duration_minutes}
                                        <span class="text-[10px] shrink-0" style="color:{color.text}">{formatDuration(e.metadata.duration_minutes)}</span>
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    {/if}
                </div>
            {/if}
            </div><!-- /calendar scroll -->
        </div>

        <!-- ── People ── col 8-10 -->
        <div class="rounded-2xl p-5 flex flex-col h-[560px]"
             style="grid-column:8/11; background:#1c1b17; border:1px solid #2a2823">

            <!-- Panel header -->
            <div class="flex items-center justify-between mb-3">
                <div class="text-[11px] font-medium uppercase tracking-widest" style="color:#6a6058">People</div>
                <div class="flex items-center gap-1.5">
                    <div class="flex gap-0.5 rounded-lg overflow-hidden" style="background:#151411">
                        <button on:click={() => peopleView = 'people'}
                            class="px-2.5 py-1 text-[11px] transition-colors"
                            style="background:{peopleView === 'people' ? '#252320' : 'transparent'}; color:{peopleView === 'people' ? '#e8e0d0' : '#6a6058'}">
                            People
                        </button>
                        <button on:click={() => peopleView = 'events'}
                            class="px-2.5 py-1 text-[11px] transition-colors"
                            style="background:{peopleView === 'events' ? '#252320' : 'transparent'}; color:{peopleView === 'events' ? '#e8e0d0' : '#6a6058'}">
                            Events
                        </button>
                    </div>
                    <button on:click={() => showPeopleForm = !showPeopleForm}
                        class="px-2.5 py-1 rounded-lg text-[11px] font-medium"
                        style="background:#2e2a1a; color:#c8a84b">
                        {showPeopleForm ? 'Cancel' : '+ Log'}
                    </button>
                </div>
            </div>

            <div class="overflow-y-auto flex-1 min-h-0 no-scroll">
            {#if peopleStatus}
                <div class="text-[11px] mb-2" style="color:#9a9080">{peopleStatus}</div>
            {/if}

            <!-- Log form -->
            {#if showPeopleForm}
                <div class="rounded-xl p-3 mb-3 flex flex-col gap-3" style="background:#151411">
                    <div class="flex gap-2">
                        <div class="flex flex-col gap-1">
                            <label class="text-[10px]" style="color:#6a6058">Date</label>
                            <input type="date" bind:value={meetupDate}
                                class="rounded-lg px-2 py-1.5 text-xs border"
                                style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823" />
                        </div>
                        <div class="flex flex-col gap-1 flex-1">
                            <label class="text-[10px]" style="color:#6a6058">Notes</label>
                            <input type="text" bind:value={meetupNotes} placeholder="Coffee at Blue Tokai…"
                                class="rounded-lg px-2 py-1.5 text-xs border"
                                style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823" />
                        </div>
                    </div>
                    <div class="flex flex-col gap-1.5">
                        <label class="text-[10px]" style="color:#6a6058">People</label>
                        {#each meetupPeople as person, i}
                            <div class="flex gap-1.5 items-center">
                                <input type="text" bind:value={person.name} placeholder="Name"
                                    class="rounded-lg px-2 py-1.5 text-xs border flex-1"
                                    style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823" />
                                <select bind:value={person.tag}
                                    class="rounded-lg px-2 py-1.5 text-xs border"
                                    style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823">
                                    {#each ['Friend','Family','Colleague','Other'] as t}
                                        <option>{t}</option>
                                    {/each}
                                </select>
                                {#if meetupPeople.length > 1}
                                    <button on:click={() => meetupPeople = meetupPeople.filter((_,j) => j !== i)}
                                        class="text-xs px-1" style="color:#6a6058">✕</button>
                                {/if}
                            </div>
                        {/each}
                        <button on:click={() => meetupPeople = [...meetupPeople, {name:'',tag:'Friend'}]}
                            class="text-[11px] self-start" style="color:#c8a84b">+ Add person</button>
                    </div>
                    <button
                        on:click={async () => {
                            const valid = meetupPeople.filter(p => p.name.trim());
                            if (!valid.length) return;
                            peopleStatus = "saving…";
                            const res = await fetch("/api/people/log", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ date: meetupDate, notes: meetupNotes, people: valid }),
                            });
                            const data = await res.json();
                            peopleStatus = `${data.count} logged`;
                            const [evRes, sumRes] = await Promise.all([
                                fetch("/api/events?source=people&event_type=meetup"),
                                fetch("/api/people/summary"),
                            ]);
                            peopleEvents  = await evRes.json();
                            peopleSummary = await sumRes.json();
                            meetupPeople  = [{ name: "", tag: "Friend" }];
                            meetupNotes   = "";
                            showPeopleForm = false;
                        }}
                        class="px-3 py-1.5 rounded-lg text-xs font-medium self-start"
                        style="background:#2e2a1a; color:#c8a84b">
                        Save
                    </button>
                </div>
            {/if}

            <!-- People / Events list -->
            {#if peopleView === 'people'}
                {#if peopleSummary.length === 0}
                    <p class="text-xs mt-2" style="color:#6a6058">No meetups logged yet.</p>
                {:else}
                    <div class="flex flex-col gap-1.5 overflow-y-auto">
                        {#each peopleSummary as person}
                            {@const days = Math.floor((Date.now() - new Date(person.last_seen)) / 86400000)}
                            {@const urgencyColor = days < 30 ? '#8aab84' : days < 90 ? '#c8a84b' : '#c4948a'}
                            {@const history = peopleEvents.filter(e => e.metadata.name === person.name)}
                            <div class="rounded-xl overflow-hidden" style="background:#151411">
                                <button class="w-full flex items-center gap-3 px-3 py-2.5 text-left"
                                    on:click={() => expandedPerson = expandedPerson === person.name ? null : person.name}>
                                    <div class="flex-1 min-w-0">
                                        <div class="flex items-center gap-1.5">
                                            <span class="text-sm font-medium">{person.name}</span>
                                            <span class="text-[10px] px-1.5 py-0.5 rounded-full" style="background:#1c1b17; color:#6a6058">{person.tag}</span>
                                        </div>
                                        {#if person.last_notes}
                                            <div class="text-[10px] mt-0.5 truncate" style="color:#6a6058">{person.last_notes}</div>
                                        {/if}
                                    </div>
                                    <div class="text-right shrink-0">
                                        <div class="text-xs font-medium" style="color:{urgencyColor}">
                                            {days === 0 ? 'today' : `${days}d ago`}
                                        </div>
                                        <div class="text-[10px]" style="color:#6a6058">{person.total_meetups} meetup{person.total_meetups !== 1 ? 's' : ''}</div>
                                    </div>
                                </button>
                                {#if expandedPerson === person.name}
                                    <div class="px-3 pb-3 flex flex-col gap-1.5" style="border-top:1px solid #2a2823">
                                        {#each history as e}
                                            <div class="flex items-start gap-2 mt-1.5">
                                                <span class="text-[10px] shrink-0 mt-0.5" style="color:#6a6058">
                                                    {new Date(e.timestamp).toLocaleDateString("en-US", {
                                                        timeZone:"Asia/Kolkata", month:"short", day:"numeric", year:"numeric"
                                                    })}
                                                </span>
                                                <span class="text-[11px] flex-1" style="color:#c8c0b0">{e.metadata.notes || '—'}</span>
                                                <button
                                                    on:click={async () => {
                                                        await fetch(`/api/events/${e.id}`, { method: "DELETE" });
                                                        const [evRes, sumRes] = await Promise.all([
                                                            fetch("/api/events?source=people&event_type=meetup"),
                                                            fetch("/api/people/summary"),
                                                        ]);
                                                        peopleEvents  = await evRes.json();
                                                        peopleSummary = await sumRes.json();
                                                    }}
                                                    class="text-[10px] shrink-0" style="color:#c4948a">✕</button>
                                            </div>
                                        {/each}
                                    </div>
                                {/if}
                            </div>
                        {/each}
                    </div>
                {/if}
            {:else if meetupsByDate.length === 0}
                <p class="text-xs mt-2" style="color:#6a6058">No meetups logged yet.</p>
            {:else}
                <div class="flex flex-col gap-2 overflow-y-auto">
                    {#each meetupsByDate as [date, events]}
                        <div class="rounded-xl px-3 py-2.5" style="background:#151411">
                            <div class="text-[10px] mb-2" style="color:#6a6058">
                                {new Date(date + "T12:00:00").toLocaleDateString("en-US", {
                                    timeZone:"Asia/Kolkata", weekday:"long", month:"long", day:"numeric", year:"numeric"
                                })}
                            </div>
                            <div class="flex flex-col gap-1">
                                {#each events as e}
                                    <div class="flex items-center gap-2">
                                        <span class="text-xs">{e.metadata.name}</span>
                                        <span class="text-[10px] px-1.5 py-0.5 rounded-full" style="background:#1c1b17; color:#9a9080">{e.metadata.tag}</span>
                                        {#if e.metadata.notes}
                                            <span class="text-[10px] truncate" style="color:#9a9080">{e.metadata.notes}</span>
                                        {/if}
                                    </div>
                                {/each}
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
            </div><!-- /people scroll -->
        </div>

        <!-- ── Gym ── col 1-4 -->
        <div class="rounded-2xl p-5 flex flex-col h-[420px]"
             style="grid-column:1/5; background:#1c1b17; border:1px solid #2a2823">

            <div class="flex items-center justify-between mb-3">
                <div class="text-[11px] font-medium uppercase tracking-widest" style="color:#6a6058">Gym</div>
                <div class="flex items-center gap-2">
                    {#if gymStatus}<span class="text-[11px]" style="color:#9a9080">{gymStatus}</span>{/if}
                    <button on:click={() => showGymForm = !showGymForm}
                        class="px-2.5 py-1 rounded-lg text-[11px] font-medium"
                        style="background:#2e2a1a; color:#c8a84b">
                        {showGymForm ? 'Cancel' : '+ Log'}
                    </button>
                </div>
            </div>

            <div class="overflow-y-auto flex-1 min-h-0 no-scroll">
            {#if showGymForm}
                <div class="rounded-xl p-3 mb-3 flex flex-col gap-3" style="background:#151411">
                    <div class="flex gap-3">
                        <div class="flex flex-col gap-1 flex-1">
                            <label class="text-[10px]" style="color:#6a6058">Date</label>
                            <input type="date" bind:value={gymDate}
                                class="rounded-lg px-2 py-1.5 text-xs border"
                                style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823" />
                        </div>
                        <div class="flex flex-col gap-1">
                            <label class="text-[10px]" style="color:#6a6058">Type</label>
                            <div class="flex gap-1.5">
                                {#each ['workout','run'] as t}
                                    <button on:click={() => gymType = t}
                                        class="px-2.5 py-1.5 rounded-lg text-xs capitalize"
                                        style="background:{gymType === t ? '#2e2a1a' : '#1c1b17'}; color:{gymType === t ? '#c8a84b' : '#9a9080'}; border:1px solid {gymType === t ? '#3e3a2a' : '#2a2823'}">
                                        {t}
                                    </button>
                                {/each}
                            </div>
                        </div>
                    </div>

                    {#if gymType === 'workout'}
                        <div class="flex flex-col gap-1.5">
                            <label class="text-[10px]" style="color:#6a6058">Muscle groups</label>
                            <div class="flex flex-wrap gap-1.5">
                                {#each ['Chest','Back','Shoulders','Biceps','Triceps','Legs','Core','Forearms','Calisthenics','Boxing'] as muscle}
                                    <button
                                        on:click={() => gymMuscles = gymMuscles.includes(muscle) ? gymMuscles.filter(m => m !== muscle) : [...gymMuscles, muscle]}
                                        class="px-2 py-0.5 rounded-full text-[10px]"
                                        style="background:{gymMuscles.includes(muscle) ? '#2e2a1a' : '#1c1b17'}; color:{gymMuscles.includes(muscle) ? '#c8a84b' : '#6a6058'}; border:1px solid {gymMuscles.includes(muscle) ? '#3e3a2a' : '#252320'}">
                                        {muscle}
                                    </button>
                                {/each}
                            </div>
                        </div>
                    {:else}
                        <div class="flex flex-col gap-1">
                            <label class="text-[10px]" style="color:#6a6058">Distance (km)</label>
                            <input type="number" bind:value={gymDistance} placeholder="5.0" step="0.1"
                                class="rounded-lg px-2 py-1.5 text-xs border w-24"
                                style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823" />
                        </div>
                    {/if}

                    <div class="flex gap-3">
                        <div class="flex flex-col gap-1">
                            <label class="text-[10px]" style="color:#6a6058">Duration (min)</label>
                            <input type="number" bind:value={gymDuration} placeholder="60"
                                class="rounded-lg px-2 py-1.5 text-xs border w-20"
                                style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823" />
                        </div>
                        <div class="flex flex-col gap-1 flex-1">
                            <label class="text-[10px]" style="color:#6a6058">Notes</label>
                            <input type="text" bind:value={gymNotes} placeholder="Optional"
                                class="rounded-lg px-2 py-1.5 text-xs border"
                                style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823" />
                        </div>
                    </div>

                    <button
                        on:click={async () => {
                            gymStatus = "saving…";
                            const res = await fetch("/api/gym/log", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                    date: gymDate, type: gymType,
                                    muscle_groups: gymMuscles,
                                    distance_km: gymDistance ? parseFloat(gymDistance) : null,
                                    duration_minutes: gymDuration ? parseInt(gymDuration) : null,
                                    notes: gymNotes,
                                }),
                            });
                            const data = await res.json();
                            gymStatus = data.count ? "Saved!" : "Already logged";
                            gymSessions = await (await fetch("/api/events?source=gym&event_type=session")).json();
                            gymMuscles = []; gymDistance = ""; gymDuration = ""; gymNotes = "";
                            showGymForm = false;
                        }}
                        class="px-3 py-1.5 rounded-lg text-xs font-medium self-start"
                        style="background:#2e2a1a; color:#c8a84b">
                        Save
                    </button>
                </div>
            {/if}

            {#if gymSessions.length === 0}
                <p class="text-xs" style="color:#6a6058">No sessions logged yet.</p>
            {:else}
                <div class="flex flex-col gap-1.5">
                    {#each gymSessions as s}
                        <div class="flex items-center gap-3 px-3 py-2.5 rounded-xl" style="background:#151411">
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-1.5 flex-wrap">
                                    <span class="text-sm font-medium capitalize">{s.metadata.type}</span>
                                    {#each s.metadata.muscle_groups || [] as m}
                                        <span class="text-[10px] px-1.5 py-0.5 rounded-full" style="background:#2e2a1a; color:#c8a84b">{m}</span>
                                    {/each}
                                    {#if s.metadata.distance_km}
                                        <span class="text-[10px]" style="color:#9a9080">{s.metadata.distance_km} km</span>
                                    {/if}
                                </div>
                                {#if s.metadata.notes}
                                    <div class="text-[10px] mt-0.5" style="color:#6a6058">{s.metadata.notes}</div>
                                {/if}
                            </div>
                            <div class="text-right shrink-0">
                                {#if s.metadata.duration_minutes}
                                    <div class="text-xs font-medium" style="color:#c8a84b">{formatDuration(s.metadata.duration_minutes)}</div>
                                {/if}
                                <div class="text-[10px]" style="color:#6a6058">{timeAgo(s.timestamp)}</div>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
            </div><!-- /gym scroll -->
        </div>

        <!-- ── Movies ── col 5-10 -->
        <div class="rounded-2xl p-5 flex flex-col h-[420px]"
             style="grid-column:5/11; background:#1c1b17; border:1px solid #2a2823">

            <!-- Panel header -->
            <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-3">
                    <div class="text-[11px] font-medium uppercase tracking-widest" style="color:#6a6058">Movies</div>
                    <div class="flex gap-0.5 rounded-lg overflow-hidden" style="background:#151411">
                        <button on:click={() => { movieView = 'watched'; showMovieForm = false; }}
                            class="px-2.5 py-1 text-[11px] transition-colors"
                            style="background:{movieView === 'watched' ? '#252320' : 'transparent'}; color:{movieView === 'watched' ? '#e8e0d0' : '#6a6058'}">
                            Watched
                        </button>
                        <button on:click={() => { movieView = 'towatch'; showMovieForm = false; }}
                            class="px-2.5 py-1 text-[11px] transition-colors"
                            style="background:{movieView === 'towatch' ? '#252320' : 'transparent'}; color:{movieView === 'towatch' ? '#e8e0d0' : '#6a6058'}">
                            To Watch
                        </button>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    {#if movieView === 'watched'}
                        {#if movieStatus}<span class="text-[11px]" style="color:#9a9080">{movieStatus}</span>{/if}
                        <button on:click={() => showMovieForm = !showMovieForm}
                            class="px-2.5 py-1 rounded-lg text-[11px] font-medium"
                            style="background:#2e2a1a; color:#c8a84b">
                            {showMovieForm ? 'Cancel' : '+ Log'}
                        </button>
                    {:else}
                        {#if watchlistStatus}<span class="text-[11px]" style="color:#9a9080">{watchlistStatus}</span>{/if}
                        <button on:click={() => { watchlistQuery = ''; watchlistResults = []; selectedWatchlistMovie = null; }}
                            class="px-2.5 py-1 rounded-lg text-[11px] font-medium"
                            style="background:#2e2a1a; color:#c8a84b">
                            + Add
                        </button>
                    {/if}
                </div>
            </div>

            <div class="overflow-y-auto flex-1 min-h-0 no-scroll">

            {#if movieView === 'watched'}

                <!-- Genre filter chips -->
                {#if availableGenres.length > 0 && !showMovieForm}
                    <div class="flex flex-wrap gap-1.5 mb-3">
                        {#each availableGenres as id}
                            <button
                                on:click={() => { if (selectedGenres.has(id)) selectedGenres.delete(id); else selectedGenres.add(id); selectedGenres = selectedGenres; }}
                                class="px-2 py-0.5 rounded-full text-[10px]"
                                style="background:{selectedGenres.has(id) ? '#2e2a1a' : '#151411'}; color:{selectedGenres.has(id) ? '#c8a84b' : '#6a6058'}; border:1px solid {selectedGenres.has(id) ? '#3e3a2a' : '#252320'}">
                                {TMDB_GENRES[id]}
                            </button>
                        {/each}
                    </div>
                {/if}

                <!-- Log watched form -->
                {#if showMovieForm}
                    <div class="rounded-xl p-3 mb-3 flex flex-col gap-3" style="background:#151411">
                        <div class="flex gap-4">
                            <div class="flex flex-col gap-1">
                                <label class="text-[10px]" style="color:#6a6058">Date watched</label>
                                <input type="date" bind:value={movieDate}
                                    class="rounded-lg px-2 py-1.5 text-xs border"
                                    style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823" />
                            </div>
                            <div class="flex flex-col gap-1">
                                <label class="text-[10px]" style="color:#6a6058">Rating</label>
                                <div class="flex gap-0.5 mt-1">
                                    {#each [1,2,3,4,5] as n}
                                        <button on:click={() => movieRating = movieRating === n ? null : n}
                                            class="text-lg leading-none" style="color:{movieRating >= n ? '#c8a84b' : '#2a2823'}">★</button>
                                    {/each}
                                </div>
                            </div>
                        </div>
                        <div class="flex flex-col gap-1 relative">
                            <label class="text-[10px]" style="color:#6a6058">Search movie</label>
                            <input type="text" bind:value={movieQuery}
                                on:input={() => {
                                    clearTimeout(searchTimeout);
                                    selectedMovie = null;
                                    if (movieQuery.length < 2) { movieResults = []; return; }
                                    searchTimeout = setTimeout(async () => {
                                        const res = await fetch(`/api/movies/search?q=${encodeURIComponent(movieQuery)}`);
                                        movieResults = await res.json();
                                    }, 300);
                                }}
                                placeholder="Start typing a title…"
                                class="rounded-lg px-2 py-1.5 text-xs border"
                                style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823" />
                            {#if movieResults.length > 0 && !selectedMovie}
                                <div class="absolute top-full left-0 right-0 mt-1 rounded-xl border z-10 overflow-hidden"
                                     style="background:#1e1d1a; border-color:#2a2823">
                                    {#each movieResults as r}
                                        <button class="w-full flex items-center gap-3 px-3 py-2 text-left transition-colors"
                                            on:click={() => { selectedMovie = r; movieQuery = r.title; movieResults = []; }}>
                                            {#if r.poster_path}
                                                <img src="/api/img?url={encodeURIComponent('https://image.tmdb.org/t/p/w92' + r.poster_path)}"
                                                    alt={r.title} class="w-7 h-10 object-cover rounded" />
                                            {:else}
                                                <div class="w-7 h-10 rounded" style="background:#151411"></div>
                                            {/if}
                                            <div>
                                                <div class="text-xs">{r.title}</div>
                                                <div class="text-[10px]" style="color:#9a9080">{r.year}</div>
                                            </div>
                                        </button>
                                    {/each}
                                </div>
                            {/if}
                        </div>
                        <div class="flex flex-col gap-1">
                            <label class="text-[10px]" style="color:#6a6058">Notes</label>
                            <input type="text" bind:value={movieNotes} placeholder="Optional"
                                class="rounded-lg px-2 py-1.5 text-xs border"
                                style="background:#1c1b17; color:#e8e0d0; border-color:#2a2823" />
                        </div>
                        <button
                            on:click={async () => {
                                if (!selectedMovie) { movieStatus = "Pick a movie from the results"; return; }
                                movieStatus = "saving…";
                                const res = await fetch("/api/movies/log", {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({
                                        date: movieDate, title: selectedMovie.title,
                                        tmdb_id: selectedMovie.tmdb_id, year: selectedMovie.year,
                                        poster_path: selectedMovie.poster_path,
                                        genres: selectedMovie.genre_ids,
                                        rating: movieRating, notes: movieNotes,
                                        overview: selectedMovie.overview,
                                    }),
                                });
                                const data = await res.json();
                                movieStatus = data.count ? "Saved!" : "Error saving";
                                movies = await (await fetch("/api/events?source=movies&event_type=watch")).json();
                                movieQuery = ""; selectedMovie = null; movieRating = null; movieNotes = "";
                                showMovieForm = false;
                            }}
                            class="px-3 py-1.5 rounded-lg text-xs font-medium self-start"
                            style="background:#2e2a1a; color:#c8a84b">
                            Save
                        </button>
                    </div>
                {/if}

                <!-- Watched poster grid -->
                {#if filteredMovies.length === 0}
                    <p class="text-xs" style="color:#6a6058">No movies logged yet.</p>
                {:else}
                    <div class="grid gap-3" style="grid-template-columns: repeat(auto-fill, minmax(120px, 1fr))">
                        {#each filteredMovies as m}
                            <button class="flex flex-col gap-1 text-left group"
                                title="{m.metadata.title} ({m.metadata.year})"
                                on:click={() => expandedMovie = m}>
                                {#if m.metadata.poster_path}
                                    <img src="/api/img?url={encodeURIComponent('https://image.tmdb.org/t/p/w342' + m.metadata.poster_path)}"
                                        alt={m.metadata.title}
                                        class="rounded-xl w-full aspect-[2/3] object-cover transition-opacity group-hover:opacity-80" />
                                {:else}
                                    <div class="rounded-xl w-full aspect-[2/3] flex items-center justify-center text-[10px] text-center p-2"
                                         style="background:#151411; color:#6a6058">{m.metadata.title}</div>
                                {/if}
                                <div class="text-[10px] truncate" style="color:#c8c0b0">{m.metadata.title}</div>
                                <div class="flex items-center gap-1">
                                    {#if m.metadata.rating}
                                        <span class="text-[10px]" style="color:#c8a84b">{"★".repeat(m.metadata.rating)}</span>
                                    {/if}
                                    <span class="text-[10px]" style="color:#6a6058">{m.metadata.year}</span>
                                </div>
                            </button>
                        {/each}
                    </div>
                {/if}

            {:else}

                <!-- To Watch: inline search -->
                <div class="flex flex-col gap-1 relative mb-3">
                    <input type="text" bind:value={watchlistQuery}
                        on:input={() => {
                            clearTimeout(watchlistSearchTimeout);
                            selectedWatchlistMovie = null;
                            if (watchlistQuery.length < 2) { watchlistResults = []; return; }
                            watchlistSearchTimeout = setTimeout(async () => {
                                const res = await fetch(`/api/movies/search?q=${encodeURIComponent(watchlistQuery)}`);
                                watchlistResults = await res.json();
                            }, 300);
                        }}
                        placeholder="Search a movie to add…"
                        class="rounded-lg px-3 py-2 text-xs border"
                        style="background:#151411; color:#e8e0d0; border-color:#2a2823" />
                    {#if watchlistResults.length > 0 && !selectedWatchlistMovie}
                        <div class="absolute top-full left-0 right-0 mt-1 rounded-xl border z-10 overflow-hidden"
                             style="background:#1e1d1a; border-color:#2a2823">
                            {#each watchlistResults as r}
                                <button class="w-full flex items-center gap-3 px-3 py-2 text-left transition-colors"
                                    on:click={async () => {
                                        watchlistStatus = "adding…";
                                        await fetch("/api/movies/watchlist", {
                                            method: "POST",
                                            headers: { "Content-Type": "application/json" },
                                            body: JSON.stringify({
                                                title: r.title, tmdb_id: r.tmdb_id,
                                                year: r.year, poster_path: r.poster_path,
                                            }),
                                        });
                                        watchlist = await (await fetch("/api/events?source=movies&event_type=watchlist")).json();
                                        watchlistQuery = ""; watchlistResults = []; selectedWatchlistMovie = null;
                                        watchlistStatus = "Added!";
                                        setTimeout(() => watchlistStatus = "", 2000);
                                    }}>
                                    {#if r.poster_path}
                                        <img src="/api/img?url={encodeURIComponent('https://image.tmdb.org/t/p/w92' + r.poster_path)}"
                                            alt={r.title} class="w-7 h-10 object-cover rounded" />
                                    {:else}
                                        <div class="w-7 h-10 rounded" style="background:#151411"></div>
                                    {/if}
                                    <div>
                                        <div class="text-xs">{r.title}</div>
                                        <div class="text-[10px]" style="color:#9a9080">{r.year}</div>
                                    </div>
                                </button>
                            {/each}
                        </div>
                    {/if}
                </div>

                <!-- To Watch poster grid -->
                {#if watchlist.length === 0}
                    <p class="text-xs" style="color:#6a6058">Nothing on your watchlist yet.</p>
                {:else}
                    <div class="grid gap-3" style="grid-template-columns: repeat(auto-fill, minmax(120px, 1fr))">
                        {#each watchlist as m}
                            <button class="flex flex-col gap-1 text-left group relative"
                                on:click={() => expandedMovie = m}>
                                {#if m.metadata.poster_path}
                                    <img src="/api/img?url={encodeURIComponent('https://image.tmdb.org/t/p/w342' + m.metadata.poster_path)}"
                                        alt={m.metadata.title}
                                        class="rounded-xl w-full aspect-[2/3] object-cover transition-opacity group-hover:opacity-80" />
                                {:else}
                                    <div class="rounded-xl w-full aspect-[2/3] flex items-center justify-center text-[10px] text-center p-2"
                                         style="background:#151411; color:#6a6058">{m.metadata.title}</div>
                                {/if}
                                <div class="text-[10px] truncate" style="color:#c8c0b0">{m.metadata.title}</div>
                                {#if m.metadata.year}
                                    <div class="text-[10px]" style="color:#6a6058">{m.metadata.year}</div>
                                {/if}
                            </button>
                        {/each}
                    </div>
                {/if}

            {/if}
            </div><!-- /movies scroll -->
        </div>

    </div><!-- /bento grid -->

    <!-- ── Movie detail modal ── -->
    {#if expandedMovie}
        {@const isWatchlist = expandedMovie.event_type === 'watchlist'}
        <div class="fixed inset-0 z-50 flex items-center justify-center p-8"
             style="background:rgba(0,0,0,0.75)"
             on:click={() => expandedMovie = null}>
            <div class="rounded-2xl overflow-hidden max-w-2xl w-full flex shadow-2xl"
                 style="background:#1c1b17"
                 on:click|stopPropagation>
                {#if expandedMovie.metadata.poster_path}
                    <img src="/api/img?url={encodeURIComponent('https://image.tmdb.org/t/p/w342' + expandedMovie.metadata.poster_path)}"
                        alt={expandedMovie.metadata.title}
                        class="w-48 shrink-0 object-cover" />
                {:else}
                    <div class="w-48 shrink-0" style="background:#151411"></div>
                {/if}
                <div class="flex flex-col gap-3 p-6 flex-1 min-w-0">

                    <!-- Title row -->
                    <div class="flex items-start justify-between gap-2">
                        <div>
                            <div class="text-lg font-semibold">{expandedMovie.metadata.title}</div>
                            <div class="text-sm" style="color:#9a9080">{expandedMovie.metadata.year}</div>
                        </div>
                        <button on:click={() => expandedMovie = null} class="text-sm shrink-0" style="color:#6a6058">✕</button>
                    </div>

                    <!-- Watched date (watched only) -->
                    {#if !isWatchlist}
                        <div class="text-xs" style="color:#9a9080">
                            Watched {new Date(expandedMovie.timestamp).toLocaleDateString("en-US", {
                                timeZone: "Asia/Kolkata", month: "long", day: "numeric", year: "numeric"
                            })}
                        </div>
                    {:else}
                        <div class="text-[10px] px-2 py-1 rounded-lg self-start" style="background:#1a2a3d; color:#6b9ecc">To Watch</div>
                    {/if}

                    <!-- Rating (watched only) -->
                    {#if !isWatchlist}
                        <div>
                            <div class="text-[10px] mb-1" style="color:#6a6058">Rating</div>
                            <div class="flex gap-1">
                                {#each [1,2,3,4,5] as n}
                                    <button on:click={() => editRating = editRating === n ? null : n}
                                        class="text-xl leading-none"
                                        style="color:{editRating >= n ? '#c8a84b' : '#2a2823'}">★</button>
                                {/each}
                            </div>
                        </div>
                    {/if}

                    <!-- Genres -->
                    {#if expandedMovie.metadata.genres?.length}
                        <div class="flex flex-wrap gap-1">
                            {#each expandedMovie.metadata.genres as id}
                                {#if TMDB_GENRES[id]}
                                    <span class="text-[10px] px-2 py-0.5 rounded-full" style="background:#151411; color:#9a9080">{TMDB_GENRES[id]}</span>
                                {/if}
                            {/each}
                        </div>
                    {/if}

                    <!-- Overview -->
                    {#if expandedMovie.metadata.overview}
                        <p class="text-xs leading-relaxed" style="color:#9a9080">{expandedMovie.metadata.overview}</p>
                    {/if}

                    <!-- Notes (editable) -->
                    <div>
                        <div class="text-[10px] mb-1" style="color:#6a6058">Notes</div>
                        <textarea
                            bind:value={editNotes}
                            placeholder="Add a note…"
                            rows="2"
                            class="w-full rounded-lg px-3 py-2 text-xs border resize-none"
                            style="background:#151411; color:#e8e0d0; border-color:#2a2823"
                        ></textarea>
                    </div>

                    <!-- Actions -->
                    <div class="flex items-center gap-3 mt-auto flex-wrap">
                        {#if isWatchlist}
                            <button
                                on:click={async () => {
                                    markingWatched = true;
                                    await fetch("/api/movies/log", {
                                        method: "POST",
                                        headers: { "Content-Type": "application/json" },
                                        body: JSON.stringify({
                                            date: isoDate(today),
                                            title: expandedMovie.metadata.title,
                                            tmdb_id: expandedMovie.metadata.tmdb_id,
                                            year: expandedMovie.metadata.year,
                                            poster_path: expandedMovie.metadata.poster_path,
                                            genres: expandedMovie.metadata.genres || [],
                                            overview: expandedMovie.metadata.overview || "",
                                            notes: editNotes,
                                        }),
                                    });
                                    await fetch(`/api/events/${expandedMovie.id}`, { method: "DELETE" });
                                    [movies, watchlist] = await Promise.all([
                                        fetch("/api/events?source=movies&event_type=watch").then(r => r.json()),
                                        fetch("/api/events?source=movies&event_type=watchlist").then(r => r.json()),
                                    ]);
                                    markingWatched = false;
                                    movieView = 'watched';
                                    expandedMovie = null;
                                }}
                                class="px-3 py-1.5 rounded-lg text-xs font-medium"
                                style="background:#2e2a1a; color:#c8a84b">
                                {markingWatched ? 'Moving…' : '✓ Watched'}
                            </button>
                        {/if}
                        <button
                            on:click={async () => {
                                editSaving = true;
                                await fetch(`/api/events/${expandedMovie.id}`, {
                                    method: "PATCH",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ metadata: { notes: editNotes, ...(!isWatchlist ? { rating: editRating } : {}) } }),
                                });
                                if (isWatchlist) {
                                    watchlist = await (await fetch("/api/events?source=movies&event_type=watchlist")).json();
                                } else {
                                    movies = await (await fetch("/api/events?source=movies&event_type=watch")).json();
                                }
                                editSaving = false;
                                expandedMovie = null;
                            }}
                            class="px-3 py-1.5 rounded-lg text-xs font-medium"
                            style="background:#252320; color:#9a9080">
                            {editSaving ? 'Saving…' : 'Save notes'}
                        </button>
                        <button
                            on:click={async () => {
                                await fetch(`/api/events/${expandedMovie.id}`, { method: "DELETE" });
                                if (isWatchlist) {
                                    watchlist = await (await fetch("/api/events?source=movies&event_type=watchlist")).json();
                                } else {
                                    movies = await (await fetch("/api/events?source=movies&event_type=watch")).json();
                                }
                                expandedMovie = null;
                            }}
                            class="text-xs" style="color:#c4948a">
                            Delete
                        </button>
                    </div>

                </div>
            </div>
        </div>
    {/if}

</main>

<style>
  .no-scroll { scrollbar-width: none; }
  .no-scroll::-webkit-scrollbar { display: none; }

  @media (max-width: 768px) {
    main {
      padding: 14px 14px 0 !important;
    }

    main > .grid {
      display: flex !important;
      flex-direction: column !important;
      gap: 10px !important;
    }

    main > .grid > div,
    main > .grid > .rounded-2xl {
      grid-column: unset !important;
      grid-row: unset !important;
      width: 100% !important;
      height: auto !important;
      min-height: 240px;
    }

    main > .grid > div[style*="grid-column:1/8"] {
      min-height: 380px;
    }

    main > .grid > .rounded-2xl {
      min-height: 320px;
    }

    main div[style*="grid-template-columns: 300px"],
    main div[style*="grid-template-columns: 1fr 300px"],
    main div[style*="grid-template-columns:repeat(6,1fr)"] {
      display: flex !important;
      flex-direction: column !important;
    }

    /* Header */
    main > div:first-child {
      flex-wrap: wrap;
      gap: 8px;
    }
  }
</style>
