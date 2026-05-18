<script>
  import { onMount } from 'svelte';
  import { todayIST, istDate, fmtDate } from '../ist.js';
  let summary = [], events = [], expandedPerson = null;
  let showForm = false;
  let meetupDate = todayIST();
  let meetupNotes = '';
  let meetupPeople = [{ name: '', tag: 'Friend' }];
  let status = '';

  function groupEvents(evs) {
    const map = new Map();
    for (const e of evs) {
      const key = `${istDate(e.timestamp)}::${(e.metadata.notes||'').trim()}`;
      if (!map.has(key)) map.set(key, { ...e, metadata: { ...e.metadata, people: [] } });
      const g = map.get(key);
      for (const p of (e.metadata.people || [])) {
        if (!g.metadata.people.find(q => q.name === p.name)) g.metadata.people.push(p);
      }
    }
    return [...map.values()];
  }

  function timeAgo(ts) {
    const s = Math.floor((Date.now()-new Date(ts))/1000);
    if (s<3600) return `${Math.floor(s/60)}m ago`;
    if (s<86400) return `${Math.floor(s/3600)}h ago`;
    const d=Math.floor(s/86400); if(d<30) return `${d}d ago`;
    return fmtDate(ts);
  }
  async function load() {
    const [evRes, sumRes] = await Promise.all([
      fetch('/api/events?source=people&event_type=meetup'),
      fetch('/api/people/summary'),
    ]);
    events = await evRes.json();
    summary = await sumRes.json();
  }
  async function save() {
    const valid = meetupPeople.filter(p => p.name.trim());
    if (!valid.length) return;
    status = 'saving…';
    await fetch('/api/people/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date: meetupDate, notes: meetupNotes, people: valid }),
    });
    status = 'Saved!';
    meetupPeople = [{ name: '', tag: 'Friend' }]; meetupNotes = '';
    showForm = false;
    load();
  }
  onMount(load);
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="flex items-center gap-3 mb-3">
    <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider flex-1">People</div>
    <button on:click={() => showForm=!showForm}
      class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-3 py-1 rounded-lg text-xs">
      {showForm ? 'Cancel' : '+ Log meetup'}
    </button>
    {#if status}<span class="text-xs text-[#9a9080]">{status}</span>{/if}
  </div>

  {#if showForm}
    <div class="bg-[#1a1714] rounded-xl p-4 mb-4 flex flex-col gap-3">
      <div class="flex gap-3">
        <div class="flex flex-col gap-1">
          <label class="text-xs text-[#9a9080]">Date</label>
          <input type="date" bind:value={meetupDate}
            class="bg-[#242019] text-[#e8e0d0] rounded-lg px-2 py-1.5 text-sm border border-[#3a3530]" />
        </div>
        <div class="flex flex-col gap-1 flex-1">
          <label class="text-xs text-[#9a9080]">Notes</label>
          <input type="text" bind:value={meetupNotes} placeholder="Coffee at Blue Tokai…"
            class="bg-[#242019] text-[#e8e0d0] rounded-lg px-2 py-1.5 text-sm border border-[#3a3530]" />
        </div>
      </div>
      {#each meetupPeople as person, i}
        <div class="flex gap-2">
          <input type="text" bind:value={person.name} placeholder="Name"
            class="bg-[#242019] text-[#e8e0d0] rounded-lg px-2 py-1.5 text-sm border border-[#3a3530] flex-1" />
          <select bind:value={person.tag}
            class="bg-[#242019] text-[#e8e0d0] rounded-lg px-2 py-1.5 text-sm border border-[#3a3530]">
            {#each ['Friend','Family','Colleague','Other'] as t}<option>{t}</option>{/each}
          </select>
          {#if meetupPeople.length > 1}
            <button on:click={() => meetupPeople=meetupPeople.filter((_,j)=>j!==i)}
              class="text-[#9a9080] hover:text-[#e8e0d0] px-1">✕</button>
          {/if}
        </div>
      {/each}
      <button on:click={() => meetupPeople=[...meetupPeople,{name:'',tag:'Friend'}]}
        class="text-xs text-[#6b9e6b] hover:text-[#8abf8a] self-start">+ Add person</button>
      <button on:click={save}
        class="bg-[#6b9e6b] hover:bg-[#5a8e5a] text-[#1a1714] font-medium px-4 py-1.5 rounded-lg text-sm self-start">Save</button>
    </div>
  {/if}

  {#if summary.length === 0}
    <p class="text-sm text-[#9a9080]">No meetups logged yet.</p>
  {:else}
    <div class="flex flex-col gap-2 max-h-72 overflow-y-auto">
      {#each summary as person}
        {@const days = Math.floor((Date.now()-new Date(person.last_seen))/86400000)}
        {@const urgency = days<30?'text-[#6b9e6b]':days<90?'text-[#c8a84b]':'text-[#c87a7a]'}
        {@const history = groupEvents(events.filter(e=>e.metadata.name===person.name))}
        <div class="bg-[#1a1714] rounded-xl overflow-hidden">
          <button class="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-[#242019]"
            on:click={() => expandedPerson=expandedPerson===person.name?null:person.name}>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium">{person.name}</span>
                <span class="text-xs px-1.5 py-0.5 rounded-full bg-[#242019] text-[#9a9080]">{person.tag}</span>
              </div>
              {#if person.last_notes}<div class="text-xs text-[#9a9080] mt-0.5 truncate">{person.last_notes}</div>{/if}
            </div>
            <div class="text-right shrink-0">
              <div class="text-xs {urgency} font-medium">{days===0?'today':`${days}d ago`}</div>
              <div class="text-xs text-[#9a9080]">{person.total_meetups} meetup{person.total_meetups!==1?'s':''}</div>
            </div>
          </button>
          {#if expandedPerson===person.name}
            <div class="border-t border-[#3a3530] px-3 py-2 flex flex-col gap-1.5">
              {#each history as e}
                <div class="flex items-start gap-2">
                  <span class="text-xs text-[#9a9080] shrink-0">
                    {fmtDate(e.timestamp, {month:'short',day:'numeric',year:'numeric'})}
                  </span>
                  <span class="text-xs text-[#c8c0b0] flex-1">{e.metadata.notes||'—'}</span>
                  <button on:click={async()=>{await fetch(`/api/events/${e.id}`,{method:'DELETE'});load();}}
                    class="text-xs text-[#c87a7a] hover:text-[#e87a7a] shrink-0">✕</button>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
