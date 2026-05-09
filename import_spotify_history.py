import json
import zipfile
from datetime import datetime, timezone
from storage.db import get_connection

ZIP = "/Users/janav/Downloads/my_spotify_data.zip"
MIN_MS = 30_000  # skip plays under 30 seconds

files = [f"Spotify Account Data/StreamingHistory_music_{i}.json" for i in range(6)]

total = 0
with zipfile.ZipFile(ZIP) as zf:
    with get_connection() as conn:
        for fname in files:
            data = json.loads(zf.read(fname))
            for entry in data:
                if entry["msPlayed"] < MIN_MS:
                    continue
                ts = datetime.strptime(entry["endTime"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                cur = conn.execute(
                    "INSERT OR IGNORE INTO events (timestamp, source, event_type, metadata) VALUES (?,?,?,?)",
                    (ts.isoformat(), "spotify", "play", json.dumps({
                        "track_name": entry["trackName"],
                        "artist": entry["artistName"],
                        "ms_played": entry["msPlayed"],
                    }))
                )
                total += cur.rowcount
            print(f"{fname}: done")

print(f"Total inserted: {total}")
