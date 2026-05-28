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

function mergeState(raw) {
  return {
    ...DEFAULT_STATE,
    ...raw,
    custom: { ...DEFAULT_STATE.custom, ...raw?.custom },
  };
}

function loadLocal() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return DEFAULT_STATE;
    return mergeState(JSON.parse(raw));
  } catch {
    return DEFAULT_STATE;
  }
}

function persist(state) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    const safe = { ...state, custom: { ...state.custom, bgMedia: null, bgMediaType: null } };
    localStorage.setItem(KEY, JSON.stringify(safe));
  }
}

async function fetchFromServer() {
  try {
    const res = await fetch('/api/theme');
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

function saveToServer(state) {
  fetch('/api/theme', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state),
  }).catch(() => {});
}

function createThemeStore() {
  const initial = loadLocal();
  applyColors(initial.preset === 'custom' ? initial.custom : (PRESETS[initial.preset] || PRESETS.warm));

  const { subscribe, update, set } = writable(initial);

  // Pull authoritative state from server — applies once page has loaded
  fetchFromServer().then(serverRaw => {
    if (!serverRaw || !serverRaw.preset) return;
    const serverState = mergeState(serverRaw);
    persist(serverState);
    set(serverState);
    applyColors(serverState.preset === 'custom' ? serverState.custom : (PRESETS[serverState.preset] || PRESETS.warm));
  });

  return {
    subscribe,
    setPreset(name) {
      update(s => {
        const next = { ...s, preset: name };
        applyColors(PRESETS[name]);
        persist(next);
        saveToServer(next);
        return next;
      });
    },
    updateCustom(patch) {
      update(s => {
        const custom = { ...s.custom, ...patch };
        const next = { preset: 'custom', custom };
        applyColors(custom);
        persist(next);
        saveToServer(next);
        return next;
      });
    },
  };
}

export const themeStore = createThemeStore();
