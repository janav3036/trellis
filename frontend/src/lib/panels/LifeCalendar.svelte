<script>
  import { onMount } from 'svelte';

  let calendarEvents = [];
  const today = new Date();
  let viewYear = today.getFullYear();
  let viewMonth = today.getMonth();
  let selectedDay = null;

  const MONTH_NAMES = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const DOW = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];

  const CAL_COLORS = {
    'Projects':       { bg: '#2a3d2a', text: '#8abf8a' },
    'Gym / Sports':   { bg: '#3d2e1a', text: '#c89a5a' },
    'College':        { bg: '#1a2a3d', text: '#6b9ecc' },
    'Slots':          { bg: '#2e1a1a', text: '#c87a7a' },
    'Side projects':  { bg: '#2a1a3d', text: '#9b7ec8' },
    'Courses & Studies': { bg: '#2e2a1a', text: '#c8a84b' },
    'Test & ICAs':    { bg: '#1a2e2e', text: '#5abfbf' },
  };
  const DEFAULT_COLOR = { bg: '#2a2a2a', text: '#9a9080' };

  function calColor(name) { return CAL_COLORS[name] || DEFAULT_COLOR; }
  function isoDate(d) {
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  }
  function isToday(d) { return isoDate(d) === isoDate(today); }
  function formatDuration(mins) {
    if (!mins) return '';
    const h = Math.floor(mins/60), m = mins%60;
    if (h === 0) return `${m}m`; if (m === 0) return `${h}h`; return `${h}h ${m}m`;
  }

  $: calendarGrid = (() => {
    const first = new Date(viewYear, viewMonth, 1);
    const last = new Date(viewYear, viewMonth+1, 0);
    const prefix = first.getDay() === 0 ? 6 : first.getDay() - 1;
    const cells = [];
    for (let i = prefix; i > 0; i--) cells.push({ date: new Date(viewYear, viewMonth, 1-i), inMonth: false });
    for (let d = 1; d <= last.getDate(); d++) cells.push({ date: new Date(viewYear, viewMonth, d), inMonth: true });
    while (cells.length % 7 !== 0) {
      cells.push({ date: new Date(viewYear, viewMonth+1, cells.length - last.getDate() - prefix + 1), inMonth: false });
    }
    return cells;
  })();

  $: eventsByDate = (() => {
    const map = {};
    for (const e of calendarEvents) {
      const key = e.timestamp.slice(0,10);
      if (!map[key]) map[key] = [];
      map[key].push(e);
    }
    return map;
  })();

  onMount(async () => {
    calendarEvents = await (await fetch('/api/events?source=calendar&event_type=event')).json();
  });
</script>

<div class="bg-[#242019] rounded-xl p-4 w-full">
  <div class="flex items-center gap-3 mb-3">
    <button on:click={() => { if(viewMonth===0){viewMonth=11;viewYear--;}else viewMonth--; }}
      class="bg-[#1a1714] hover:bg-[#2a2520] px-2 py-1 rounded text-sm">←</button>
    <div class="text-xs font-semibold text-[#9a9080] uppercase tracking-wider flex-1 text-center">
      {MONTH_NAMES[viewMonth]} {viewYear}
    </div>
    <button on:click={() => { if(viewMonth===11){viewMonth=0;viewYear++;}else viewMonth++; }}
      class="bg-[#1a1714] hover:bg-[#2a2520] px-2 py-1 rounded text-sm">→</button>
  </div>

  <div class="grid grid-cols-7 gap-0.5 mb-0.5">
    {#each DOW as dow}<div class="text-center text-[9px] text-[#9a9080] py-0.5">{dow}</div>{/each}
  </div>

  <div class="grid grid-cols-7 gap-0.5">
    {#each calendarGrid as cell}
      {@const dateKey = isoDate(cell.date)}
      {@const events = eventsByDate[dateKey] || []}
      {@const todayCell = isToday(cell.date)}
      <div
        class="rounded p-1 min-h-[52px] flex flex-col cursor-pointer
          {cell.inMonth ? 'bg-[#1a1714]' : 'bg-[#181613]'}
          {todayCell ? 'ring-1 ring-[#6b9e6b]' : ''}
          {selectedDay === dateKey ? 'ring-1 ring-[#c8a84b]' : ''}"
        on:click={() => selectedDay = selectedDay === dateKey ? null : dateKey}
      >
        <div class="text-[9px] mb-0.5 {todayCell ? 'text-[#6b9e6b] font-semibold' : cell.inMonth ? 'text-[#9a9080]' : 'text-[#4a4540]'}">
          {cell.date.getDate()}
        </div>
        {#each events.slice(0,2) as e}
          <div class="text-[8px] rounded px-0.5 py-0.5 mb-0.5 truncate leading-tight"
            style="background:{calColor(e.metadata.calendar_name).bg};color:{calColor(e.metadata.calendar_name).text}"
            title="{e.metadata.title}">{e.metadata.title}</div>
        {/each}
        {#if events.length > 2}<div class="text-[8px] text-[#9a9080]">+{events.length-2}</div>{/if}
      </div>
    {/each}
  </div>

  {#if selectedDay}
    {@const dayEvents = eventsByDate[selectedDay] || []}
    <div class="mt-3 bg-[#1a1714] rounded-xl p-3">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs font-medium">
          {new Date(selectedDay+'T12:00:00').toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'})}
        </span>
        <button on:click={() => selectedDay=null} class="text-xs text-[#9a9080] hover:text-[#e8e0d0]">✕</button>
      </div>
      {#if dayEvents.length === 0}
        <p class="text-xs text-[#9a9080]">No events</p>
      {:else}
        <div class="flex flex-col gap-1.5">
          {#each dayEvents as e}
            {@const color = calColor(e.metadata.calendar_name)}
            <div class="flex items-center gap-2 px-2 py-1.5 rounded-lg" style="background:{color.bg}">
              <div class="text-xs font-medium truncate flex-1" style="color:{color.text}">{e.metadata.title}</div>
              <div class="text-[10px] text-[#9a9080] shrink-0">
                {e.metadata.calendar_name}{#if e.metadata.duration_minutes} · {formatDuration(e.metadata.duration_minutes)}{/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>
