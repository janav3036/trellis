<script>
  import { onMount } from 'svelte';
  import { todayIST } from '../ist.js';
  export let monthOnly = false;

  let photos = [], selectedPhoto = null;
  let year = new Date().getFullYear();
  const TODAY = todayIST();
  const THIS_MONTH = new Date().getMonth();

  const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  $: photosByDate = Object.fromEntries(photos.map(p => [p.date, p]));
  $: yearDays = (() => {
    const days = [];
    const start = new Date(year, 0, 1);
    for (let d = new Date(start); d.getFullYear() === year; d.setDate(d.getDate()+1)) {
      days.push(d.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' }));
    }
    return days;
  })();
  $: yearByMonth = (() => {
    const months = [];
    for (let m=0; m<12; m++) months.push(yearDays.filter(d => parseInt(d.slice(5,7))-1===m));
    return months;
  })();
  $: photoCount = yearDays.filter(d => photosByDate[d]).length;

  // In monthOnly mode, only current month days and photo count
  $: monthDays   = yearByMonth[THIS_MONTH] || [];
  $: monthCount  = monthDays.filter(d => photosByDate[d]).length;

  onMount(async () => {
    photos = await (await fetch('/api/photos')).json();
  });
</script>

<div class="th-surface h-full flex flex-col overflow-hidden" style="border-radius:14px;padding:14px">
  <div class="flex items-center gap-3 mb-3 shrink-0">
    <a href="/#/journal"
       class="flex-1 hover:text-[#e8e0d0] transition-colors"
       style="font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.13em;color:var(--text-secondary)">
      {monthOnly ? `${MONTH_NAMES[THIS_MONTH]} ${year}` : 'Photo a Day'}
    </a>
    {#if !monthOnly}
      <button on:click={() => year--} class="th-bg th-hover-up px-2 py-0.5 rounded text-xs">←</button>
      <span class="text-xs th-muted">{year}</span>
      <button on:click={() => year++} class="th-bg th-hover-up px-2 py-0.5 rounded text-xs">→</button>
    {/if}
  </div>

  {#if monthOnly}
    <!-- Single month: 3 columns, square cells, scrollable -->
    <div class="flex-1 overflow-y-auto min-h-0" style="scrollbar-width:none">
      <div class="grid grid-cols-3 gap-1.5">
        {#each monthDays as day}
          {@const photo = photosByDate[day]}
          {@const isFuture = day > TODAY}
          <button title={photo ? (photo.caption || day) : day}
            on:click={() => { if (photo) selectedPhoto = photo; }}
            class="aspect-square w-full rounded-md overflow-hidden {isFuture ? 'th-bg opacity-40' : photo ? 'opacity-100' : 'th-surface opacity-60'}"
            style={photo ? `background-image:url(${photo.url});background-size:cover;background-position:center` : ''}
          />
        {/each}
      </div>
      {#if monthCount > 0}
        <p class="text-xs th-muted mt-2">{monthCount} / {monthDays.length} days this month</p>
      {/if}
    </div>
  {:else}
    <!-- Full year grid -->
    <div class="grid grid-cols-6 gap-3">
      {#each yearByMonth as mDays, mi}
        <div>
          <div class="text-[9px] th-muted mb-1">{MONTH_NAMES[mi]}</div>
          <div class="grid grid-cols-7 gap-0.5">
            {#each mDays as day}
              {@const photo = photosByDate[day]}
              {@const isFuture = day > TODAY}
              <button title={photo ? (photo.caption || day) : day}
                on:click={() => { if (photo) selectedPhoto = photo; }}
                class="w-3 h-3 rounded-sm overflow-hidden {isFuture ? 'opacity-20' : photo ? 'opacity-100' : 'th-surface opacity-60'}"
                style={photo ? `background-image:url(${photo.url});background-size:cover;background-position:center` : ''}
              />
            {/each}
          </div>
        </div>
      {/each}
    </div>
    {#if photoCount > 0}
      <p class="text-xs th-muted mt-2">{photoCount} / {yearDays.length} days</p>
    {/if}
  {/if}
</div>

{#if selectedPhoto}
  <div class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8"
    on:click={() => selectedPhoto=null}>
    <div class="th-surface rounded-2xl overflow-hidden max-w-lg w-full shadow-2xl" on:click|stopPropagation>
      <img src={selectedPhoto.url} alt={selectedPhoto.caption||selectedPhoto.date} class="w-full max-h-96 object-cover" />
      <div class="px-5 py-4 flex items-start justify-between gap-4">
        <div>
          <div class="text-sm th-muted">
            {new Date(selectedPhoto.date+'T12:00:00').toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'})}
          </div>
          {#if selectedPhoto.caption}<p class="text-sm th-text mt-1">{selectedPhoto.caption}</p>{/if}
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <button on:click={async()=>{await fetch(`/api/events/${selectedPhoto.id}`,{method:'DELETE'});selectedPhoto=null;photos=await(await fetch('/api/photos')).json();}}
            class="text-xs text-[#c87a7a] hover:text-[#e87a7a]">Delete</button>
          <button on:click={() => selectedPhoto=null} class="th-muted hover:text-[#e8e0d0]">✕</button>
        </div>
      </div>
    </div>
  </div>
{/if}
