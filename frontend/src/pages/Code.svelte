<script>
  import { onMount } from 'svelte';
  import Plotly from 'plotly.js-dist-min';
  import { daysAgoIST, buildDatesIST, groupByDayIST, groupByWeekIST, istDate, istTime, fmtDate } from '../lib/ist.js';

  let chartEl;
  let range         = 'monthly';
  let recentCommits = [];
  let yearCommits   = [];
  let prs           = [];
  let allRepos      = [];
  let languages     = [];
  let ideas         = [];
  let dailyCommits  = [];
  let backfillDate  = '';
  let backfillStatus = '';
  let newIdea       = '';
  let editingId     = null;
  let editText      = '';
  let editDesc      = '';

  const focusOnMount = (node) => { setTimeout(() => node.focus(), 0); };

  const RANGES = [
    { key: 'daily',   label: 'Today' },
    { key: 'monthly', label: '30d'   },
    { key: '6m',      label: '6m'    },
    { key: 'yearly',  label: 'Year'  },
  ];

  const STATUS_NEXT  = { active: 'shipped', shipped: 'archived', archived: 'active' };
  const STATUS_STYLE = {
    active:   { bg: '#0e4429', color: '#3fb950' },
    shipped:  { bg: '#112d52', color: '#58a6ff' },
    archived: { bg: '#21262d', color: '#8b949e' },
  };

  const LANG_COLORS = {
    Python:'#3572A5', JavaScript:'#f1e05a', TypeScript:'#2b7489',
    HTML:'#e34c26', CSS:'#563d7c', Go:'#00ADD8', Rust:'#dea584',
    Java:'#b07219', 'C++':'#f34b7d', 'C#':'#178600', Ruby:'#701516',
    Swift:'#F05138', Kotlin:'#7F52FF', Shell:'#89e051', Vue:'#41b883',
    Svelte:'#ff3e00', Dart:'#00B4AB', PHP:'#4F5D95',
  };
  const langColor = n => LANG_COLORS[n] || '#3fb950';

  const plotLayout = {
    paper_bgcolor:'#0d1117', plot_bgcolor:'#0d1117',
    font:{ color:'#e6edf3', size:11 },
    xaxis:{ gridcolor:'#21262d', tickcolor:'#8b949e', tickfont:{ size:10 } },
    yaxis:{ gridcolor:'#21262d', tickcolor:'#8b949e', title:'commits', rangemode:'tozero', tickfont:{ size:10 } },
    margin:{ t:30, r:10, b:50, l:45 },
  };

  // ── streak ───────────────────────────────────────────────────────────────────
  function computeStreak(commits) {
    const days = new Set(commits.map(c => istDate(c.timestamp)));
    let streak = 0;
    const today = daysAgoIST(0);
    const d = new Date(today + 'T12:00:00');
    if (!days.has(today)) d.setDate(d.getDate() - 1);
    while (true) {
      const s = d.toLocaleDateString('en-CA');
      if (!days.has(s)) break;
      streak++;
      d.setDate(d.getDate() - 1);
    }
    return streak;
  }

  // ── heatmap ──────────────────────────────────────────────────────────────────
  function computeHeatmap(commits) {
    const counts = {};
    for (const c of commits) {
      const d = istDate(c.timestamp);
      counts[d] = (counts[d] || 0) + 1;
    }
    const today = daysAgoIST(0);
    const start = new Date(today + 'T12:00:00');
    start.setDate(start.getDate() - 364);
    start.setDate(start.getDate() - start.getDay());
    const cells = [];
    const d = new Date(start);
    while (true) {
      const week = [];
      for (let i = 0; i < 7; i++) {
        const s = d.toLocaleDateString('en-CA');
        week.push({ date: s, count: counts[s] || 0, future: s > today });
        d.setDate(d.getDate() + 1);
      }
      cells.push(week);
      if (week[6].date >= today) break;
    }
    return { cells, maxCount: Math.max(1, ...Object.values(counts)) };
  }

  function heatColor(count, maxCount, future) {
    if (future || count === 0) return '#161b22';
    const r = count / maxCount;
    if (r < 0.25) return '#0e4429';
    if (r < 0.5)  return '#006d32';
    if (r < 0.75) return '#26a641';
    return '#39d353';
  }

  function monthLabel(cells, wi) {
    const curr = cells[wi]?.[0]?.date, prev = cells[wi-1]?.[0]?.date;
    if (!curr) return '';
    if (!prev || curr.slice(0,7) !== prev.slice(0,7))
      return new Date(curr+'T12:00:00').toLocaleString('en-US',{month:'short'});
    return '';
  }

  // ── chart ────────────────────────────────────────────────────────────────────
  async function loadChart(r) {
    range = r;
    dailyCommits = [];
    if (r === 'daily') {
      dailyCommits = await (await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(0)}`)).json();
      if (chartEl) Plotly.purge(chartEl);
      return;
    }
    let evs, dates, counts, title;
    if (r === 'monthly') {
      evs = await (await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(29)}`)).json();
      dates = buildDatesIST(30); counts = groupByDayIST(evs); title = 'Last 30 days';
    } else if (r === '6m') {
      evs = await (await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(179)}`)).json();
      dates = buildDatesIST(180); counts = groupByDayIST(evs); title = 'Last 6 months';
    } else {
      evs = await (await fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(364)}`)).json();
      counts = groupByWeekIST(evs); dates = Object.keys(counts).sort(); title = 'Last year';
    }
    Plotly.react(chartEl,
      [{ x:dates, y:dates.map(d=>counts[d]||0), type:'bar', marker:{ color:'#3fb950' } }],
      { ...plotLayout, title:{ text:title, font:{ color:'#e6edf3', size:12 } } }
    );
  }

  function timeAgo(ts) {
    const sec = Math.floor((Date.now() - new Date(ts)) / 1000);
    if (sec < 60)  return 'just now';
    const min = Math.floor(sec/60);
    if (min < 60)  return `${min}m ago`;
    const hr = Math.floor(min/60);
    if (hr < 24)   return `${hr}h ago`;
    const day = Math.floor(hr/24);
    if (day < 30)  return `${day}d ago`;
    return fmtDate(ts);
  }

  async function doBackfill() {
    if (!backfillDate) return;
    backfillStatus = 'running…';
    const res  = await fetch('/api/backfill/github', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ date_from: backfillDate }),
    });
    const data = await res.json();
    backfillStatus = `+${data.count} commits`;
    [yearCommits, recentCommits, allRepos] = await Promise.all([
      fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(364)}`).then(r=>r.json()),
      fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(29)}`).then(r=>r.json()),
      fetch('/api/github/repos').then(r=>r.json()),
    ]);
    await loadChart(range);
  }

  // ── ideas ────────────────────────────────────────────────────────────────────
  async function addIdea() {
    const text = newIdea.trim();
    if (!text) return;
    const res = await fetch('/api/ideas', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ text }),
    });
    const { id } = await res.json();
    ideas = [{ id, text, status:'active', repo:null, created_at: new Date().toISOString() }, ...ideas];
    newIdea = '';
  }

  async function cycleStatus(idea) {
    const status = STATUS_NEXT[idea.status] || 'active';
    await fetch(`/api/ideas/${idea.id}`, {
      method:'PATCH', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ status }),
    });
    ideas = ideas.map(i => i.id === idea.id ? { ...i, status } : i);
  }

  async function deleteIdea(id) {
    await fetch(`/api/ideas/${id}`, { method:'DELETE' });
    ideas = ideas.filter(i => i.id !== id);
  }

  function startEdit(idea) {
    editingId = idea.id;
    editText  = idea.text;
    editDesc  = idea.description || '';
  }

  async function saveEdit(id) {
    const text = editText.trim();
    if (!text) { cancelEdit(); return; }
    const description = editDesc.trim();
    await fetch(`/api/ideas/${id}`, {
      method:'PATCH', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ text, description }),
    });
    ideas = ideas.map(i => i.id === id ? { ...i, text, description } : i);
    cancelEdit();
  }

  function cancelEdit() {
    editingId = null;
    editText  = '';
    editDesc  = '';
  }

  onMount(async () => {
    const [recentRes, yearRes, prRes, reposRes, langsRes, ideasRes] = await Promise.all([
      fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(29)}`),
      fetch(`/api/events?source=github&event_type=commit&date_from=${daysAgoIST(364)}`),
      fetch(`/api/events?source=github&event_type=pr`),
      fetch('/api/github/repos'),
      fetch('/api/github/languages'),
      fetch('/api/ideas'),
      loadChart('monthly'),
    ]);
    recentCommits = await recentRes.json();
    yearCommits   = await yearRes.json();
    prs           = await prRes.json();
    allRepos      = await reposRes.json();
    languages     = await langsRes.json();
    ideas         = await ideasRes.json();
  });

  $: streak         = computeStreak(yearCommits);
  $: commits30d     = recentCommits.length;
  $: activeRepos    = [...new Set(recentCommits.map(c=>c.metadata?.repo))].filter(Boolean).length;
  $: openPRs        = prs.filter(p=>p.metadata?.state==='open').length;
  $: heatmap        = computeHeatmap(yearCommits);
  $: totalLangBytes  = languages.reduce((s,l)=>s+l.bytes,0) || 1;
  $: displayLangs   = languages.slice(0, 10);
  $: displayTotal   = displayLangs.reduce((s,l)=>s+l.bytes,0) || 1;
</script>

<main class="p-5 min-h-screen" style="background:#0d1117; color:#e6edf3">
  <div class="grid gap-4" style="
    grid-template-columns: repeat(20, 1fr);
    grid-template-rows: 52px 56vh 40vh 40vh;
  ">

    <!-- ── Title / stats / backfill: cols 1-13, row 1 ── -->
    <div class="flex items-center gap-3 min-w-0" style="grid-column:1/14; grid-row:1">
      <h1 class="text-2xl font-semibold shrink-0">Code</h1>

      {#if streak > 0}
        <span class="px-2.5 py-0.5 rounded-full text-sm font-semibold shrink-0"
              style="background:#0e4429; color:#3fb950">🔥 {streak}d</span>
      {/if}
      <span class="text-sm shrink-0" style="color:#8b949e">
        <span style="color:#e6edf3">{commits30d}</span> commits
      </span>
      <span class="text-sm shrink-0" style="color:#8b949e">
        <span style="color:#e6edf3">{activeRepos}</span> repos
      </span>
      {#if openPRs > 0}
        <span class="text-sm shrink-0" style="color:#8b949e">
          <span style="color:#e6edf3">{openPRs}</span> open PRs
        </span>
      {/if}

      <div class="ml-auto flex items-center gap-2 shrink-0">
        <input type="date" bind:value={backfillDate}
          class="rounded-lg px-2.5 py-1 text-xs border"
          style="background:#161b22; color:#e6edf3; border-color:#30363d" />
        <button on:click={doBackfill}
          class="px-3 py-1 rounded-lg text-xs font-medium"
          style="background:#238636; color:#fff">Backfill</button>
        {#if backfillStatus}
          <span class="text-xs" style="color:#8b949e">{backfillStatus}</span>
        {/if}
      </div>
    </div>

    <!-- ── Recent Commits: cols 14-20, rows 1-2 ── -->
    <div class="rounded-xl p-4 flex flex-col overflow-hidden"
         style="grid-column:14/21; grid-row:1/3; background:#161b22">
      <div class="text-xs font-semibold uppercase tracking-wider mb-3 shrink-0" style="color:#8b949e">
        Recent Commits
      </div>
      <div class="flex flex-col flex-1 overflow-y-auto" style="scrollbar-width:none; gap:0">
        {#each recentCommits.slice(0,50) as c}
          <div class="flex items-start gap-2 py-2 border-b" style="border-color:#21262d">
            <div class="flex-1 min-w-0">
              <span class="text-[10px] font-mono px-1.5 py-0.5 rounded mr-1 inline-block"
                    style="background:#0d1117; color:#3fb950">{c.metadata?.repo?.split('/')[1]}</span>
              <span class="text-sm leading-snug">{c.metadata?.message}</span>
            </div>
            <span class="text-xs shrink-0 mt-0.5 tabular-nums" style="color:#8b949e">{timeAgo(c.timestamp)}</span>
          </div>
        {:else}
          <p class="text-sm mt-4" style="color:#8b949e">No commits in the last 30 days.</p>
        {/each}
      </div>
    </div>

    <!-- ── Commits chart: cols 1-13, row 2 ── -->
    <div class="rounded-xl p-4 flex flex-col overflow-hidden"
         style="grid-column:1/14; grid-row:2; background:#161b22">
      <div class="flex items-center gap-1.5 mb-3 shrink-0">
        <div class="text-xs font-semibold uppercase tracking-wider flex-1" style="color:#8b949e">Commits</div>
        {#each RANGES as r}
          <button on:click={() => loadChart(r.key)}
            class="px-2.5 py-1 rounded text-xs font-medium"
            style="background:{range===r.key?'#238636':'transparent'};
                   color:{range===r.key?'#fff':'#8b949e'}">
            {r.label}
          </button>
        {/each}
      </div>

      {#if range === 'daily'}
        <div class="flex flex-col gap-1.5 flex-1 overflow-y-auto" style="scrollbar-width:none">
          {#each dailyCommits as c}
            <div class="flex items-center gap-3 px-3 py-2 rounded-lg" style="background:#0d1117">
              <span class="text-xs shrink-0 font-mono" style="color:#8b949e">{istTime(c.timestamp)}</span>
              <span class="text-xs px-2 py-0.5 rounded font-mono shrink-0"
                    style="background:#161b22; color:#3fb950">{c.metadata?.repo?.split('/')[1]}</span>
              <span class="text-sm truncate">{c.metadata?.message}</span>
            </div>
          {:else}
            <p class="text-sm mt-6 text-center" style="color:#8b949e">No commits today.</p>
          {/each}
        </div>
      {:else}
        <div bind:this={chartEl} class="flex-1 min-h-0"></div>
      {/if}
    </div>

    <!-- ── Repositories: cols 1-6, row 3 ── -->
    <div class="rounded-xl p-4 flex flex-col overflow-hidden"
         style="grid-column:1/7; grid-row:3; background:#161b22">
      <div class="text-xs font-semibold uppercase tracking-wider mb-3 shrink-0" style="color:#8b949e">
        Repositories
      </div>
      <div class="flex flex-col gap-2 flex-1 overflow-y-auto" style="scrollbar-width:none">
        {#each allRepos as r}
          <div class="flex items-center justify-between px-3 py-2 rounded-lg" style="background:#0d1117">
            <div class="min-w-0">
              <div class="text-sm font-medium truncate">{r.repo.split('/')[1]}</div>
              <div class="text-xs truncate" style="color:#8b949e">{r.repo.split('/')[0]}</div>
            </div>
            <div class="text-xs font-mono tabular-nums shrink-0 ml-3" style="color:#3fb950">
              {r.commits}
            </div>
          </div>
        {:else}
          <p class="text-sm" style="color:#8b949e">No repos yet.</p>
        {/each}
      </div>
    </div>

    <!-- ── Ideas: cols 7-10, row 3 ── -->
    <div class="rounded-xl p-4 flex flex-col overflow-hidden"
         style="grid-column:7/11; grid-row:3; background:#161b22">
      <div class="text-xs font-semibold uppercase tracking-wider mb-3 shrink-0" style="color:#8b949e">
        Ideas
      </div>

      <!-- Add input -->
      <div class="flex gap-1.5 mb-3 shrink-0">
        <input
          type="text"
          bind:value={newIdea}
          placeholder="New idea…"
          class="flex-1 min-w-0 rounded-lg px-2.5 py-1.5 text-xs border"
          style="background:#0d1117; color:#e6edf3; border-color:#30363d; outline:none"
          on:keydown={e => e.key === 'Enter' && addIdea()}
        />
        <button on:click={addIdea}
          class="px-2.5 py-1.5 rounded-lg text-xs font-medium shrink-0"
          style="background:#238636; color:#fff">+</button>
      </div>

      <!-- Ideas list -->
      <div class="flex flex-col gap-1.5 flex-1 overflow-y-auto" style="scrollbar-width:none">
        {#each ideas as idea (idea.id)}
          <div class="group flex items-start gap-2 px-2.5 py-2 rounded-lg" style="background:#0d1117">
            <!-- Status badge (click to cycle) -->
            <button
              on:click={() => cycleStatus(idea)}
              class="text-[10px] px-1.5 py-0.5 rounded shrink-0 font-medium mt-0.5"
              style="background:{STATUS_STYLE[idea.status]?.bg}; color:{STATUS_STYLE[idea.status]?.color}"
            >{idea.status}</button>
            {#if editingId === idea.id}
              <div class="flex flex-col gap-1 flex-1 min-w-0">
                <input
                  class="text-xs rounded px-1.5 py-0.5 border leading-snug"
                  style="background:#0d1117; color:#e6edf3; border-color:#30363d; outline:none"
                  bind:value={editText}
                  placeholder="Idea…"
                  on:keydown={e => { if (e.key === 'Escape') cancelEdit(); }}
                  use:focusOnMount
                />
                <input
                  class="text-xs rounded px-1.5 py-0.5 border leading-snug"
                  style="background:#0d1117; color:#8b949e; border-color:#30363d; outline:none"
                  bind:value={editDesc}
                  placeholder="Description…"
                  on:keydown={e => { if (e.key === 'Enter') saveEdit(idea.id); if (e.key === 'Escape') cancelEdit(); }}
                  on:blur={() => saveEdit(idea.id)}
                />
              </div>
            {:else}
              <div
                class="flex flex-col flex-1 min-w-0 cursor-text"
                on:dblclick={() => startEdit(idea)}
                title="Double-click to edit"
              >
                <span class="text-xs leading-snug">{idea.text}</span>
                {#if idea.description}
                  <span class="text-[10px] leading-snug mt-0.5" style="color:#8b949e">{idea.description}</span>
                {/if}
              </div>
            {/if}
            <!-- Delete -->
            <button
              on:click={() => deleteIdea(idea.id)}
              class="text-xs opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              style="color:#8b949e">×</button>
          </div>
        {:else}
          <p class="text-xs mt-2" style="color:#8b949e">No ideas yet.</p>
        {/each}
      </div>
    </div>

    <!-- ── Right column: Heatmap (20vh) + Languages (fills rest ~60vh), cols 11-20, rows 3-4 ── -->
    <div class="flex flex-col gap-4" style="grid-column:11/21; grid-row:3/5">

      <!-- Heatmap: fixed 20vh -->
      <div class="rounded-xl p-4 flex flex-col overflow-hidden shrink-0"
           style="height:20vh; background:#161b22">
        <div class="flex items-center justify-between mb-2 shrink-0">
          <div class="text-xs font-semibold uppercase tracking-wider" style="color:#8b949e">
            Contribution Activity
          </div>
          <div class="text-xs" style="color:#8b949e">{yearCommits.length} this year</div>
        </div>

        <div class="flex gap-2 flex-1 min-h-0">
          <div class="shrink-0" style="display:grid; grid-template-rows:repeat(7,1fr); gap:2px; width:22px">
            {#each ['','Mon','','Wed','','Fri',''] as label}
              <div class="text-[9px] flex items-center justify-end" style="color:#8b949e">{label}</div>
            {/each}
          </div>
          <div class="flex-1 min-w-0 min-h-0" style="
            display:grid;
            grid-template-rows: repeat(7, 1fr);
            grid-auto-flow: column;
            grid-auto-columns: 1fr;
            gap:2px;
          ">
            {#each heatmap.cells as week}
              {#each [0,1,2,3,4,5,6] as dayIdx}
                {@const cell = week[dayIdx]}
                <div style="background:{heatColor(cell?.count??0, heatmap.maxCount, cell?.future)}; border-radius:2px"
                     title="{cell?.date}: {cell?.count??0} commit{(cell?.count??0)!==1?'s':''}">
                </div>
              {/each}
            {/each}
          </div>
        </div>
      </div>

      <!-- Languages: fills remaining ~60vh -->
      <div class="rounded-xl p-5 flex flex-col overflow-hidden flex-1 min-h-0"
           style="background:#161b22">

        {#if displayLangs.length > 0}
          <!-- Segmented bar -->
          <div class="flex shrink-0 overflow-hidden mb-4" style="height:10px; border-radius:6px">
            {#each displayLangs as lang, i}
              {@const pct = (lang.bytes / displayTotal) * 100}
              <div style="
                width:{pct}%; flex-shrink:0;
                background:{langColor(lang.language)};
                {i < displayLangs.length - 1 ? 'border-right:2px solid #0d1117' : ''}
              "></div>
            {/each}
          </div>

          <!-- Language rows — each takes equal flex-1 slice of remaining height -->
          <div class="flex flex-col gap-2 flex-1 min-h-0">
            {#each displayLangs as lang}
              {@const pct = (lang.bytes / displayTotal) * 100}
              <div class="relative flex items-center px-4 rounded-lg overflow-hidden flex-1 min-h-0"
                   style="background:#0d1117">
                <!-- Tinted fill -->
                <div class="absolute inset-0" style="width:{pct}%; background:{langColor(lang.language)}; opacity:0.12"></div>
                <!-- Left accent -->
                <div class="absolute left-0 inset-y-0 rounded-l-lg" style="width:3px; background:{langColor(lang.language)}"></div>
                <!-- Content -->
                <div class="relative flex items-center gap-3 w-full">
                  <div class="shrink-0 rounded-full" style="width:8px; height:8px; background:{langColor(lang.language)}"></div>
                  <span class="text-sm font-medium flex-1 truncate" style="color:#e6edf3">{lang.language}</span>
                  <span class="text-sm font-semibold tabular-nums shrink-0" style="color:{langColor(lang.language)}">{pct.toFixed(1)}%</span>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <p class="text-sm mt-2" style="color:#8b949e">No language data yet.</p>
        {/if}
      </div>

    </div>

    <!-- ── Pull Requests: cols 1-10, row 4 ── -->
    <div class="rounded-xl p-4 flex flex-col overflow-hidden"
         style="grid-column:1/11; grid-row:4; background:#161b22">
      <div class="text-xs font-semibold uppercase tracking-wider mb-3 shrink-0" style="color:#8b949e">
        Pull Requests
      </div>
      <div class="flex flex-col flex-1 overflow-y-auto" style="scrollbar-width:none; gap:0">
        {#each prs.slice(0, 20) as pr}
          <div class="flex items-start gap-2.5 py-2.5 border-b" style="border-color:#21262d">
            <span class="text-[10px] px-1.5 py-0.5 rounded shrink-0 mt-0.5 font-medium"
                  style="background:{pr.metadata?.state==='open'?'#0e4429':'#21262d'};
                         color:{pr.metadata?.state==='open'?'#3fb950':'#8b949e'}">
              {pr.metadata?.state}
            </span>
            <div class="flex-1 min-w-0">
              <div class="text-sm truncate">{pr.metadata?.title}</div>
              <div class="text-xs mt-0.5" style="color:#8b949e">
                {pr.metadata?.repo} #{pr.metadata?.number}
              </div>
            </div>
            <span class="text-xs shrink-0 tabular-nums" style="color:#8b949e">{timeAgo(pr.timestamp)}</span>
          </div>
        {:else}
          <p class="text-sm mt-2" style="color:#8b949e">No PRs yet.</p>
        {/each}
      </div>
    </div>

  </div>
</main>
