import { writable } from 'svelte/store';

const KEY = 'trellis_theme';

export const PRESETS = {
  warm:  { bg: '#1a1714', surface: '#242019', textPrimary: '#e8e0d0', textSecondary: '#9a9080', accent: '#c8813a' },
  cool:  { bg: '#141a1e', surface: '#1c2530', textPrimary: '#dce8f0', textSecondary: '#7a9aaa', accent: '#5b8cc8' },
  slate: { bg: '#12141a', surface: '#1c1e2c', textPrimary: '#dde0f0', textSecondary: '#7080a0', accent: '#8b6bb0' },
  light: { bg: '#f0ece4', surface: '#ffffff',  textPrimary: '#2a2520', textSecondary: '#7a7060', accent: '#c8813a' },
};

const DEFAULT_STATE = {
  preset: 'warm',
  custom: {
    bg: '#1a1714',
    surface: '#242019',
    textPrimary: '#e8e0d0',
    textSecondary: '#9a9080',
    accent: '#c8813a',
    bgMedia: null,
    bgMediaType: null,
  },
};

function applyColors(c) {
  const r = document.documentElement;
  r.style.setProperty('--bg', c.bg);
  r.style.setProperty('--surface', c.surface);
  r.style.setProperty('--text-primary', c.textPrimary);
  r.style.setProperty('--text-secondary', c.textSecondary);
  r.style.setProperty('--accent', c.accent);
  document.body.style.backgroundColor = c.bg;
}

function loadState() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return DEFAULT_STATE;
    const parsed = JSON.parse(raw);
    return {
      ...DEFAULT_STATE,
      ...parsed,
      custom: { ...DEFAULT_STATE.custom, ...parsed.custom },
    };
  } catch {
    return DEFAULT_STATE;
  }
}

function persist(state) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    // Large data URL may overflow localStorage — save without bgMedia
    const safe = { ...state, custom: { ...state.custom, bgMedia: null, bgMediaType: null } };
    localStorage.setItem(KEY, JSON.stringify(safe));
  }
}

function createThemeStore() {
  const initial = loadState();
  applyColors(initial.preset === 'custom' ? initial.custom : (PRESETS[initial.preset] || PRESETS.warm));

  const { subscribe, update } = writable(initial);

  return {
    subscribe,
    setPreset(name) {
      update(s => {
        const next = { ...s, preset: name };
        applyColors(PRESETS[name]);
        persist(next);
        return next;
      });
    },
    updateCustom(patch) {
      update(s => {
        const custom = { ...s.custom, ...patch };
        const next = { preset: 'custom', custom };
        applyColors(custom);
        persist(next);
        return next;
      });
    },
  };
}

export const themeStore = createThemeStore();
