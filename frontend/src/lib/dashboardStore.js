import { writable } from 'svelte/store';

const KEY = 'trellis_dashboard';

export const DEFAULT_CONFIG = {
  music:   ['music_nowplaying'],
  code:    ['code_commits_chart'],
  weather: ['weather_today'],
  life:    ['life_calendar', 'life_movies'],
  f1:      ['f1_schedule'],
  journal: ['journal_habits'],
  market:  ['market_heartbeat', 'market_sentiment'],
  sky:     ['sky_starmap'],
};

function load() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : DEFAULT_CONFIG;
  } catch {
    return DEFAULT_CONFIG;
  }
}

function createStore() {
  const { subscribe, set } = writable(load());
  return {
    subscribe,
    save(cfg) {
      localStorage.setItem(KEY, JSON.stringify(cfg));
      set(cfg);
    },
    reset() {
      localStorage.removeItem(KEY);
      set(DEFAULT_CONFIG);
    },
  };
}

export const dashboardConfig = createStore();
