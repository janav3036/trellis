const TZ = 'Asia/Kolkata';

// YYYY-MM-DD in IST for a given timestamp (or now)
export function istDate(ts) {
  return new Date(ts ?? Date.now()).toLocaleDateString('en-CA', { timeZone: TZ });
}

// HH:MM display in IST
export function istTime(ts) {
  return new Date(ts).toLocaleTimeString('en-US', { timeZone: TZ, hour: '2-digit', minute: '2-digit' });
}

// YYYY-MM-DD in IST for today
export function todayIST() {
  return new Date().toLocaleDateString('en-CA', { timeZone: TZ });
}

// YYYY-MM-DD in IST for today minus n days
export function daysAgoIST(n = 0) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toLocaleDateString('en-CA', { timeZone: TZ });
}

// Human-readable date in IST (e.g. "May 18")
export function fmtDate(ts, opts = { month: 'short', day: 'numeric' }) {
  return new Date(ts).toLocaleDateString('en-US', { timeZone: TZ, ...opts });
}

// Build an array of IST date strings from n days ago up to today
export function buildDatesIST(n) {
  return Array.from({ length: n }, (_, i) => daysAgoIST(n - 1 - i));
}

// Group events by IST date → { 'YYYY-MM-DD': count }
export function groupByDayIST(evs) {
  const c = {};
  for (const e of evs) {
    const d = istDate(e.timestamp);
    c[d] = (c[d] || 0) + 1;
  }
  return c;
}

// Group events by the Monday of their IST week → { 'YYYY-MM-DD': count }
export function groupByWeekIST(evs) {
  const c = {};
  for (const e of evs) {
    // Get the IST date parts
    const istStr = new Date(e.timestamp).toLocaleDateString('en-CA', { timeZone: TZ, weekday: 'short' });
    const istDateStr = istDate(e.timestamp);
    const dow = new Date(istDateStr + 'T12:00:00').getDay(); // 0=Sun
    const mon = new Date(istDateStr + 'T12:00:00');
    mon.setDate(mon.getDate() - dow);
    const w = mon.toLocaleDateString('en-CA');
    c[w] = (c[w] || 0) + 1;
  }
  return c;
}
