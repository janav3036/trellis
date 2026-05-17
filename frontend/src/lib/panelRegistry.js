import MusicNowPlaying  from './panels/MusicNowPlaying.svelte';
import MusicPlaysChart  from './panels/MusicPlaysChart.svelte';
import MusicPlaylists   from './panels/MusicPlaylists.svelte';
import CodeCommitsChart   from './panels/CodeCommitsChart.svelte';
import CodeRecentCommits  from './panels/CodeRecentCommits.svelte';
import CodeRepos          from './panels/CodeRepos.svelte';
import WeatherToday from './panels/WeatherToday.svelte';
import WeatherWeek  from './panels/WeatherWeek.svelte';
import Weather90d   from './panels/Weather90d.svelte';
import WeatherChart from './panels/WeatherChart.svelte';
import LifeCalendar from './panels/LifeCalendar.svelte';
import LifeGym      from './panels/LifeGym.svelte';
import LifePeople   from './panels/LifePeople.svelte';
import LifeMovies   from './panels/LifeMovies.svelte';
import F1Schedule from './panels/F1Schedule.svelte';
import F1Arc      from './panels/F1Arc.svelte';
import F1News     from './panels/F1News.svelte';
import JournalHabits from './panels/JournalHabits.svelte';
import JournalDreams from './panels/JournalDreams.svelte';
import JournalPhotos from './panels/JournalPhotos.svelte';
import JournalQuotes from './panels/JournalQuotes.svelte';
import MarketHeartbeat from './panels/MarketHeartbeat.svelte';
import MarketSentiment from './panels/MarketSentiment.svelte';
import MarketSectors   from './panels/MarketSectors.svelte';
import MarketCrypto    from './panels/MarketCrypto.svelte';
import SkyStarMap from './panels/SkyStarMap.svelte';
import SkyFlights from './panels/SkyFlights.svelte';
import SkyApod    from './panels/SkyApod.svelte';
import SkySpace   from './panels/SkySpace.svelte';

export const SECTIONS = [
  { id: 'music',   label: 'Music',   href: '/#/music' },
  { id: 'code',    label: 'Code',    href: '/#/code' },
  { id: 'weather', label: 'Weather', href: '/#/weather' },
  { id: 'life',    label: 'Life',    href: '/#/life' },
  { id: 'f1',      label: 'F1',      href: '/#/f1' },
  { id: 'journal', label: 'Journal', href: '/#/journal' },
  { id: 'market',  label: 'Markets', href: '/#/market' },
  { id: 'sky',     label: 'Sky',     href: '/#/sky' },
];

export const PANELS = {
  music_nowplaying:      { label: 'Now Playing',         section: 'music',   component: MusicNowPlaying },
  music_plays_chart:     { label: 'Plays Chart',         section: 'music',   component: MusicPlaysChart },
  music_playlists:       { label: 'Playlists',           section: 'music',   component: MusicPlaylists },

  code_commits_chart:    { label: 'Commits Chart',       section: 'code',    component: CodeCommitsChart },
  code_recent_commits:   { label: 'Recent Commits',      section: 'code',    component: CodeRecentCommits },
  code_repos:            { label: 'Repositories',        section: 'code',    component: CodeRepos },

  weather_today:         { label: "Today's Conditions",  section: 'weather', component: WeatherToday },
  weather_week:          { label: 'This Week',           section: 'weather', component: WeatherWeek },
  weather_90d:           { label: 'Last 90 Days',        section: 'weather', component: Weather90d },
  weather_chart:         { label: 'Temperature Trend',   section: 'weather', component: WeatherChart },

  life_calendar:         { label: 'Calendar',            section: 'life',    component: LifeCalendar },
  life_gym:              { label: 'Gym Sessions',        section: 'life',    component: LifeGym },
  life_people:           { label: 'People Log',          section: 'life',    component: LifePeople },
  life_movies:           { label: 'Movie Diary',         section: 'life',    component: LifeMovies },

  f1_schedule:           { label: 'Schedule & Standings', section: 'f1',     component: F1Schedule },
  f1_arc:                { label: 'Championship Arc',    section: 'f1',      component: F1Arc },
  f1_news:               { label: 'Latest News',         section: 'f1',      component: F1News },

  journal_habits:        { label: 'Habits Today',        section: 'journal', component: JournalHabits },
  journal_dreams:        { label: 'Dream Journal',       section: 'journal', component: JournalDreams },
  journal_photos:        { label: 'Photo a Day',         section: 'journal', component: JournalPhotos },
  journal_quotes:        { label: 'Quotes',              section: 'journal', component: JournalQuotes },

  market_heartbeat:      { label: 'Market Heartbeat',    section: 'market',  component: MarketHeartbeat },
  market_sentiment:      { label: 'Sentiment Orb',       section: 'market',  component: MarketSentiment },
  market_sectors:        { label: 'Sector Rotation',     section: 'market',  component: MarketSectors },
  market_crypto:         { label: 'Crypto Dominance',    section: 'market',  component: MarketCrypto },

  sky_starmap:           { label: 'Star Map',            section: 'sky',     component: SkyStarMap },
  sky_flights:           { label: 'Flight Radar',        section: 'sky',     component: SkyFlights },
  sky_apod:              { label: 'Astronomy Picture',   section: 'sky',     component: SkyApod },
  sky_space:             { label: 'Space Events',        section: 'sky',     component: SkySpace },
};

export const PANELS_BY_SECTION = {};
for (const [id, panel] of Object.entries(PANELS)) {
  if (!PANELS_BY_SECTION[panel.section]) PANELS_BY_SECTION[panel.section] = [];
  PANELS_BY_SECTION[panel.section].push({ id, ...panel });
}
