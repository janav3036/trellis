<script>
  import { onMount } from "svelte";
  import { todayIST, fmtDate } from "../lib/ist.js";

  let dreams = [];
  let showForm = false;
  let expandedDream = null;

  const MOODS = ["neutral", "peaceful", "vivid", "eerie", "anxious", "nostalgic", "joyful"];

  const MOOD_COLORS = {
    neutral:    { bg: "#2a2a2a", text: "#9a9080" },
    peaceful:   { bg: "#1a2a3d", text: "#6b9ecc" },
    vivid:      { bg: "#2a1a3d", text: "#9b7ec8" },
    eerie:      { bg: "#1a2e2e", text: "#5abfbf" },
    anxious:    { bg: "#2e1a1a", text: "#c87a7a" },
    nostalgic:  { bg: "#3d2e1a", text: "#c89a5a" },
    joyful:     { bg: "#2a3d2a", text: "#8abf8a" },
  };

  function moodColor(mood) {
    return MOOD_COLORS[mood] || MOOD_COLORS.neutral;
  }

  function timeAgo(ts) {
    const secs = Math.floor((Date.now() - new Date(ts)) / 1000);
    if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
    if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
    const days = Math.floor(secs / 86400);
    if (days < 30) return `${days}d ago`;
    return fmtDate(ts, { month: "short", day: "numeric", year: "numeric" });
  }

  let form = {
    date: todayIST(),
    title: "",
    description: "",
    mood: "neutral",
    tags: "",
    lucid: false,
  };

  async function loadDreams() {
    const res = await fetch("/api/dreams");
    dreams = await res.json();
  }

  async function submitDream() {
    if (!form.title.trim()) return;
    await fetch("/api/dreams/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...form,
        tags: form.tags.split(",").map(t => t.trim()).filter(Boolean),
      }),
    });
    form = { date: todayIST(), title: "", description: "", mood: "neutral", tags: "", lucid: false };
    showForm = false;
    loadDreams();
  }

  async function deleteDream(id) {
    await fetch(`/api/events/${id}`, { method: "DELETE" });
    expandedDream = null;
    loadDreams();
  }

  let photos = [];
  let photosByDate = {};
  let photoYear = new Date().getFullYear();
  let selectedPhoto = null;
  let showPhotoForm = false;
  let photoForm = {
    date: todayIST(),
    url: "",
    caption: "",
  };

  $: photosByDate = Object.fromEntries(photos.map(p => [p.date, p]));
  $: photoCount = yearDays.filter(d => photosByDate[d]).length;

  $: yearDays = (() => {
    const days = [];
    const start = new Date(photoYear, 0, 1);
    const end = new Date(photoYear, 11, 31);
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      days.push(d.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' }));
    }
    return days;
  })();

  $: yearByMonth = (() => {
    const months = [];
    for (let m = 0; m < 12; m++) {
      months.push(yearDays.filter(d => parseInt(d.slice(5, 7)) - 1 === m));
    }
    return months;
  })();

  const MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

  async function loadPhotos() {
    const res = await fetch("/api/photos");
    photos = await res.json();
  }

  async function submitPhoto() {
    if (!photoForm.url.trim()) return;
    await fetch("/api/photos/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(photoForm),
    });
    photoForm = { date: todayIST(), url: "", caption: "" };
    showPhotoForm = false;
    loadPhotos();
  }

  let letters = [];
  let showLetterForm = false;
  let expandedLetter = null;
  let letterForm = {
    body: "",
    unlock_date: "",
  };

  async function loadLetters() {
    const res = await fetch("/api/letters");
    letters = await res.json();
  }

  async function submitLetter() {
    if (!letterForm.body.trim() || !letterForm.unlock_date) return;
    await fetch("/api/letters/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(letterForm),
    });
    letterForm = { body: "", unlock_date: "" };
    showLetterForm = false;
    loadLetters();
  }

  let quotes = [];
  let showQuoteForm = false;
  let quoteForm = { text: "", author: "", source_title: "", tags: "" };
  let selectedQuoteTag = "";

  $: filteredQuotes = selectedQuoteTag
    ? quotes.filter(q => q.tags?.includes(selectedQuoteTag))
    : quotes;

  $: allQuoteTags = [...new Set(quotes.flatMap(q => q.tags || []))];

  async function loadQuotes() {
    const res = await fetch("/api/quotes");
    quotes = await res.json();
  }

  async function submitQuote() {
    if (!quoteForm.text.trim()) return;
    await fetch("/api/quotes/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...quoteForm,
        tags: quoteForm.tags.split(",").map(t => t.trim()).filter(Boolean),
      }),
    });
    quoteForm = { text: "", author: "", source_title: "", tags: "" };
    showQuoteForm = false;
    loadQuotes();
  }

  let habits = [];
  let showHabitForm = false;
  let newHabitName = "";
  let newHabitColor = "#6b9e6b";

  const HABIT_COLORS = ["#6b9e6b", "#6b9ecc", "#9b7ec8", "#c89a5a", "#c87a7a", "#5abfbf"];

  async function loadHabits() {
    const res = await fetch("/api/habits");
    habits = await res.json();
  }

  async function createHabit() {
    if (!newHabitName.trim()) return;
    await fetch("/api/habits", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: newHabitName.trim(), color: newHabitColor }),
    });
    newHabitName = "";
    newHabitColor = "#6b9e6b";
    showHabitForm = false;
    loadHabits();
  }

  async function toggleCheckin(id) {
    await fetch(`/api/habits/${id}/checkin`, { method: "POST" });
    loadHabits();
  }

  async function deleteHabit(id) {
    await fetch(`/api/habits/${id}`, { method: "DELETE" });
    loadHabits();
  }

  onMount(() => { loadDreams(); loadPhotos(); loadLetters(); loadQuotes(); loadHabits(); });
</script>

<main class="p-8 bg-[#1a1714] min-h-screen text-[#e8e0d0]">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-3xl font-semibold">Journal</h1>
    <button
      on:click={() => (showForm = !showForm)}
      class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-2 rounded-lg text-sm"
    >
      {showForm ? "Cancel" : "+ Log dream"}
    </button>
  </div>

  <!-- Entry form -->
  {#if showForm}
    <div class="max-w-xl bg-[#242019] rounded-xl p-5 mb-8">
      <div class="flex flex-col gap-4">

        <div class="flex gap-4">
          <div class="flex flex-col gap-1">
            <label class="text-xs text-[#9a9080]">Date</label>
            <input
              type="date"
              bind:value={form.date}
              class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
            />
          </div>
          <div class="flex flex-col gap-1 flex-1">
            <label class="text-xs text-[#9a9080]">Title</label>
            <input
              type="text"
              bind:value={form.title}
              placeholder="The house with no doors…"
              class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
            />
          </div>
        </div>

        <div class="flex flex-col gap-1">
          <label class="text-xs text-[#9a9080]">Description</label>
          <textarea
            bind:value={form.description}
            placeholder="What happened…"
            rows="4"
            class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530] resize-none"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label class="text-xs text-[#9a9080]">Mood</label>
          <div class="flex flex-wrap gap-2">
            {#each MOODS as m}
              {@const mc = moodColor(m)}
              <button
                on:click={() => (form.mood = m)}
                class="px-3 py-1 rounded-full text-xs capitalize transition-opacity"
                style="background:{form.mood === m ? mc.bg : '#1a1714'}; color:{form.mood === m ? mc.text : '#9a9080'}; border: 1px solid {form.mood === m ? mc.text + '40' : '#3a3530'}"
              >
                {m}
              </button>
            {/each}
          </div>
        </div>

        <div class="flex gap-4 items-end">
          <div class="flex flex-col gap-1 flex-1">
            <label class="text-xs text-[#9a9080]">Tags <span class="text-[#5a5040]">(comma-separated)</span></label>
            <input
              type="text"
              bind:value={form.tags}
              placeholder="ocean, childhood, flying"
              class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
            />
          </div>
          <label class="flex items-center gap-2 text-sm text-[#9a9080] pb-2 cursor-pointer">
            <input type="checkbox" bind:checked={form.lucid} class="accent-[#9b7ec8]" />
            Lucid
          </label>
        </div>

        <button
          on:click={submitDream}
          class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-2 rounded-lg text-sm self-start"
        >
          Save
        </button>
      </div>
    </div>
  {/if}

  <!-- Dream list -->
  <section class="mb-16">
    <h2 class="text-xl font-semibold mb-4">Dream Journal</h2>
    {#if dreams.length === 0}
      <p class="text-sm text-[#9a9080]">No dreams logged yet.</p>
    {:else}
      <div class="flex flex-col gap-3 max-w-2xl">
        {#each dreams as d}
          {@const mc = moodColor(d.mood)}
          <button
            class="bg-[#242019] hover:bg-[#2a2520] rounded-xl px-5 py-4 text-left transition-colors"
            on:click={() => (expandedDream = d)}
          >
            <div class="flex items-start justify-between gap-4">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 flex-wrap mb-1">
                  <span class="text-sm font-medium">{d.title}</span>
                  {#if d.lucid}
                    <span class="text-xs px-2 py-0.5 rounded-full bg-[#2a1a3d] text-[#9b7ec8]">lucid</span>
                  {/if}
                  {#if d.mood}
                    <span
                      class="text-xs px-2 py-0.5 rounded-full capitalize"
                      style="background:{mc.bg}; color:{mc.text}"
                    >{d.mood}</span>
                  {/if}
                </div>
                {#if d.description}
                  <p class="text-xs text-[#9a9080] truncate">{d.description}</p>
                {/if}
                {#if d.tags?.length}
                  <div class="flex flex-wrap gap-1 mt-2">
                    {#each d.tags as tag}
                      <span class="text-xs px-2 py-0.5 rounded-full bg-[#1a1714] text-[#5a5040]">#{tag}</span>
                    {/each}
                  </div>
                {/if}
              </div>
              <span class="text-xs text-[#9a9080] shrink-0">{timeAgo(d.timestamp)}</span>
            </div>
          </button>
        {/each}
      </div>
    {/if}
  </section>

  <!-- Photo a Day -->
  <section class="mb-10">
    <div class="flex items-center gap-3 mb-4">
      <h2 class="text-xl font-semibold">Photo a Day</h2>
      <button on:click={() => photoYear--} class="bg-[#242019] hover:bg-[#2e2923] px-2 py-1 rounded-lg text-sm">←</button>
      <span class="text-sm text-[#9a9080]">{photoYear}</span>
      <button on:click={() => photoYear++} class="bg-[#242019] hover:bg-[#2e2923] px-2 py-1 rounded-lg text-sm">→</button>
      <button
        on:click={() => (showPhotoForm = !showPhotoForm)}
        class="ml-2 bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-3 py-1 rounded-lg text-sm"
      >{showPhotoForm ? "Cancel" : "+ Add photo"}</button>
    </div>

    {#if showPhotoForm}
      <div class="max-w-xl bg-[#242019] rounded-xl p-5 mb-6">
        <div class="flex flex-col gap-4">
          <div class="flex gap-4">
            <div class="flex flex-col gap-1">
              <label class="text-xs text-[#9a9080]">Date</label>
              <input
                type="date"
                bind:value={photoForm.date}
                class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
              />
            </div>
            <div class="flex flex-col gap-1 flex-1">
              <label class="text-xs text-[#9a9080]">Image</label>
              <input
                type="file"
                accept="image/*"
                on:change={async (e) => {
                  const file = e.target.files[0];
                  if (!file) return;
                  const fd = new FormData();
                  fd.append("file", file);
                  const res = await fetch("/api/photos/upload", { method: "POST", body: fd });
                  const data = await res.json();
                  photoForm.url = data.url;
                }}
                class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
              />
              {#if photoForm.url}
                <img src={photoForm.url} alt="preview" class="w-32 h-24 object-cover rounded-lg mt-1" />
              {/if}
            </div>
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-[#9a9080]">Caption <span class="text-[#5a5040]">(optional)</span></label>
            <input
              type="text"
              bind:value={photoForm.caption}
              placeholder="A quiet morning…"
              class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
            />
          </div>
          <button
            on:click={submitPhoto}
            class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-2 rounded-lg text-sm self-start"
          >Save</button>
        </div>
      </div>
    {/if}

    <div class="grid grid-cols-6 gap-4">
      {#each yearByMonth as monthDays, mi}
        <div>
          <div class="text-xs text-[#9a9080] mb-1.5">{MONTH_NAMES[mi]}</div>
          <div class="grid grid-cols-7 gap-0.5">
            {#each monthDays as day}
              {@const photo = photosByDate[day]}
              {@const isFuture = day > todayIST()}
              <button
                title={photo ? (photo.caption || day) : day}
                on:click={() => { if (photo) selectedPhoto = photo; }}
                class="w-3.5 h-3.5 rounded-sm overflow-hidden {isFuture ? 'opacity-20' : photo ? 'opacity-100' : 'bg-[#2a2520] opacity-60'}"
                style={photo ? `background-image:url(${photo.url});background-size:cover;background-position:center` : ''}
              />
            {/each}
          </div>
        </div>
      {/each}
    </div>

    {#if photoCount > 0}
      <p class="text-xs text-[#9a9080] mt-3">{photoCount} / {yearDays.length} days captured</p>
    {/if}
  </section>

  <!-- Habit tracker -->
  <section class="mb-10">
    <div class="flex items-center gap-4 mb-4">
      <h2 class="text-xl font-semibold">Habits</h2>
      <button
        on:click={() => (showHabitForm = !showHabitForm)}
        class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-3 py-1 rounded-lg text-sm"
      >{showHabitForm ? "Cancel" : "+ Add habit"}</button>
    </div>

    {#if showHabitForm}
      <div class="max-w-xl bg-[#242019] rounded-xl p-5 mb-6">
        <div class="flex gap-4 items-end">
          <div class="flex flex-col gap-1 flex-1">
            <label class="text-xs text-[#9a9080]">Habit name</label>
            <input
              type="text"
              bind:value={newHabitName}
              placeholder="Read, Meditate, Exercise…"
              class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-[#9a9080]">Color</label>
            <div class="flex gap-1.5">
              {#each HABIT_COLORS as c}
                <button
                  on:click={() => (newHabitColor = c)}
                  title={c}
                  class="w-6 h-6 rounded-full border-2 transition-all"
                  style="background:{c}; border-color:{newHabitColor === c ? '#e8e0d0' : 'transparent'}"
                ></button>
              {/each}
            </div>
          </div>
          <button
            on:click={createHabit}
            class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-2 rounded-lg text-sm"
          >Add</button>
        </div>
      </div>
    {/if}

    {#if habits.length === 0}
      <p class="text-sm text-[#9a9080]">No habits yet.</p>
    {:else}
      <div class="flex flex-col gap-2 max-w-2xl">
        {#each habits as h}
          <div class="bg-[#242019] rounded-xl px-5 py-3 flex items-center gap-4 group">
            <button
              on:click={() => toggleCheckin(h.id)}
              class="w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-all"
              style="border-color:{h.color}; background:{h.done_today ? h.color : 'transparent'}"
            >
              {#if h.done_today}
                <span class="text-[#1a1714] text-xs font-bold">✓</span>
              {/if}
            </button>
            <span class="text-sm flex-1" style="color:{h.done_today ? h.color : '#e8e0d0'}">{h.name}</span>
            <button
              on:click={() => deleteHabit(h.id)}
              class="text-xs text-[#c87a7a] hover:text-[#e87a7a] opacity-0 group-hover:opacity-100 transition-opacity"
            >✕</button>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  <!-- Quote collector -->
  <section class="mb-10">
    <div class="flex items-center gap-4 mb-4">
      <h2 class="text-xl font-semibold">Quotes</h2>
      <button
        on:click={() => (showQuoteForm = !showQuoteForm)}
        class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-3 py-1 rounded-lg text-sm"
      >{showQuoteForm ? "Cancel" : "+ Add quote"}</button>
    </div>

    {#if showQuoteForm}
      <div class="max-w-xl bg-[#242019] rounded-xl p-5 mb-6">
        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-1">
            <label class="text-xs text-[#9a9080]">Quote</label>
            <textarea
              bind:value={quoteForm.text}
              placeholder="The quote…"
              rows="3"
              class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530] resize-none"
            />
          </div>
          <div class="flex gap-4">
            <div class="flex flex-col gap-1 flex-1">
              <label class="text-xs text-[#9a9080]">Author</label>
              <input type="text" bind:value={quoteForm.author} placeholder="Name…"
                class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]" />
            </div>
            <div class="flex flex-col gap-1 flex-1">
              <label class="text-xs text-[#9a9080]">Source <span class="text-[#5a5040]">(book, article…)</span></label>
              <input type="text" bind:value={quoteForm.source_title} placeholder="Title…"
                class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]" />
            </div>
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-[#9a9080]">Tags <span class="text-[#5a5040]">(comma-separated)</span></label>
            <input type="text" bind:value={quoteForm.tags} placeholder="philosophy, life, work"
              class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530]" />
          </div>
          <button on:click={submitQuote}
            class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-2 rounded-lg text-sm self-start">
            Save
          </button>
        </div>
      </div>
    {/if}

    {#if allQuoteTags.length > 0}
      <div class="flex flex-wrap gap-2 mb-4">
        <button
          on:click={() => (selectedQuoteTag = "")}
          class="px-3 py-1 rounded-full text-xs {selectedQuoteTag === '' ? 'bg-[#3a3530] text-[#e8e0d0]' : 'text-[#9a9080] hover:text-[#e8e0d0]'}"
        >All</button>
        {#each allQuoteTags as tag}
          <button
            on:click={() => (selectedQuoteTag = selectedQuoteTag === tag ? null : tag)}
            class="px-3 py-1 rounded-full text-xs {selectedQuoteTag === tag ? 'bg-[#3a3530] text-[#e8e0d0]' : 'text-[#9a9080] hover:text-[#e8e0d0]'}"
          >#{tag}</button>
        {/each}
      </div>
    {/if}

    {#if filteredQuotes.length === 0}
      <p class="text-sm text-[#9a9080]">No quotes yet.</p>
    {:else}
      <div class="flex flex-col gap-3 max-w-2xl">
        {#each filteredQuotes as q}
          <div class="bg-[#242019] rounded-xl px-5 py-4 group relative">
            <p class="text-sm text-[#c8c0b0] leading-relaxed italic mb-2">"{q.text}"</p>
            <div class="flex items-center justify-between gap-4">
              <div class="text-xs text-[#9a9080]">
                {#if q.author}— {q.author}{/if}{#if q.source_title}, <span class="italic">{q.source_title}</span>{/if}
              </div>
              <div class="flex items-center gap-3">
                {#each q.tags || [] as tag}
                  <span class="text-xs text-[#5a5040]">#{tag}</span>
                {/each}
                <button
                  on:click={async () => {
                    await fetch(`/api/events/${q.id}`, { method: "DELETE" });
                    loadQuotes();
                  }}
                  class="text-xs text-[#c87a7a] hover:text-[#e87a7a] opacity-0 group-hover:opacity-100 transition-opacity"
                >✕</button>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  <!-- Letters to future self -->
  <section class="mb-10">
    <div class="flex items-center gap-4 mb-4">
      <h2 class="text-xl font-semibold">Letters to Future Self</h2>
      <button
        on:click={() => (showLetterForm = !showLetterForm)}
        class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-3 py-1 rounded-lg text-sm"
      >{showLetterForm ? "Cancel" : "+ Write letter"}</button>
    </div>

    {#if showLetterForm}
      <div class="max-w-xl bg-[#242019] rounded-xl p-5 mb-6">
        <div class="flex flex-col gap-4">
          <div class="flex flex-col gap-1">
            <label class="text-xs text-[#9a9080]">Unlock date <span class="text-[#5a5040]">(when you'll receive the email)</span></label>
            <input
              type="date"
              bind:value={letterForm.unlock_date}
              class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530] w-48"
            />
          </div>
          <div class="flex flex-col gap-1">
            <label class="text-xs text-[#9a9080]">Your letter</label>
            <textarea
              bind:value={letterForm.body}
              placeholder="Dear future me…"
              rows="8"
              class="bg-[#1a1714] text-[#e8e0d0] rounded-lg px-3 py-2 text-sm border border-[#3a3530] resize-none"
            />
          </div>
          <button
            on:click={submitLetter}
            class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-2 rounded-lg text-sm self-start"
          >Seal & save</button>
        </div>
      </div>
    {/if}

    {#if letters.length === 0}
      <p class="text-sm text-[#9a9080]">No letters yet.</p>
    {:else}
      <div class="flex flex-col gap-3 max-w-2xl">
        {#each letters as letter}
          <button
            class="bg-[#242019] hover:bg-[#2a2520] rounded-xl px-5 py-4 text-left transition-colors {letter.unlocked ? '' : 'cursor-default'}"
            on:click={() => { if (letter.unlocked) expandedLetter = letter; }}
          >
            <div class="flex items-center justify-between gap-4">
              <div class="flex items-center gap-3">
                {#if letter.unlocked}
                  <span class="text-lg">✉️</span>
                  <div>
                    <div class="text-sm font-medium">Letter unlocked</div>
                    <div class="text-xs text-[#9a9080]">Written {timeAgo(letter.timestamp)}</div>
                  </div>
                {:else}
                  <span class="text-lg opacity-40">🔒</span>
                  <div>
                    <div class="text-sm font-medium text-[#9a9080]">Sealed</div>
                    <div class="text-xs text-[#9a9080]">Opens {new Date(letter.unlock_date + "T12:00:00").toLocaleDateString("en-US", { timeZone: "Asia/Kolkata", month: "long", day: "numeric", year: "numeric" })}</div>
                  </div>
                {/if}
              </div>
              {#if letter.unlocked}
                <span class="text-xs text-[#6b9e6b] shrink-0">Read →</span>
              {/if}
            </div>
          </button>
        {/each}
      </div>
    {/if}
  </section>
</main>

<!-- Detail modal -->
{#if expandedDream}
  {@const mc = moodColor(expandedDream.mood)}
  <div
    class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-8"
    on:click={() => (expandedDream = null)}
  >
    <div
      class="bg-[#242019] rounded-2xl p-8 max-w-xl w-full shadow-2xl"
      on:click|stopPropagation
    >
      <div class="flex items-start justify-between gap-4 mb-4">
        <div>
          <div class="text-xl font-semibold mb-1">{expandedDream.title}</div>
          <div class="text-xs text-[#9a9080]">
            {new Date(expandedDream.timestamp).toLocaleDateString("en-US", { timeZone: "Asia/Kolkata", weekday: "long", month: "long", day: "numeric", year: "numeric" })}
          </div>
        </div>
        <button on:click={() => (expandedDream = null)} class="text-[#9a9080] hover:text-[#e8e0d0]">✕</button>
      </div>

      <div class="flex flex-wrap gap-2 mb-4">
        {#if expandedDream.lucid}
          <span class="text-xs px-2 py-0.5 rounded-full bg-[#2a1a3d] text-[#9b7ec8]">lucid</span>
        {/if}
        {#if expandedDream.mood}
          <span
            class="text-xs px-2 py-0.5 rounded-full capitalize"
            style="background:{mc.bg}; color:{mc.text}"
          >{expandedDream.mood}</span>
        {/if}
        {#each expandedDream.tags || [] as tag}
          <span class="text-xs px-2 py-0.5 rounded-full bg-[#1a1714] text-[#5a5040]">#{tag}</span>
        {/each}
      </div>

      {#if expandedDream.description}
        <p class="text-sm text-[#c8c0b0] leading-relaxed whitespace-pre-wrap mb-6">{expandedDream.description}</p>
      {/if}

      <button
        on:click={() => deleteDream(expandedDream.id)}
        class="text-xs text-[#c87a7a] hover:text-[#e87a7a]"
      >Delete</button>
    </div>
  </div>
{/if}

{#if selectedPhoto}
  <div
    class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8"
    on:click={() => (selectedPhoto = null)}
  >
    <div
      class="bg-[#242019] rounded-2xl overflow-hidden max-w-lg w-full shadow-2xl"
      on:click|stopPropagation
    >
      <img src={selectedPhoto.url} alt={selectedPhoto.caption || selectedPhoto.date} class="w-full max-h-96 object-cover" />
      <div class="px-6 py-4 flex items-start justify-between gap-4">
        <div>
          <div class="text-sm text-[#9a9080]">
            {new Date(selectedPhoto.date + "T12:00:00").toLocaleDateString("en-US", { timeZone: "Asia/Kolkata", weekday: "long", month: "long", day: "numeric", year: "numeric" })}
          </div>
          {#if selectedPhoto.caption}
            <p class="text-sm text-[#c8c0b0] mt-1">{selectedPhoto.caption}</p>
          {/if}
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <button
            on:click={async () => {
              await fetch(`/api/events/${selectedPhoto.id}`, { method: "DELETE" });
              selectedPhoto = null;
              loadPhotos();
            }}
            class="text-xs text-[#c87a7a] hover:text-[#e87a7a]"
          >Delete</button>
          <button on:click={() => (selectedPhoto = null)} class="text-[#9a9080] hover:text-[#e8e0d0]">✕</button>
        </div>
      </div>
    </div>
  </div>
{/if}

{#if expandedLetter}
  <div
    class="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-8"
    on:click={() => (expandedLetter = null)}
  >
    <div
      class="bg-[#242019] rounded-2xl p-8 max-w-xl w-full shadow-2xl"
      on:click|stopPropagation
    >
      <div class="flex items-start justify-between gap-4 mb-2">
        <div class="text-xs text-[#9a9080]">
          Written {new Date(expandedLetter.timestamp).toLocaleDateString("en-US", { timeZone: "Asia/Kolkata", month: "long", day: "numeric", year: "numeric" })}
          · unlocked {new Date(expandedLetter.unlock_date + "T12:00:00").toLocaleDateString("en-US", { timeZone: "Asia/Kolkata", month: "long", day: "numeric", year: "numeric" })}
        </div>
        <button on:click={() => (expandedLetter = null)} class="text-[#9a9080] hover:text-[#e8e0d0] shrink-0">✕</button>
      </div>
      <p class="text-sm text-[#c8c0b0] leading-relaxed whitespace-pre-wrap mt-4 mb-6">{expandedLetter.body}</p>
      <button
        on:click={async () => {
          await fetch(`/api/events/${expandedLetter.id}`, { method: "DELETE" });
          expandedLetter = null;
          loadLetters();
        }}
        class="text-xs text-[#c87a7a] hover:text-[#e87a7a]"
      >Delete</button>
    </div>
  </div>
{/if}
