import json 
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from storage.db import get_connection

_EMOJI_RE = re.compile(
    "[\U00010000-\U0010ffff"
    "\U0001F300-\U0001F9FF"
    "\u2600-\u27BF]+",
    flags=re.UNICODE,
)
_STOP = {
    'the','a','an','and','or','but','in','on','at','to','for','of','with',
    'is','it','i','you','he','she','we','they','this','that','was','are',
    'be','been','have','has','had','do','did','will','would','could','should',
    'not','so','if','me','my','your','his','her','our','their','up','out',
    'ok','okay','haha','lol','yeah','yes','no','oh','ah','hmm','like','just',
    'got','get','go','going','im','its','thats','dont','cant','https','http',
    'media','omitted','null','message','deleted',

    # hinglish
    'hai','hain','haan','nahi','nhi','kya','toh','toh','bhi','aur','kar',
    'tha','thi','the','woh','yeh','ye','koi','kuch','mein','mujhe','tumhe',
    'isko','usko','unko','ek','do','teen','bas','agar','matlab','yaar',
    'bhai','bro','areh','arre','chal','abhi','phir','fir','sab','kab',
    'kaise','kyun','kyunki','lekin','par','pe','se','ko','ne','hi','na',
    'accha','acha','theek','thik','haha','hahaha','lmao','lmk','wtf','omg',

}

def _load_messages(chat_name: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT timestamp, sender, message FROM whatsapp_messages WHERE chat_name = ? ORDER BY timestamp",
            (chat_name,)
        ).fetchall()
        return [{'timestamp': datetime.fromisoformat(r['timestamp']), 'sender': r['sender'], 'message': r['message']} for r in rows]

def compute_stats(chat_name: str) -> dict:
    msgs = _load_messages(chat_name)
    if not msgs:
        return {}
    
    senders = sorted({m['sender'] for m in msgs})
    total = len(msgs)

    #counter
    counts = Counter(m['sender'] for m in msgs)

    #messages per month
    by_month = defaultdict(lambda: Counter())
    for m in msgs:
        key = m['timestamp'].strftime('%Y-%m')
        by_month[key][m['sender']] += 1 
    months = sorted(by_month.keys())

    # active hours heatmap  (hour 0-23 → {sender: count})
    by_hour = defaultdict(lambda: Counter())
    for m in msgs:
        by_hour[m['timestamp'].hour][m['sender']] += 1

    # response times (seconds) - only when sender changes
    response_times = defaultdict(list)

    for i in range(1, len(msgs)):
        prev, curr = msgs[i-1], msgs[i]
        if prev['sender'] != curr['sender']:
            delta = (curr['timestamp'] - prev['timestamp']).total_seconds()
            if 0 < delta < 86400:
                response_times[curr['sender']].append(delta)

    avg_response = {}
    for sender, times in response_times.items():
        avg_response[sender] = sum(times) / len(times) if times else 0

    #top emojis per sender
    top_emojis = {}
    for sender in senders:
        all_emojis = []
        for m in msgs:
            if m['sender'] == sender:
                all_emojis.extend(_EMOJI_RE.findall(m['message']))
        top_emojis[sender] = Counter(all_emojis).most_common(8)

    # top words per sender (excluding stop words + short tokens)
    top_words = {}
    for sender in senders:
        words = []
        for m in msgs:
            if m['sender'] == sender:
                tokens = re.findall(r"[a-zA-Z']{3,}", m['message'].lower())
                words.extend(t for t in tokens if t not in _STOP)
        top_words[sender] = Counter(words).most_common(12)

    # longest chain (consecutive messages by same sender)
    best_chain = {'sender': '', 'length': 0, 'start': None}
    chain_sender, chain_len, chain_start = msgs[0]['sender'], 1, msgs[0]['timestamp']
    for m in msgs[1:]:
        if m['sender'] == chain_sender:
            chain_len += 1
        else:
            if chain_len > best_chain['length']:
                best_chain = {'sender': chain_sender, 'length': chain_len, 'start': chain_start}
            chain_sender, chain_len, chain_start = m['sender'], 1, m['timestamp']
    if chain_len > best_chain['length']:
        best_chain = {'sender': chain_sender, 'length': chain_len, 'start': chain_start}

    return {
        'chat_name':    chat_name,
        'total':        total,
        'senders':      senders,
        'counts':       dict(counts),
        'months':       months,
        'by_month':     {k: dict(v) for k, v in by_month.items()},
        'by_hour':      {k: dict(v) for k, v in by_hour.items()},
        'avg_response': avg_response,
        'top_emojis':   top_emojis,
        'top_words':    top_words,
        'best_chain':   best_chain,
        'date_from':    msgs[0]['timestamp'].strftime('%b %d, %Y'),
        'date_to':      msgs[-1]['timestamp'].strftime('%b %d, %Y'),
    }

def _fmt_seconds(s: float) -> str:
    s = int(s)
    if s < 60:   return f'{s}s'
    if s < 3600: return f'{s//60}m'
    return f'{s//3600}h {(s%3600)//60}m'

def _bar_chart_svg(labels: list, series: dict[str, list], colors: list[str], width=600, height=160) -> str:
    n = len(labels)
    if n == 0:
        return ''
    bar_w = max(2, (width - 40) // n - 2)
    max_val = max((sum(series[s][i] for s in series) for i in range(n)), default=1)
    rects = []
    for i, label in enumerate(labels):
        x = 40 + i * ((width - 40) // n)
        stack_y = height - 20
        for color, sender in zip(colors, series):
            val = series[sender][i]
            if val == 0:
                continue
            bh = max(1, int((val / max_val) * (height - 30)))
            stack_y -= bh
            rects.append(f'<rect x="{x}" y="{stack_y}" width="{bar_w}" height="{bh}" fill="{color}" opacity="0.85"/>')
    year_labels = ''
    prev_year = ''
    for i, label in enumerate(labels):
        year = label[:4]
        if year != prev_year:
            x = 40 + i * ((width - 40) // n)
            year_labels += f'<text x="{x}" y="{height-4}" font-size="9" fill="#8a7a6a">{year}</text>'
            prev_year = year
    return (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:{height}px">'
        + ''.join(rects) + year_labels
        + f'<line x1="40" y1="{height-20}" x2="{width}" y2="{height-20}" stroke="#4a4030" stroke-width="1"/>'
        + '</svg>'
    )

def _hour_heatmap_svg(by_hour: dict, senders: list, colors: list[str], width=600, height=60) -> str:
    cell = (width - 40) // 24
    max_val = max((sum(by_hour.get(h, {}).get(s, 0) for s in senders) for h in range(24)), default=1)
    cells = ''
    for h in range(24):
        total = sum(by_hour.get(h, {}).get(s, 0) for s in senders)
        intensity = total / max_val
        alpha = 0.1 + 0.85 * intensity
        x = 40 + h * cell
        cells += f'<rect x="{x}" y="10" width="{cell-1}" height="30" fill="#c4a882" opacity="{alpha:.2f}" rx="2"/>'
        if h % 6 == 0:
            cells += f'<text x="{x}" y="55" font-size="9" fill="#8a7a6a">{h:02d}h</text>'
    return (
        f'<svg viewBox="0 0 {width} 60" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:60px">'
        + cells + '</svg>'
    )

def generate_report(stats: dict) -> str:
    if not stats:
        return '<html><body>No data</body></html>'

    senders = stats['senders']
    palette = ['#c4a882', '#8fa882', '#a882a8', '#82a4a8', '#a89882']
    colors  = palette[:len(senders)]
    months  = stats['months']

    series = {s: [stats['by_month'].get(mo, {}).get(s, 0) for mo in months] for s in senders}
    bar_svg  = _bar_chart_svg(months, series, colors)
    hour_svg = _hour_heatmap_svg(stats['by_hour'], senders, colors)

    legend = ''.join(
        f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:16px">'
        f'<span style="width:12px;height:12px;border-radius:50%;background:{c}"></span>'
        f'<span>{s}</span></span>'
        for s, c in zip(senders, colors)
    )

    def person_card(sender, color):
        count  = stats['counts'].get(sender, 0)
        pct    = round(100 * count / stats['total'])
        avg_r  = stats['avg_response'].get(sender, 0)
        emojis = '  '.join(e for e, _ in stats['top_emojis'].get(sender, []))
        words  = '  '.join(f'<span style="background:#2a2218;padding:2px 7px;border-radius:10px;font-size:12px">{w}</span>'
                           for w, _ in stats['top_words'].get(sender, []))
        return f'''
        <div style="background:#1e1a14;border:1px solid #3a3020;border-radius:12px;padding:20px;flex:1;min-width:220px">
          <div style="font-size:15px;font-weight:600;color:{color};margin-bottom:12px">{sender}</div>
          <div style="font-size:28px;font-weight:700;color:#e8d5b0">{count:,}</div>
          <div style="font-size:12px;color:#6a5a4a;margin-bottom:12px">{pct}% of messages · avg reply {_fmt_seconds(avg_r)}</div>
          <div style="font-size:20px;margin-bottom:10px">{emojis or "—"}</div>
          <div style="display:flex;flex-wrap:wrap;gap:4px;color:#c4a882">{words}</div>
        </div>'''

    cards = ''.join(person_card(s, c) for s, c in zip(senders, colors))

    chain = stats['best_chain']
    chain_date = chain['start'].strftime('%b %d, %Y') if chain.get('start') else '—'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{stats["chat_name"]}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #13110d; color: #c8b89a; font-family: -apple-system, sans-serif; padding: 32px 24px; max-width: 800px; margin: 0 auto; }}
  h1 {{ font-size: 28px; color: #e8d5b0; margin-bottom: 4px; }}
  .sub {{ font-size: 13px; color: #6a5a4a; margin-bottom: 32px; }}
  .section {{ margin-bottom: 32px; }}
  .section-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #6a5a4a; margin-bottom: 12px; }}
  .cards {{ display: flex; gap: 16px; flex-wrap: wrap; }}
  .stat-row {{ display:flex; gap:24px; margin-bottom:16px; }}
  .stat {{ background:#1e1a14; border:1px solid #3a3020; border-radius:10px; padding:14px 18px; flex:1; }}
  .stat-val {{ font-size:22px; font-weight:700; color:#e8d5b0; }}
  .stat-lbl {{ font-size:11px; color:#6a5a4a; margin-top:2px; }}
</style>
</head>
<body>
  <h1>{stats["chat_name"]}</h1>
  <div class="sub">{stats["date_from"]} — {stats["date_to"]} · {legend}</div>

  <div class="section">
    <div class="section-title">Overview</div>
    <div class="stat-row">
      <div class="stat"><div class="stat-val">{stats["total"]:,}</div><div class="stat-lbl">total messages</div></div>
      <div class="stat"><div class="stat-val">{len(senders)}</div><div class="stat-lbl">participants</div></div>
      <div class="stat"><div class="stat-val">{len(months)}</div><div class="stat-lbl">months active</div></div>
      <div class="stat"><div class="stat-val">{chain["length"]}</div><div class="stat-lbl">longest chain · {chain["sender"]} · {chain_date}</div></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Messages over time</div>
    {bar_svg}
  </div>

  <div class="section">
    <div class="section-title">Active hours</div>
    {hour_svg}
  </div>

  <div class="section">
    <div class="section-title">By person</div>
    <div class="cards">{cards}</div>
  </div>
</body>
</html>'''
