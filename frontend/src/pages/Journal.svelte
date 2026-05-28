<script>
  import { onMount } from "svelte";
  import { todayIST, fmtDate } from "../lib/ist.js";

  let dreams = [];
  let showForm = false;
  let expandedDream = null;

  const MOODS = ["neutral", "peaceful", "vivid", "eerie", "anxious", "nostalgic", "joyful"];

  const MOOD_COLORS = {
    neutral:   { bg: "#2a2a2a", text: "#9a9080", stripe: "#4a4848" },
    peaceful:  { bg: "#1a2a3d", text: "#6b9ecc", stripe: "#4a7ea8" },
    vivid:     { bg: "#2a1a3d", text: "#9b7ec8", stripe: "#7a5ea8" },
    eerie:     { bg: "#1a2e2e", text: "#5abfbf", stripe: "#3a9898" },
    anxious:   { bg: "#2e1a1a", text: "#c87a7a", stripe: "#a85858" },
    nostalgic: { bg: "#3d2e1a", text: "#c89a5a", stripe: "#a87840" },
    joyful:    { bg: "#2a3d2a", text: "#8abf8a", stripe: "#5a9e5a" },
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

  // Photos
  let photos = [];
  let photosByDate = {};
  let photoYear = new Date().getFullYear();
  let selectedPhoto = null;
  let showPhotoForm = false;
  let photoForm = { date: todayIST(), url: "", caption: "" };

  $: photosByDate = Object.fromEntries(photos.map(p => [p.date, p]));
  $: photoCount = yearDays.filter(d => photosByDate[d]).length;

  $: yearDays = (() => {
    const days = [];
    const start = new Date(photoYear, 0, 1);
    const end   = new Date(photoYear, 11, 31);
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
  const TODAY = todayIST();

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

  // Letters
  let letters = [];
  let showLetterForm = false;
  let expandedLetter = null;
  let letterForm = { body: "", unlock_date: "" };

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

  // Quotes
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

  // Habits
  let habits = [];
  let showHabitForm = false;
  let newHabitName = "";
  let newHabitColor = "#6b9e6b";

  const HABIT_COLORS = ["#6b9e6b","#6b9ecc","#9b7ec8","#c89a5a","#c87a7a","#5abfbf"];

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

  // Memories
  let memories = [];

  async function loadMemories() {
    const res = await fetch("/api/memories");
    memories = await res.json();
  }

  onMount(() => {
    loadDreams();
    loadPhotos();
    loadLetters();
    loadQuotes();
    loadHabits();
    loadMemories();
  });
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="" />
  <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,500;0,600;1,400;1,500&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap" rel="stylesheet" />
</svelte:head>

<main class="j-root">

  <div class="j-bento">

    <!-- ── Dreams ── cols 1-7, row 1 -->
    <div class="j-cell dreams-cell" style="grid-column:1/8;grid-row:1;animation-delay:0.04s">
      <div class="cell-head">
        <span class="eyebrow">Dream Journal</span>
        <button class="add-btn" class:cancel={showForm} on:click={() => showForm = !showForm}>
          {showForm ? "Cancel" : "+ Log dream"}
        </button>
      </div>

      <div class="scroll-area">
        {#if showForm}
          <div class="form-card" style="animation:fade-in 0.2s ease both">
            <div class="form-row">
              <div class="form-group" style="flex:0 0 auto">
                <label class="form-label">Date</label>
                <input type="date" bind:value={form.date} class="j-input" />
              </div>
              <div class="form-group" style="flex:1">
                <label class="form-label">Title</label>
                <input type="text" bind:value={form.title} placeholder="The house with no doors…" class="j-input" />
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Description</label>
              <textarea bind:value={form.description} placeholder="What happened…" rows="3" class="j-input j-textarea" />
            </div>
            <div class="mood-row">
              {#each MOODS as m}
                {@const mc = moodColor(m)}
                <button on:click={() => form.mood = m}
                  class="mood-chip"
                  style="background:{form.mood === m ? mc.bg : 'transparent'};
                         color:{form.mood === m ? mc.text : '#6a6058'};
                         border-color:{form.mood === m ? mc.stripe + '60' : '#2a2823'}"
                >{m}</button>
              {/each}
            </div>
            <div class="form-row" style="align-items:center">
              <input type="text" bind:value={form.tags} placeholder="ocean, childhood, flying"
                class="j-input" style="flex:1" />
              <label class="lucid-label">
                <input type="checkbox" bind:checked={form.lucid} class="lucid-check" />
                <span>Lucid</span>
              </label>
              <button on:click={submitDream} class="save-btn">Save</button>
            </div>
          </div>
        {/if}

        {#if dreams.length === 0 && !showForm}
          <p class="empty-text">No dreams logged yet.</p>
        {:else}
          <div class="dream-list">
            {#each dreams as d}
              {@const mc = moodColor(d.mood)}
              <button class="dream-card" on:click={() => expandedDream = d}>
                <div class="dream-stripe" style="background:{mc.stripe}"></div>
                <div class="dream-body">
                  <div class="dream-header">
                    <span class="dream-title">{d.title}</span>
                    <div class="dream-badges">
                      {#if d.lucid}
                        <span class="badge lucid-badge">lucid</span>
                      {/if}
                      {#if d.mood && d.mood !== 'neutral'}
                        <span class="badge mood-badge" style="background:{mc.bg};color:{mc.text}">{d.mood}</span>
                      {/if}
                    </div>
                    <span class="dream-time">{timeAgo(d.timestamp)}</span>
                  </div>
                  {#if d.description}
                    <p class="dream-desc">{d.description}</p>
                  {/if}
                  {#if d.tags?.length}
                    <div class="dream-tags">
                      {#each d.tags as tag}<span class="tag">#{tag}</span>{/each}
                    </div>
                  {/if}
                </div>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- ── Photo a Day ── cols 8-12, row 1 -->
    <div class="j-cell photos-cell" style="grid-column:8/13;grid-row:1;animation-delay:0.08s">
      <div class="cell-head">
        <div class="photo-nav">
          <span class="eyebrow">Photo a Day</span>
          <button on:click={() => photoYear--} class="yr-btn">‹</button>
          <span class="yr-label">{photoYear}</span>
          <button on:click={() => photoYear++} class="yr-btn">›</button>
        </div>
        <button class="add-btn" class:cancel={showPhotoForm} on:click={() => showPhotoForm = !showPhotoForm}>
          {showPhotoForm ? "Cancel" : "+ Add"}
        </button>
      </div>

      <div class="scroll-area">
        {#if showPhotoForm}
          <div class="form-card" style="animation:fade-in 0.2s ease both">
            <div class="form-row">
              <div class="form-group" style="flex:0 0 auto">
                <label class="form-label">Date</label>
                <input type="date" bind:value={photoForm.date} class="j-input" />
              </div>
              <div class="form-group" style="flex:1">
                <label class="form-label">Image</label>
                <input type="file" accept="image/*"
                  on:change={async (e) => {
                    const file = e.target.files[0];
                    if (!file) return;
                    const fd = new FormData();
                    fd.append("file", file);
                    const res = await fetch("/api/photos/upload", { method: "POST", body: fd });
                    const data = await res.json();
                    photoForm.url = data.url;
                  }}
                  class="j-input" />
              </div>
            </div>
            {#if photoForm.url}
              <img src={photoForm.url} alt="preview" class="photo-preview" />
            {/if}
            <div class="form-row" style="align-items:center">
              <input type="text" bind:value={photoForm.caption} placeholder="A quiet morning…"
                class="j-input" style="flex:1" />
              <button on:click={submitPhoto} class="save-btn">Save</button>
            </div>
          </div>
        {/if}

        <div class="photo-grid">
          {#each yearByMonth as monthDays, mi}
            <div class="month-col">
              <div class="month-label">{MONTH_NAMES[mi]}</div>
              <div class="dot-grid">
                {#each monthDays as day}
                  {@const photo = photosByDate[day]}
                  {@const isFuture = day > TODAY}
                  <button
                    title={photo ? (photo.caption || day) : day}
                    on:click={() => { if (photo) selectedPhoto = photo; }}
                    class="day-dot"
                    class:dot-future={isFuture}
                    class:dot-empty={!photo && !isFuture}
                    class:dot-filled={!!photo}
                    style={photo ? `background-image:url(${photo.url});background-size:cover;background-position:center` : ''}
                  />
                {/each}
              </div>
            </div>
          {/each}
        </div>

        {#if photoCount > 0}
          <p class="photo-count">{photoCount} / {yearDays.length} days captured</p>
        {/if}
      </div>
    </div>

    <!-- ── Habits ── cols 1-3, row 2 -->
    <div class="j-cell habits-cell" style="grid-column:1/4;grid-row:2;animation-delay:0.12s">
      <div class="cell-head">
        <span class="eyebrow">Habits · Today</span>
        <button class="add-btn" class:cancel={showHabitForm} on:click={() => showHabitForm = !showHabitForm}>
          {showHabitForm ? "Cancel" : "+ Add"}
        </button>
      </div>

      <div class="scroll-area">
        {#if showHabitForm}
          <div class="form-card" style="animation:fade-in 0.2s ease both;margin-bottom:10px">
            <input type="text" bind:value={newHabitName} placeholder="Read, Meditate…" class="j-input" />
            <div class="color-row">
              {#each HABIT_COLORS as c}
                <button on:click={() => newHabitColor = c}
                  class="color-dot"
                  style="background:{c};outline:{newHabitColor === c ? `2px solid ${c}` : 'none'};outline-offset:2px"
                />
              {/each}
              <button on:click={createHabit} class="save-btn" style="margin-left:auto">Add</button>
            </div>
          </div>
        {/if}

        {#if habits.length === 0}
          <p class="empty-text">No habits yet.</p>
        {:else}
          <div class="habit-list">
            {#each habits as h}
              <div class="habit-row group">
                <button on:click={() => toggleCheckin(h.id)} class="habit-check"
                  style="border-color:{h.color};background:{h.done_today ? h.color : 'transparent'}">
                  {#if h.done_today}
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                      <path d="M2 5l2.5 2.5L8 3" stroke="#1a1714" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  {/if}
                </button>
                <span class="habit-name" style="color:{h.done_today ? h.color : '#c8c0b0'}">{h.name}</span>
                {#if h.streak > 1}
                  <span class="habit-streak" style="color:{h.color}">{h.streak}d</span>
                {/if}
                <button on:click={() => deleteHabit(h.id)} class="del-btn">✕</button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- ── Quotes ── cols 4-9, row 2 -->
    <div class="j-cell quotes-cell" style="grid-column:4/10;grid-row:2;animation-delay:0.16s">
      <div class="cell-head">
        <span class="eyebrow">Quotes</span>
        <div class="tag-pills">
          {#if allQuoteTags.length > 0}
            <button on:click={() => selectedQuoteTag = ""}
              class="tag-pill" class:tag-active={selectedQuoteTag === ""}>All</button>
            {#each allQuoteTags as tag}
              <button on:click={() => selectedQuoteTag = selectedQuoteTag === tag ? "" : tag}
                class="tag-pill" class:tag-active={selectedQuoteTag === tag}>#{tag}</button>
            {/each}
          {/if}
        </div>
        <button class="add-btn" class:cancel={showQuoteForm} on:click={() => showQuoteForm = !showQuoteForm}>
          {showQuoteForm ? "Cancel" : "+ Add"}
        </button>
      </div>

      <div class="scroll-area">
        {#if showQuoteForm}
          <div class="form-card" style="animation:fade-in 0.2s ease both">
            <div class="form-group">
              <textarea bind:value={quoteForm.text} placeholder="The quote…" rows="2"
                class="j-input j-textarea" style="font-family:'Lora',serif;font-style:italic" />
            </div>
            <div class="form-row">
              <input type="text" bind:value={quoteForm.author} placeholder="Author"
                class="j-input" style="flex:1" />
              <input type="text" bind:value={quoteForm.source_title} placeholder="Source"
                class="j-input" style="flex:1" />
            </div>
            <div class="form-row" style="align-items:center">
              <input type="text" bind:value={quoteForm.tags} placeholder="philosophy, life"
                class="j-input" style="flex:1" />
              <button on:click={submitQuote} class="save-btn">Save</button>
            </div>
          </div>
        {/if}

        {#if filteredQuotes.length === 0}
          <p class="empty-text">No quotes yet.</p>
        {:else}
          <div class="quote-list">
            {#each filteredQuotes as q}
              <div class="quote-card group">
                <div class="quote-mark">"</div>
                <div class="quote-content">
                  <p class="quote-text">{q.text}"</p>
                  {#if q.author || q.source_title}
                    <div class="quote-attr">
                      {#if q.author}— {q.author}{/if}
                      {#if q.source_title}<span class="quote-source">, {q.source_title}</span>{/if}
                    </div>
                  {/if}
                  {#if q.tags?.length}
                    <div class="quote-tags">
                      {#each q.tags as tag}<span class="tag">#{tag}</span>{/each}
                    </div>
                  {/if}
                </div>
                <button on:click={async () => { await fetch(`/api/events/${q.id}`, { method: "DELETE" }); loadQuotes(); }}
                  class="del-btn quote-del">✕</button>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- ── Letters ── cols 10-12, row 2 -->
    <div class="j-cell letters-cell" style="grid-column:10/13;grid-row:2;animation-delay:0.2s">
      <div class="cell-head">
        <span class="eyebrow">Letters to Future Self</span>
        <button class="add-btn" class:cancel={showLetterForm} on:click={() => showLetterForm = !showLetterForm}>
          {showLetterForm ? "Cancel" : "+ Write"}
        </button>
      </div>

      <div class="scroll-area">
        {#if showLetterForm}
          <div class="form-card" style="animation:fade-in 0.2s ease both">
            <div class="form-group">
              <label class="form-label">Unlock date</label>
              <input type="date" bind:value={letterForm.unlock_date} class="j-input" />
            </div>
            <div class="form-group">
              <textarea bind:value={letterForm.body} placeholder="Dear future me…" rows="5"
                class="j-input j-textarea" style="font-family:'Lora',serif" />
            </div>
            <button on:click={submitLetter} class="save-btn" style="align-self:flex-end">Seal &amp; save</button>
          </div>
        {/if}

        {#if letters.length === 0}
          <p class="empty-text">No letters yet.</p>
        {:else}
          <div class="letter-list">
            {#each letters as letter}
              <button class="letter-card"
                class:letter-open={letter.unlocked}
                class:letter-sealed={!letter.unlocked}
                on:click={() => { if (letter.unlocked) expandedLetter = letter; }}
                disabled={!letter.unlocked}
              >
                {#if letter.unlocked}
                  <div class="letter-icon open-icon">✉</div>
                  <div class="letter-meta">
                    <div class="letter-status open">Unlocked</div>
                    <div class="letter-date">{timeAgo(letter.timestamp)}</div>
                  </div>
                  <span class="letter-read">Read →</span>
                {:else}
                  <div class="letter-icon seal-icon">⊕</div>
                  <div class="letter-meta">
                    <div class="letter-status sealed">Sealed</div>
                    <div class="letter-date">
                      Opens {new Date(letter.unlock_date + "T12:00:00").toLocaleDateString("en-US", {
                        timeZone: "Asia/Kolkata", month: "short", day: "numeric", year: "numeric"
                      })}
                    </div>
                  </div>
                {/if}
              </button>
            {/each}
          </div>
        {/if}
      </div>
    </div>

    <!-- ── Memories ── row 3, all 12 cols -->
    {#if memories.length > 0}
      <div class="j-cell memories-cell" style="grid-column:1/13;grid-row:3;animation-delay:0.24s">
        <div class="cell-head" style="margin-bottom:12px">
          <span class="eyebrow">Memories</span>
          <span class="mem-subtitle">what you were doing on this day</span>
        </div>
        <div class="mem-strip">
          {#each memories as window}
            <div class="mem-window">
              <div class="mem-window-head">
                <span class="mem-label">{window.label}</span>
                <span class="mem-date">{new Date(window.date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
              </div>
              <div class="mem-entries">
                {#each window.entries as entry}
                  {#if entry.source === 'photos'}
                    <button class="mem-entry mem-photo"
                      on:click={() => selectedPhoto = { ...entry, date: entry.timestamp?.slice(0,10) }}>
                      <img src={entry.url} alt={entry.caption || ''} class="mem-photo-thumb" />
                      {#if entry.caption}
                        <span class="mem-photo-cap">{entry.caption}</span>
                      {/if}
                    </button>
                  {:else if entry.source === 'dreams'}
                    <button class="mem-entry mem-dream"
                      on:click={() => expandedDream = entry}>
                      <span class="mem-dream-dot" style="background:{moodColor(entry.mood).stripe}"></span>
                      <div class="mem-dream-info">
                        <span class="mem-dream-title">{entry.title}</span>
                        {#if entry.mood && entry.mood !== 'neutral'}
                          <span class="mem-dream-mood" style="color:{moodColor(entry.mood).text}">{entry.mood}</span>
                        {/if}
                      </div>
                    </button>
                  {/if}
                {/each}
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}

  </div>
</main>

<!-- ── Modals ── -->

{#if expandedDream}
  {@const mc = moodColor(expandedDream.mood)}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="modal-bg" on:click={() => expandedDream = null}>
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="modal" on:click|stopPropagation>
      <div class="modal-stripe" style="background:{mc.stripe}"></div>
      <div class="modal-inner">
        <div class="modal-head">
          <div>
            <div class="modal-title">{expandedDream.title}</div>
            <div class="modal-sub">
              {new Date(expandedDream.timestamp).toLocaleDateString("en-US", {
                timeZone: "Asia/Kolkata", weekday: "long", month: "long", day: "numeric", year: "numeric"
              })}
            </div>
          </div>
          <button on:click={() => expandedDream = null} class="modal-x">✕</button>
        </div>
        <div class="modal-badges">
          {#if expandedDream.lucid}
            <span class="badge lucid-badge">lucid</span>
          {/if}
          {#if expandedDream.mood}
            <span class="badge mood-badge" style="background:{mc.bg};color:{mc.text}">{expandedDream.mood}</span>
          {/if}
          {#each expandedDream.tags || [] as tag}
            <span class="badge tag-badge">#{tag}</span>
          {/each}
        </div>
        {#if expandedDream.description}
          <p class="modal-body-text">{expandedDream.description}</p>
        {/if}
        <button on:click={() => deleteDream(expandedDream.id)} class="del-text">Delete</button>
      </div>
    </div>
  </div>
{/if}

{#if selectedPhoto}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="modal-bg" on:click={() => selectedPhoto = null}>
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="modal photo-modal" on:click|stopPropagation>
      <img src={selectedPhoto.url} alt={selectedPhoto.caption || selectedPhoto.date}
           class="photo-modal-img" />
      <div class="photo-modal-info">
        <div>
          <div class="modal-sub">
            {new Date(selectedPhoto.date + "T12:00:00").toLocaleDateString("en-US", {
              timeZone: "Asia/Kolkata", weekday: "long", month: "long", day: "numeric", year: "numeric"
            })}
          </div>
          {#if selectedPhoto.caption}
            <p class="photo-caption">{selectedPhoto.caption}</p>
          {/if}
        </div>
        <div class="modal-actions">
          <button on:click={async () => {
            await fetch(`/api/events/${selectedPhoto.id}`, { method: "DELETE" });
            selectedPhoto = null;
            loadPhotos();
          }} class="del-text">Delete</button>
          <button on:click={() => selectedPhoto = null} class="modal-x">✕</button>
        </div>
      </div>
    </div>
  </div>
{/if}

{#if expandedLetter}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="modal-bg" on:click={() => expandedLetter = null}>
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="modal" on:click|stopPropagation>
      <div class="modal-stripe" style="background:#c89a5a;opacity:0.5"></div>
      <div class="modal-inner">
        <div class="modal-head">
          <div class="modal-sub">
            Written {new Date(expandedLetter.timestamp).toLocaleDateString("en-US", {
              timeZone: "Asia/Kolkata", month: "long", day: "numeric", year: "numeric"
            })}
            · unlocked {new Date(expandedLetter.unlock_date + "T12:00:00").toLocaleDateString("en-US", {
              timeZone: "Asia/Kolkata", month: "long", day: "numeric", year: "numeric"
            })}
          </div>
          <button on:click={() => expandedLetter = null} class="modal-x">✕</button>
        </div>
        <p class="letter-body">{expandedLetter.body}</p>
        <button on:click={async () => {
          await fetch(`/api/events/${expandedLetter.id}`, { method: "DELETE" });
          expandedLetter = null;
          loadLetters();
        }} class="del-text">Delete</button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* ── Root ── */
  .j-root {
    background: #181512;
    color: #e8e0d0;
    padding: 18px;
    min-height: 100vh;
    box-sizing: border-box;
    font-family: 'DM Sans', system-ui, sans-serif;
  }

  /* ── Bento ── */
  .j-bento {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    grid-template-rows: 52vh 36vh auto;
    gap: 10px;
  }

  .j-cell {
    background: #1c1b17;
    border-radius: 14px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-sizing: border-box;
    border: 1px solid rgba(255,255,255,0.04);
    animation: cell-in 0.4s cubic-bezier(0.22,1,0.36,1) both;
  }

  @keyframes cell-in {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  @keyframes fade-in {
    from { opacity: 0; }
    to   { opacity: 1; }
  }

  /* ── Header row ── */
  .cell-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
    flex-shrink: 0;
    flex-wrap: wrap;
  }

  .eyebrow {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: #5a5248;
    flex: 1;
    min-width: 0;
  }

  .add-btn {
    font-size: 11px;
    font-weight: 500;
    padding: 4px 10px;
    border-radius: 8px;
    border: 1px solid #3a2a50;
    background: rgba(155,126,200,0.08);
    color: #9b7ec8;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.15s, color 0.15s;
    flex-shrink: 0;
  }
  .add-btn:hover { background: rgba(155,126,200,0.16); }
  .add-btn.cancel {
    background: rgba(200,120,120,0.08);
    border-color: #5a2828;
    color: #c87a7a;
  }

  /* ── Scroll area ── */
  .scroll-area {
    flex: 1;
    overflow-y: auto;
    min-height: 0;
    scrollbar-width: none;
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  /* ── Forms ── */
  .form-card {
    background: #141210;
    border: 1px solid #2a2823;
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex-shrink: 0;
  }

  .form-row {
    display: flex;
    gap: 8px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .form-label {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #5a5248;
  }

  .j-input {
    background: #1a1714;
    color: #e8e0d0;
    border: 1px solid #2e2c28;
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 12px;
    font-family: 'DM Sans', system-ui, sans-serif;
    outline: none;
    transition: border-color 0.15s;
    width: 100%;
    box-sizing: border-box;
  }
  .j-input:focus { border-color: #4a3a60; }
  .j-textarea { resize: none; line-height: 1.5; }

  .mood-row {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .mood-chip {
    font-size: 10px;
    padding: 3px 10px;
    border-radius: 20px;
    border: 1px solid;
    cursor: pointer;
    text-transform: capitalize;
    transition: all 0.15s ease;
  }

  .lucid-label {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    color: #9a9080;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .lucid-check { accent-color: #9b7ec8; }

  .save-btn {
    font-size: 11px;
    font-weight: 500;
    padding: 6px 14px;
    border-radius: 8px;
    background: rgba(155,126,200,0.14);
    color: #9b7ec8;
    border: 1px solid #3a2a50;
    cursor: pointer;
    white-space: nowrap;
    flex-shrink: 0;
    transition: background 0.15s;
  }
  .save-btn:hover { background: rgba(155,126,200,0.24); }

  /* ── Dream cards ── */
  .dream-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .dream-card {
    display: flex;
    align-items: stretch;
    background: #141210;
    border: 1px solid #252320;
    border-radius: 10px;
    overflow: hidden;
    text-align: left;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
    width: 100%;
  }
  .dream-card:hover { background: #1a1815; border-color: #352f28; }

  .dream-stripe {
    width: 3px;
    flex-shrink: 0;
    border-radius: 0;
    opacity: 0.75;
  }

  .dream-body {
    flex: 1;
    min-width: 0;
    padding: 9px 12px;
  }

  .dream-header {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 3px;
  }

  .dream-title {
    font-family: 'Lora', serif;
    font-size: 13px;
    font-weight: 500;
    color: #d8d0c0;
    flex: 1;
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .dream-badges { display: flex; gap: 4px; flex-shrink: 0; }

  .badge {
    font-size: 9px;
    padding: 2px 7px;
    border-radius: 20px;
    font-weight: 500;
  }
  .lucid-badge { background: rgba(155,126,200,0.15); color: #9b7ec8; }
  .mood-badge  { }
  .tag-badge   { background: #1a1714; color: #5a5040; }

  .dream-time {
    font-size: 9px;
    color: #4a4840;
    flex-shrink: 0;
    margin-left: auto;
    font-variant-numeric: tabular-nums;
  }

  .dream-desc {
    font-size: 11px;
    color: #7a7268;
    line-height: 1.4;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
  }

  .dream-tags { display: flex; gap: 5px; margin-top: 3px; }
  .tag { font-size: 9px; color: #4a4438; }

  /* ── Photos ── */
  .photo-nav { display: flex; align-items: center; gap: 4px; flex: 1; }

  .yr-btn {
    font-size: 11px;
    color: #7a7268;
    background: none;
    border: none;
    cursor: pointer;
    padding: 2px 4px;
    transition: color 0.15s;
  }
  .yr-btn:hover { color: #e8e0d0; }
  .yr-label { font-size: 11px; color: #7a7268; font-variant-numeric: tabular-nums; }

  .photo-preview {
    width: 100%;
    height: 60px;
    object-fit: cover;
    border-radius: 8px;
  }

  .photo-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    flex-shrink: 0;
  }

  .month-col {}
  .month-label {
    font-size: 8px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #4a4840;
    margin-bottom: 4px;
  }

  .dot-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 2px;
  }

  .day-dot {
    width: 100%;
    aspect-ratio: 1;
    border-radius: 3px;
    border: none;
    cursor: default;
    transition: opacity 0.15s;
  }
  .dot-future { background: #1e1c18; opacity: 0.3; }
  .dot-empty  { background: #252320; opacity: 0.5; }
  .dot-filled { cursor: pointer; opacity: 0.9; }
  .dot-filled:hover { opacity: 1; transform: scale(1.15); }

  .photo-count {
    font-size: 9px;
    color: #4a4840;
    margin-top: 8px;
    letter-spacing: 0.05em;
  }

  /* ── Habits ── */
  .habit-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .habit-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    background: #141210;
    border: 1px solid #252320;
    border-radius: 10px;
    transition: background 0.12s;
  }
  .habit-row:hover { background: #1a1815; }

  .habit-check {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: 1.5px solid;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .habit-name {
    font-size: 12.5px;
    flex: 1;
    transition: color 0.2s;
  }

  .habit-streak {
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 0.05em;
    flex-shrink: 0;
  }

  .color-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .color-dot {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    border: none;
    cursor: pointer;
    transition: transform 0.15s;
    flex-shrink: 0;
  }
  .color-dot:hover { transform: scale(1.15); }

  /* ── Quotes ── */
  .tag-pills { display: flex; gap: 4px; flex-wrap: wrap; }

  .tag-pill {
    font-size: 9px;
    padding: 2px 8px;
    border-radius: 20px;
    background: transparent;
    color: #5a5248;
    border: 1px solid transparent;
    cursor: pointer;
    transition: all 0.15s;
  }
  .tag-pill:hover { color: #9a9080; }
  .tag-pill.tag-active { background: #252320; color: #c8c0b0; border-color: #3a3530; }

  .quote-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .quote-card {
    display: flex;
    align-items: flex-start;
    gap: 4px;
    background: #141210;
    border: 1px solid #252320;
    border-radius: 10px;
    padding: 10px 12px 10px 8px;
    position: relative;
    transition: background 0.12s;
  }
  .quote-card:hover { background: #1a1815; }

  .quote-mark {
    font-family: 'Lora', serif;
    font-size: 36px;
    line-height: 0.7;
    color: #3a3430;
    flex-shrink: 0;
    margin-top: 4px;
    user-select: none;
  }

  .quote-content { flex: 1; min-width: 0; }

  .quote-text {
    font-family: 'Lora', serif;
    font-size: 12px;
    font-style: italic;
    line-height: 1.55;
    color: #c0b8a8;
    margin: 0 0 5px 0;
  }

  .quote-attr {
    font-size: 10px;
    color: #6a6258;
  }
  .quote-source { font-style: italic; }

  .quote-tags {
    display: flex;
    gap: 5px;
    margin-top: 4px;
  }

  .quote-del {
    position: absolute;
    top: 8px;
    right: 8px;
    opacity: 0;
  }
  .quote-card:hover .quote-del { opacity: 1; }

  /* ── Letters ── */
  .letter-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .letter-card {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 10px;
    text-align: left;
    width: 100%;
    border: 1px solid;
    transition: all 0.15s;
  }
  .letter-sealed {
    background: #141210;
    border-color: #252320;
    cursor: default;
    opacity: 0.7;
  }
  .letter-open {
    background: rgba(200,154,90,0.06);
    border-color: rgba(200,154,90,0.2);
    cursor: pointer;
  }
  .letter-open:hover { background: rgba(200,154,90,0.1); }

  .letter-icon {
    font-size: 16px;
    flex-shrink: 0;
    line-height: 1;
  }
  .open-icon  { color: #c89a5a; }
  .seal-icon  { color: #3a3530; }

  .letter-meta { flex: 1; min-width: 0; }

  .letter-status {
    font-size: 11px;
    font-weight: 500;
  }
  .letter-status.open   { color: #c89a5a; }
  .letter-status.sealed { color: #5a5248; }

  .letter-date {
    font-size: 9px;
    color: #4a4840;
    margin-top: 1px;
  }

  .letter-read {
    font-size: 10px;
    color: #c89a5a;
    flex-shrink: 0;
    opacity: 0.7;
  }

  /* ── Shared ── */
  .empty-text {
    font-size: 12px;
    color: #5a5248;
    padding: 4px 0;
  }

  .del-btn {
    font-size: 10px;
    color: #c87a7a;
    background: none;
    border: none;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.15s;
    padding: 0 2px;
    flex-shrink: 0;
  }
  .habit-row:hover .del-btn,
  .quote-card:hover .quote-del { opacity: 1; }

  .del-text {
    font-size: 11px;
    color: #c87a7a;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    transition: color 0.15s;
  }
  .del-text:hover { color: #e87a7a; }

  /* ── Modals ── */
  .modal-bg {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.75);
    z-index: 50;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }

  .modal {
    background: #1c1b17;
    border-radius: 18px;
    width: 100%;
    max-width: 500px;
    max-height: 85vh;
    overflow: hidden;
    display: flex;
    box-shadow: 0 20px 60px rgba(0,0,0,0.6);
    border: 1px solid rgba(255,255,255,0.05);
  }

  .modal-stripe {
    width: 4px;
    flex-shrink: 0;
    border-radius: 18px 0 0 18px;
  }

  .modal-inner {
    flex: 1;
    min-width: 0;
    padding: 22px 24px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .modal-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
  }

  .modal-title {
    font-family: 'Lora', serif;
    font-size: 20px;
    font-weight: 500;
    color: #e0d8c8;
    line-height: 1.2;
  }

  .modal-sub {
    font-size: 11px;
    color: #6a6258;
    margin-top: 3px;
  }

  .modal-x {
    font-size: 16px;
    color: #5a5248;
    background: none;
    border: none;
    cursor: pointer;
    flex-shrink: 0;
    padding: 0;
    line-height: 1;
    transition: color 0.15s;
  }
  .modal-x:hover { color: #e8e0d0; }

  .modal-badges { display: flex; flex-wrap: wrap; gap: 5px; }

  .modal-body-text {
    font-family: 'Lora', serif;
    font-size: 13px;
    color: #c0b8a8;
    line-height: 1.7;
    white-space: pre-wrap;
    margin: 0;
  }

  .photo-modal {
    flex-direction: column;
    max-width: 460px;
    max-height: 82vh;
  }
  .photo-modal-img {
    flex: 1;
    min-height: 0;
    width: 100%;
    object-fit: contain;
    background: #0d0d0f;
    display: block;
  }
  .photo-modal-info {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 16px 20px;
    gap: 12px;
    flex-shrink: 0;
  }
  .photo-caption {
    font-family: 'Lora', serif;
    font-size: 13px;
    color: #c0b8a8;
    margin-top: 5px;
  }
  .modal-actions { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }

  .letter-body {
    font-family: 'Lora', serif;
    font-size: 14px;
    color: #c8bfa8;
    line-height: 1.8;
    white-space: pre-wrap;
    margin: 0;
  }

  /* ── Memories ── */
  .memories-cell {
    padding: 14px 16px;
  }

  .mem-subtitle {
    font-size: 9px;
    color: #3a3830;
    letter-spacing: 0.08em;
  }

  .mem-strip {
    display: flex;
    gap: 10px;
    overflow-x: auto;
    scrollbar-width: none;
    padding-bottom: 2px;
  }

  .mem-window {
    flex-shrink: 0;
    background: #141210;
    border: 1px solid #252320;
    border-radius: 12px;
    padding: 12px 14px;
    min-width: 200px;
    max-width: 260px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .mem-window-head {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex-shrink: 0;
  }

  .mem-label {
    font-size: 11px;
    font-weight: 600;
    color: #c89a5a;
    letter-spacing: 0.02em;
  }

  .mem-date {
    font-size: 9px;
    color: #4a4438;
    font-variant-numeric: tabular-nums;
  }

  .mem-entries {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .mem-entry {
    display: flex;
    align-items: center;
    gap: 8px;
    text-align: left;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    width: 100%;
    border-radius: 8px;
    transition: background 0.12s;
  }
  .mem-entry:hover { background: rgba(255,255,255,0.03); }

  .mem-photo {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .mem-photo-thumb {
    width: 100%;
    height: 80px;
    object-fit: cover;
    border-radius: 8px;
    display: block;
  }

  .mem-photo-cap {
    font-size: 10px;
    color: #7a7268;
    font-family: 'Lora', serif;
    font-style: italic;
    padding: 0 2px;
    line-height: 1.3;
  }

  .mem-dream {
    padding: 6px 8px;
    border-radius: 8px;
    background: rgba(255,255,255,0.02);
  }

  .mem-dream-dot {
    width: 3px;
    height: 28px;
    border-radius: 2px;
    flex-shrink: 0;
    opacity: 0.7;
  }

  .mem-dream-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .mem-dream-title {
    font-family: 'Lora', serif;
    font-size: 12px;
    color: #c0b8a8;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .mem-dream-mood {
    font-size: 9px;
    text-transform: capitalize;
    letter-spacing: 0.04em;
  }

  @media (max-width: 768px) {
    .j-root {
      padding: 14px 14px 0;
    }

    .j-bento {
      display: flex !important;
      flex-direction: column !important;
      gap: 10px !important;
      grid-template-rows: unset !important;
    }

    .j-cell {
      grid-column: unset !important;
      grid-row: unset !important;
      height: auto !important;
      min-height: 160px;
    }

    .dreams-cell {
      min-height: 340px;
    }

    .habits-cell {
      min-height: 240px;
    }
  }
</style>
