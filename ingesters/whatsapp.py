import re
from datetime import datetime
from pathlib import Path

# iOS:     [27/05/25, 3:45:02 PM] Alice: hey
# Android: 27/05/25, 15:45 - Alice: hey
_IOS     = re.compile(r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2}:\d{2}\s*[AP]M)\]\s+([^:]+):\s(.*)')
_ANDROID = re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s+(\d{1,2}:\d{2})\s*[–\-]\s+([^:]+):\s(.*)')

def _parse_ts_ios(date_str, time_str):
    for fmt in ('%d/%m/%y', '%d/%m/%Y', '%m/%d/%y', '%m/%d/%Y'):
        try:
            return datetime.strptime(f'{date_str} {time_str.strip()}', f'{fmt} %I:%M:%S %p')
        except ValueError:
            continue
    return None

def _parse_ts_android(date_str, time_str):
    for fmt in ('%d/%m/%y', '%d/%m/%Y', '%m/%d/%y', '%m/%d/%Y'):
        try:
            return datetime.strptime(f'{date_str} {time_str}', f'{fmt} %H:%M')
        except ValueError:
            continue
    return None

def parse(filepath: str, chat_name: str) -> list[dict]:
    messages = []
    current = None

    for raw in Path(filepath).read_text(encoding='utf-8', errors='replace').splitlines():
        line = raw.lstrip('\u200e\u200f\u202a\u202c')
        m = _IOS.match(line)
        if m:
            if current:
                messages.append(current)
            ts = _parse_ts_ios(m.group(1), m.group(2))
            current = {'timestamp': ts, 'sender': m.group(3).strip(), 'message': m.group(4), 'chat_name': chat_name}
            continue

        m = _ANDROID.match(line)
        if m:
            if current:
                messages.append(current)
            ts = _parse_ts_android(m.group(1), m.group(2))
            current = {'timestamp': ts, 'sender': m.group(3).strip(), 'message': m.group(4), 'chat_name': chat_name}
            continue

        if current:
            current['message'] += '\n' + line

    if current:
        messages.append(current)

    return [msg for msg in messages if msg['timestamp'] is not None]
