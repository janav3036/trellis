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

def _compute_tone(msgs: list[dict], sender: str) -> list[str]:
    own = [m for m in msgs if m['sender'] == sender]
    if not own:
        return []
    

    n = len(own)
    avg_words   = sum(len(m['message'].split()) for m in own) / n
    excl_ratio  = sum('!' in m['message'] for m in own) / n
    q_ratio     = sum('?' in m['message'] for m in own) / n
    emoji_ratio = sum(bool(_EMOJI_RE.search(m['message'])) for m in own) / n
    night_ratio = sum(m['timestamp'].hour >= 23 or m['timestamp'].hour <= 3 for m in own) / n
    caps_ratio  = sum(
        sum(1 for w in m['message'].split() if w.isupper() and len(w) > 1)
        for m in own
    ) / max(sum(len(m['message'].split()) for m in own), 1)

    tags = []
    if avg_words < 5:     tags.append('brief')
    elif avg_words > 14:  tags.append('verbose')
    if excl_ratio > 0.15: tags.append('expressive')
    if q_ratio > 0.12:    tags.append('inquisitive')
    if emoji_ratio > 0.2: tags.append('emoji-heavy')
    if night_ratio > 0.2: tags.append('night owl')
    if caps_ratio > 0.05: tags.append('yells sometimes')
    if not tags:          tags.append('measured')

    return tags[:3]


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
    tone = {sender: _compute_tone(msgs, sender) for sender in senders}


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
        'tone':         tone,
        'date_from':    msgs[0]['timestamp'].strftime('%b %d, %Y'),
        'date_to':      msgs[-1]['timestamp'].strftime('%b %d, %Y'),
    }

def _fmt_seconds(s: float) -> str:
    s = int(s)
    if s < 60:   return f'{s}s'
    if s < 3600: return f'{s//60}m'
    return f'{s//3600}h {(s%3600)//60}m'

# 10 distinct earthy/muted colors — cycles for groups > 10
_PALETTE = [
    '#a07850', '#6b8c6b', '#7080a8', '#a87060', '#6b8c88',
    '#9a7888', '#8a9860', '#7868a0', '#c4944a', '#5a8878',
]

def _donut_svg(counts: dict, senders: list, colors: list[str]) -> str:
    total = sum(counts.values()) or 1
    r, cx, cy = 52, 75, 75
    C = 2 * 3.14159265 * r
    cumulative = 0.0
    segs = []
    for sender, color in zip(senders, colors):
        f = counts.get(sender, 0) / total
        dash = f * C
        segs.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="18" '
            f'stroke-dasharray="{dash:.2f} {C:.2f}" '
            f'stroke-dashoffset="{-(cumulative * C):.2f}" '
            f'transform="rotate(-90 {cx} {cy})" stroke-linecap="butt"/>'
        )
        cumulative += f
    legend_rows = ''.join(
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:7px">'
        f'<span style="width:9px;height:9px;border-radius:50%;background:{c};flex-shrink:0"></span>'
        f'<span style="font-size:12px;color:#5a4a38;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{s}</span>'
        f'<span style="font-size:12px;color:#1a1410;font-family:\'Courier New\',monospace;margin-left:12px">'
        f'{counts.get(s, 0):,}</span>'
        f'</div>'
        for s, c in zip(senders, colors)
    )
    return (
        f'<div style="display:flex;align-items:center;gap:28px;flex-wrap:wrap">'
        f'<svg viewBox="0 0 150 150" xmlns="http://www.w3.org/2000/svg" width="150" height="150" style="flex-shrink:0">'
        + ''.join(segs) +
        f'<text x="{cx}" y="{cy-7}" text-anchor="middle" font-size="10" fill="#8a7a68" font-family="Georgia,serif">total</text>'
        f'<text x="{cx}" y="{cy+12}" text-anchor="middle" font-size="19" font-weight="700" '
        f'fill="#1a1410" font-family="\'Courier New\',monospace">{sum(counts.values()):,}</text>'
        f'</svg>'
        f'<div style="flex:1;min-width:180px">{legend_rows}</div>'
        f'</div>'
    )

def _bar_chart_svg(labels: list, series: dict, colors: list[str], width=700, height=180) -> str:
    n = len(labels)
    if n == 0:
        return ''
    left, bottom = 8, 28
    chart_w = width - left
    chart_h = height - bottom
    bar_w = max(2, chart_w // n - 2)
    max_val = max((sum(series[s][i] for s in series) for i in range(n)), default=1)
    senders = list(series.keys())
    grids = ''.join(
        f'<line x1="{left}" y1="{height - bottom - int(p * chart_h)}" x2="{width}" '
        f'y2="{height - bottom - int(p * chart_h)}" stroke="#ddd5c8" stroke-width="0.5"/>'
        for p in (0.25, 0.5, 0.75, 1.0)
    )
    rects = []
    overlays = []
    for i, label in enumerate(labels):
        x = left + i * (chart_w // n)
        stack_y = height - bottom
        for color, sender in zip(colors, senders):
            val = series[sender][i]
            if val == 0:
                continue
            bh = max(1, int((val / max_val) * chart_h))
            stack_y -= bh
            rects.append(f'<rect x="{x}" y="{stack_y}" width="{bar_w}" height="{bh}" fill="{color}" opacity="0.88"/>')
        total_i = sum(series[s][i] for s in senders)
        breakdown = '|'.join(f'{s}:{series[s][i]}' for s in senders if series[s][i] > 0)
        overlays.append(
            f'<rect x="{x}" y="0" width="{max(bar_w + 4, (chart_w // n))}" height="{height - bottom}"'
            f' fill="transparent" class="bar-hover"'
            f' data-month="{label}" data-total="{total_i}" data-vals="{breakdown}"/>'
        )
    year_labs = ''
    prev_year = ''
    for i, label in enumerate(labels):
        year = label[:4]
        if year != prev_year:
            x = left + i * (chart_w // n)
            year_labs += f'<text x="{x}" y="{height - 8}" font-size="9" fill="#8a7a68" font-family="Georgia,serif">{year}</text>'
            prev_year = year
    baseline = height - bottom
    return (
        f'<svg id="bar-chart" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:{height}px;overflow:visible">'
        + grids + ''.join(rects) + year_labs
        + f'<line x1="{left}" y1="{baseline}" x2="{width}" y2="{baseline}" stroke="#b8a898" stroke-width="1"/>'
        + ''.join(overlays)
        + '</svg>'
    )

def _hour_heatmap_svg(by_hour: dict, senders: list, colors: list[str], width=700, height=72) -> str:
    cell_w = (width - 32) // 24
    max_val = max((sum(by_hour.get(h, {}).get(s, 0) for s in senders) for h in range(24)), default=1)
    cells = ''
    for h in range(24):
        total = sum(by_hour.get(h, {}).get(s, 0) for s in senders)
        intensity = (total / max_val) ** 0.55
        alpha = 0.07 + 0.88 * intensity
        x = 32 + h * cell_w
        cells += f'<rect x="{x}" y="8" width="{cell_w - 2}" height="36" fill="#8b5e3c" opacity="{alpha:.2f}" rx="3"/>'
        if h in (0, 6, 12, 18, 23):
            label = {0: '12a', 6: '6a', 12: '12p', 18: '6p', 23: '11p'}[h]
            cells += f'<text x="{x + 1}" y="{height - 4}" font-size="8" fill="#8a7a68" font-family="\'Courier New\',monospace">{label}</text>'
    return (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:{height}px">'
        + cells + '</svg>'
    )

def generate_report(stats: dict) -> str:
    if not stats:
        return '<html><body>No data</body></html>'

    senders = stats['senders']
    colors  = [_PALETTE[i % len(_PALETTE)] for i in range(len(senders))]
    months  = stats['months']

    series   = {s: [stats['by_month'].get(mo, {}).get(s, 0) for mo in months] for s in senders}
    donut    = _donut_svg(stats['counts'], senders, colors)
    bar_svg  = _bar_chart_svg(months, series, colors)
    hour_svg = _hour_heatmap_svg(stats['by_hour'], senders, colors)

    chain      = stats['best_chain']
    chain_date = chain['start'].strftime('%b %d, %Y') if chain.get('start') else '—'

    def person_row(sender, color):
        count     = stats['counts'].get(sender, 0)
        pct       = round(100 * count / stats['total'])
        avg_r     = stats['avg_response'].get(sender, 0)
        emojis    = ' '.join(e for e, _ in stats['top_emojis'].get(sender, []))
        tone_tags = stats.get('tone', {}).get(sender, [])
        words     = ''.join(
            f'<span style="display:inline-block;background:#ede6da;color:#5a4a38;'
            f'padding:2px 9px;border-radius:10px;font-size:11px;margin:2px 3px 2px 0">{w}</span>'
            for w, _ in stats['top_words'].get(sender, [])
        )
        tone_html = (
            f'<div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:10px">'
            + ''.join(
                f'<span style="font-size:10px;font-family:\'Courier New\',monospace;'
                f'color:{color};border:1px solid {color};opacity:0.7;'
                f'padding:1px 8px;border-radius:10px;letter-spacing:0.5px">{t}</span>'
                for t in tone_tags
            )
            + '</div>'
        ) if tone_tags else ''
        return (
            f'<div style="border-left:3px solid {color};padding:16px 0 16px 20px;margin-bottom:24px">'
            f'<div style="display:flex;align-items:baseline;gap:10px;margin-bottom:6px;flex-wrap:wrap">'
            f'<span style="font-size:16px;font-weight:700;color:#1a1410;font-family:Georgia,serif">{sender}</span>'
            f'<span style="font-size:24px;font-weight:700;color:#1a1410;font-family:\'Courier New\',monospace">{count:,}</span>'
            f'<span style="font-size:11px;color:#8a7a68">{pct}% · avg reply {_fmt_seconds(avg_r)}</span>'
            f'</div>'
            + tone_html
            + f'<div style="height:4px;background:#e8e0d4;border-radius:2px;margin-bottom:10px;max-width:440px">'
            f'<div style="height:4px;width:{max(2,pct)}%;background:{color};border-radius:2px;opacity:0.75"></div>'
            f'</div>'
            + (f'<div style="font-size:22px;margin-bottom:8px;line-height:1.4">{emojis}</div>' if emojis else '')
            + f'<div style="line-height:2">{words}</div>'
            f'</div>'
        )

    people_html = ''.join(person_row(s, c) for s, c in zip(senders, colors))

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{stats["chat_name"]}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:#f5f0e8;color:#2a2218;font-family:-apple-system,'Helvetica Neue',sans-serif;min-height:100vh}}
  .hero{{background:#1a1410;padding:52px 40px 44px}}
  .hero-eye{{font-size:9px;letter-spacing:3.5px;text-transform:uppercase;color:#8b5e3c;font-family:'Courier New',monospace;margin-bottom:12px}}
  .hero-title{{font-size:38px;font-family:Georgia,'Times New Roman',serif;font-style:italic;color:#f0e8d8;margin-bottom:14px;line-height:1.15}}
  .hero-meta{{font-size:11px;color:#6a5a4a;font-family:'Courier New',monospace;display:flex;gap:14px;flex-wrap:wrap;align-items:center}}
  .hero-meta em{{color:#c4a882;font-style:normal}}
  .body{{max-width:760px;margin:0 auto;padding:44px 32px 80px}}
  .chips{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:40px}}
  .chip{{background:#ede6da;border-radius:8px;padding:14px 18px;flex:1;min-width:110px}}
  .chip-v{{font-size:26px;font-weight:700;font-family:'Courier New',monospace;color:#1a1410;line-height:1;margin-bottom:4px}}
  .chip-l{{font-size:9px;text-transform:uppercase;letter-spacing:2px;color:#8a7a68}}
  .sec{{margin-bottom:40px}}
  .sec-lbl{{font-size:9px;letter-spacing:3px;text-transform:uppercase;color:#8a7a68;font-family:'Courier New',monospace;border-bottom:1px solid #ddd5c8;padding-bottom:8px;margin-bottom:20px}}
  .callout{{background:#1a1410;color:#c4a882;border-radius:8px;padding:14px 20px;font-size:12px;font-family:'Courier New',monospace}}
  .callout strong{{color:#f0e8d8}}
  #bar-tip{{position:fixed;pointer-events:none;background:#1a1410;color:#f0e8d8;border-radius:7px;padding:9px 13px;font-size:11px;font-family:'Courier New',monospace;box-shadow:0 4px 16px rgba(0,0,0,0.35);display:none;z-index:99;min-width:120px;line-height:1.7}}
  #bar-tip .tip-month{{font-size:10px;color:#8a7a68;margin-bottom:3px}}
  #bar-tip .tip-row{{display:flex;align-items:center;gap:7px}}
  #bar-tip .tip-dot{{width:7px;height:7px;border-radius:50%;flex-shrink:0}}
  .bar-hover{{cursor:crosshair}}
  @media(max-width:600px){{.hero{{padding:36px 24px 32px}}.hero-title{{font-size:28px}}.body{{padding:32px 20px 60px}}}}
</style>
</head>
<body>
<div id="bar-tip"></div>
<div class="hero">
  <div class="hero-eye">Conversation Archive</div>
  <div class="hero-title">{stats["chat_name"]}</div>
  <div class="hero-meta">
    <em>{stats["date_from"]}</em>
    <span>→</span>
    <em>{stats["date_to"]}</em>
    <span style="color:#3a2a1a">·</span>
    <span>{len(senders)} participants · {len(months)} months</span>
  </div>
</div>
<div class="body">
  <div class="chips">
    <div class="chip"><div class="chip-v">{stats["total"]:,}</div><div class="chip-l">Messages</div></div>
    <div class="chip"><div class="chip-v">{len(senders)}</div><div class="chip-l">Participants</div></div>
    <div class="chip"><div class="chip-v">{len(months)}</div><div class="chip-l">Months</div></div>
    <div class="chip"><div class="chip-v">{chain["length"]}</div><div class="chip-l">Longest chain</div></div>
  </div>
  <div class="sec">
    <div class="sec-lbl">Who talks more</div>
    {donut}
  </div>
  <div class="sec">
    <div class="sec-lbl">Messages over time</div>
    {bar_svg}
  </div>
  <div class="sec">
    <div class="sec-lbl">Active hours</div>
    {hour_svg}
  </div>
  <div class="sec">
    <div class="sec-lbl">By person</div>
    {people_html}
  </div>
  <div class="callout">
    Longest unbroken chain — <strong>{chain["length"]} messages</strong> by <strong>{chain["sender"]}</strong> · {chain_date}
  </div>
</div>
<script>
(function(){{
  var tip = document.getElementById('bar-tip');
  var colors = {json.dumps(dict(zip(senders, colors)))};
  document.querySelectorAll('.bar-hover').forEach(function(r){{
    r.addEventListener('mouseenter', function(e){{
      var month = r.dataset.month;
      var total = r.dataset.total;
      var vals = r.dataset.vals ? r.dataset.vals.split('|') : [];
      var rows = vals.map(function(v){{
        var parts = v.split(':');
        var name = parts[0], count = parts[1];
        var c = colors[name] || '#8a7a68';
        return '<div class="tip-row"><span class="tip-dot" style="background:'+c+'"></span><span>'+name+'</span><span style="margin-left:auto;padding-left:12px">'+parseInt(count).toLocaleString()+'</span></div>';
      }}).join('');
      tip.innerHTML = '<div class="tip-month">'+month+'</div>'+rows+'<div style="border-top:1px solid #3a3020;margin-top:5px;padding-top:5px;color:#c4a882">'+parseInt(total).toLocaleString()+' total</div>';
      tip.style.display = 'block';
    }});
    r.addEventListener('mousemove', function(e){{
      var x = e.clientX + 14, y = e.clientY - 10;
      if (x + 160 > window.innerWidth) x = e.clientX - 160;
      tip.style.left = x + 'px';
      tip.style.top = y + 'px';
    }});
    r.addEventListener('mouseleave', function(){{ tip.style.display = 'none'; }});
  }});
}})();
</script>
</body>
</html>'''
