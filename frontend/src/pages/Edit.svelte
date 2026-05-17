<script>
  import { onDestroy } from 'svelte';
  import { themeStore, PRESETS } from '../lib/themeStore.js';

  let state = { preset: 'warm', custom: { bg: '#1a1714', surface: '#242019', textPrimary: '#e8e0d0', textSecondary: '#9a9080', accent: '#c8813a', bgMedia: null, bgMediaType: null } };
  const unsub = themeStore.subscribe(v => { state = v; });
  onDestroy(unsub);

  const PRESET_LABELS = { warm: 'Warm Dark', cool: 'Cool Dark', slate: 'Slate', light: 'Light' };

  let urlInput = '';

  function applyPreset(name) {
    themeStore.setPreset(name);
    urlInput = '';
  }

  function selectCustom() {
    if (state.preset !== 'custom') {
      // Seed custom colours from the current preset so pickers start sensibly
      const seed = PRESETS[state.preset] || PRESETS.warm;
      themeStore.updateCustom({ ...seed });
    }
  }

  function handleFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = ev => themeStore.updateCustom({ bgMedia: ev.target.result, bgMediaType: 'image' });
    reader.readAsDataURL(file);
    e.target.value = '';
  }

  function handleUrl() {
    const url = urlInput.trim();
    if (!url) return;
    const videoExts = ['.mp4', '.webm', '.mov', '.m4v', '.ogg'];
    const lower = url.split('?')[0].toLowerCase();
    const type = videoExts.some(ext => lower.endsWith(ext)) ? 'video' : 'image';
    themeStore.updateCustom({ bgMedia: url, bgMediaType: type });
  }

  function clearMedia() {
    urlInput = '';
    themeStore.updateCustom({ bgMedia: null, bgMediaType: null });
  }

  const COLOR_FIELDS = [
    { key: 'bg',            label: 'Background' },
    { key: 'surface',       label: 'Card'        },
    { key: 'textPrimary',   label: 'Text'        },
    { key: 'textSecondary', label: 'Muted Text'  },
    { key: 'accent',        label: 'Accent'      },
  ];
</script>

<main class="min-h-screen p-8" style="background-color: var(--bg); color: var(--text-primary)">
  <div class="flex items-center gap-4 mb-8">
    <a href="/#/" class="text-xs transition-colors"
       style="color: var(--text-secondary)"
       on:mouseenter={e => e.target.style.color = 'var(--text-primary)'}
       on:mouseleave={e => e.target.style.color = 'var(--text-secondary)'}>
      ← Home
    </a>
    <h1 class="text-2xl font-semibold">Appearance</h1>
  </div>

  <div class="max-w-lg flex flex-col gap-8">

    <!-- ── Preset themes ── -->
    <div>
      <h2 class="text-xs font-semibold uppercase tracking-wider mb-3" style="color: var(--text-secondary)">Theme</h2>
      <div class="grid grid-cols-2 gap-2">

        {#each Object.entries(PRESET_LABELS) as [key, label]}
          {@const colors = PRESETS[key]}
          <button on:click={() => applyPreset(key)}
            class="flex items-center gap-3 p-3 rounded-xl border transition-all text-left"
            style="
              background-color: {colors.surface};
              border-color: {state.preset === key ? 'var(--text-primary)' : 'rgba(255,255,255,0.08)'};
              color: {colors.textPrimary};
            ">
            <div class="flex gap-1.5 shrink-0">
              <div class="w-3 h-3 rounded-full" style="background:{colors.bg}" />
              <div class="w-3 h-3 rounded-full" style="background:{colors.surface}" />
              <div class="w-3 h-3 rounded-full" style="background:{colors.accent}" />
            </div>
            <span class="text-sm">{label}</span>
          </button>
        {/each}

        <!-- Custom option -->
        <button on:click={selectCustom}
          class="flex items-center gap-3 p-3 rounded-xl border transition-all text-left"
          style="
            border-color: {state.preset === 'custom' ? 'var(--text-primary)' : 'rgba(255,255,255,0.08)'};
          ">
          <div class="w-3 h-3 rounded-full shrink-0"
               style="background: linear-gradient(135deg, #c8813a, #5b8cc8)" />
          <span class="text-sm">Custom</span>
        </button>

      </div>
    </div>

    <!-- ── Custom settings (only when custom is active) ── -->
    {#if state.preset === 'custom'}

      <!-- Background media -->
      <div>
        <h2 class="text-xs font-semibold uppercase tracking-wider mb-3" style="color: var(--text-secondary)">Background</h2>

        <div class="flex gap-2 mb-2">
          <input type="text" bind:value={urlInput}
                 placeholder="Paste image or video URL…"
                 class="flex-1 rounded-lg px-3 py-2 text-sm border"
                 style="background: var(--surface); color: var(--text-primary); border-color: rgba(255,255,255,0.08)" />
          <button on:click={handleUrl}
                  class="px-3 py-2 rounded-lg text-sm transition-colors"
                  style="background: var(--surface); color: var(--text-primary)">
            Set
          </button>
        </div>

        <div class="flex items-center gap-3 mb-3">
          <label class="text-xs underline cursor-pointer transition-colors"
                 style="color: var(--text-secondary)">
            Upload image
            <input type="file" accept="image/*" class="hidden" on:change={handleFile} />
          </label>
          {#if state.custom.bgMedia}
            <button on:click={clearMedia}
                    class="text-xs" style="color: #c87a7a">
              Clear
            </button>
          {/if}
        </div>

        {#if state.custom.bgMedia}
          <div class="rounded-xl overflow-hidden mb-2 h-32">
            {#if state.custom.bgMediaType === 'video'}
              <video src={state.custom.bgMedia} autoplay loop muted playsinline
                     class="w-full h-full object-cover" />
            {:else}
              <img src={state.custom.bgMedia} alt="background preview"
                   class="w-full h-full object-cover" />
            {/if}
          </div>
        {/if}
      </div>

      <!-- Colour pickers -->
      <div>
        <h2 class="text-xs font-semibold uppercase tracking-wider mb-3" style="color: var(--text-secondary)">Colours</h2>
        <div class="flex flex-col gap-3">
          {#each COLOR_FIELDS as { key, label }}
            <div class="flex items-center gap-3">
              <input type="color"
                     value={state.custom[key]}
                     on:input={e => themeStore.updateCustom({ [key]: e.target.value })}
                     class="w-8 h-8 rounded cursor-pointer border-0 bg-transparent p-0" />
              <span class="text-sm flex-1">{label}</span>
              <span class="text-xs font-mono" style="color: var(--text-secondary)">{state.custom[key]}</span>
            </div>
          {/each}
        </div>
      </div>

    {/if}

  </div>
</main>
