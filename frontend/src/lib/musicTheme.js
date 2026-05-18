import { writable } from 'svelte/store';

export const SPOTIFY_THEME = {
  bg:      '#121212',
  card:    '#181818',
  cardAlt: '#282828',
  accent:  '#1DB954',
  border:  '#2a2a2a',
  muted:   '#9a9080',
  text:    '#e8e0d0',
};

export const musicTheme = writable({ ...SPOTIFY_THEME });
