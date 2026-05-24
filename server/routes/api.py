import json
import os
import hashlib
import mimetypes
import re
import cloudinary
import cloudinary.uploader
from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, redirect, request, Response, send_from_directory, session
from storage.db import get_connection
from storage.credentials import get as get_cred
import yfinance as yf
from yt_dlp import YoutubeDL
from ingesters.spotify import SpotifyIngester
from ingesters.github import GitHubIngester
from ingesters.weather import WeatherIngester
from ingesters.calendar import CalendarIngester

import requests as req

api_bp = Blueprint("api", __name__)

_AUTH_FREE = {"api.auth_login", "api.auth_check", "api.auth_change_password", "api.wallpaper_serve"}

@api_bp.before_request
def require_auth():
    if request.endpoint in _AUTH_FREE:
        return
    if not session.get("authed"):
        return jsonify({"error": "unauthorized"}), 401

@api_bp.route("/auth/check")
def auth_check():
    if session.get("authed"):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 401

@api_bp.route("/auth/login", methods=["POST"])
def auth_login():
    password = (request.json or {}).get("password", "")
    stored = get_cred("TRELLIS_PASSWORD", "trellis", "password") or ""
    if password and password == stored:
        session["authed"] = True
        return jsonify({"ok": True})
    return jsonify({"error": "incorrect password"}), 401

@api_bp.route("/auth/change-password", methods=["POST"])
def auth_change_password():
    body = request.json or {}
    old_pw = body.get("old_password", "")
    new_pw = body.get("new_password", "").strip()
    stored = get_cred("TRELLIS_PASSWORD", "trellis", "password") or ""
    if not old_pw or old_pw != stored:
        return jsonify({"error": "Current password is incorrect"}), 401
    if not new_pw:
        return jsonify({"error": "New password cannot be empty"}), 400
    try:
        import keyring
        keyring.set_password("trellis", "password", new_pw)
    except Exception:
        pass
    return jsonify({"ok": True})

cloudinary.config(
    cloud_name=get_cred("CLOUDINARY_CLOUD_NAME", "trellis", "cloudinary_cloud_name"),
    api_key=get_cred("CLOUDINARY_API_KEY",       "trellis", "cloudinary_api_key"),
    api_secret=get_cred("CLOUDINARY_API_SECRET", "trellis", "cloudinary_api_secret"),
)

def _spotify_cutoff(range_: str) -> str | None:
    now = datetime.now(timezone.utc)
    if range_ == "weekly":
        return (now - timedelta(days=7)).isoformat()
    if range_ == "monthly":
        return (now - timedelta(days=30)).isoformat()
    if range_ == "6m":
        return (now - timedelta(days=180)).isoformat()
    return None  # alltime — no filter

@api_bp.route("/events")
def get_events():
    source = request.args.get("source")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    event_type = request.args.get("event_type")

    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if source:
        query += " AND source = ?"
        params.append(source)
    if date_from:
        query += " AND timestamp >= ?"
        params.append(date_from)
    if date_to:
        query += " AND timestamp <= ?"
        params.append(date_to)
    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)

    query += " ORDER BY timestamp DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    events = [
        {**dict(row), "metadata": json.loads(row["metadata"])} for row in rows
    ]
    return jsonify(events)

@api_bp.route("/callback/spotify")
def spotify_callback():
    code = request.args.get("code")
    SpotifyIngester().exchange_code(code)
    return redirect("/")

def _full_img_url(url):
    if not url or url.startswith("http"):
        return url
    return f"https://i.scdn.co/image/{url}"

def _proxy_url(url):
    if not url:
        return None
    import urllib.parse
    return f"/api/img?url={urllib.parse.quote(url, safe='')}"

@api_bp.route("/now-playing")
def now_playing():
    try:
        ingester = SpotifyIngester()
        resp = req.get(
            "https://api.spotify.com/v1/me/player/currently-playing",
            headers=ingester._get_headers(),
            timeout=5,
        )
        if resp.status_code == 401:
            ingester._refresh_token()
            resp = req.get(
                "https://api.spotify.com/v1/me/player/currently-playing",
                headers=ingester._get_headers(),
                timeout=5,
            )
        if resp.status_code == 204 or not resp.content:
            return jsonify(None)
        data = resp.json()
        if not data.get("item"):
            return jsonify(None)
        item = data["item"]
        return jsonify({
            "track": item["name"],
            "artist": ", ".join(a["name"] for a in item["artists"]),
            "album": item["album"]["name"],
            "cover": _proxy_url(_full_img_url(item["album"]["images"][0]["url"])) if item["album"]["images"] else None,
            "progress_ms": data["progress_ms"],
            "duration_ms": item["duration_ms"],
        })
    except Exception:
        return jsonify(None)

@api_bp.route("/playlists")
def playlists():
    ingester = SpotifyIngester()
    resp = req.get(
        "https://api.spotify.com/v1/me/playlists?limit=50",
        headers=ingester._get_headers()
    )
    if resp.status_code == 401:
        ingester._refresh_token()
        resp = req.get(
            "https://api.spotify.com/v1/me/playlists?limit=50",
            headers=ingester._get_headers()
        )
    data = resp.json()
    playlist = [
        {
            "name": p["name"],
            "id": p["id"],
            "cover": _proxy_url(_full_img_url(p["images"][0]["url"])) if p["images"] else None,
            "track_count": (p.get("items") or {}).get("total", 0)
        }
        for p in data["items"]
    ]
    return jsonify(playlist)

@api_bp.route("/backfill/spotify", methods=["POST"])
def backfill_spotify():
    date_from = request.json.get("date_from")
    if not date_from:
        return jsonify({"error": "date_from required"}), 400
    count = SpotifyIngester().backfill(datetime.fromisoformat(date_from))
    return jsonify({"count": count})

@api_bp.route("/backfill/github", methods=["POST"])
def backfill_github():
    date_from = request.json.get("date_from")
    if not date_from:
        return jsonify({"error": "date_from required"}), 400
    count = GitHubIngester().backfill(datetime.fromisoformat(date_from))
    return jsonify({"count": count})

@api_bp.route("/github/repos")
def github_repos():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT json_extract(metadata, '$.repo') as repo, COUNT(*) as commits
            FROM events
            WHERE source = 'github' AND event_type = 'commit'
            GROUP BY repo
            ORDER BY commits DESC
        """).fetchall()
    return jsonify([dict(r) for r in rows])

@api_bp.route("/backfill/weather", methods=["POST"])
def backfill_weather():
    date_from = request.json.get("date_from")
    if not date_from:
        return jsonify({"error": "date_from required"}), 400
    count = WeatherIngester().backfill(datetime.fromisoformat(date_from))
    return jsonify({"count": count})

@api_bp.route("/weather/forecast")
def weather_forecast():
    ingester = WeatherIngester()
    resp = req.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": ingester.lat,
        "longitude": ingester.lon,
        "forecast_days": 14,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,windspeed_10m_max,apparent_temperature_max,apparent_temperature_min,uv_index_max,sunrise,sunset,windgusts_10m_max",
        "timezone": "auto"
    })
    resp.raise_for_status()
    daily = resp.json()["daily"]
    events = [
        {
            "timestamp": f"{day}T12:00:00",
            "metadata": {
                "temp_max": daily["temperature_2m_max"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "precipitation": daily["precipitation_sum"][i],
                "weathercode": daily["weathercode"][i],
                "windspeed_max": daily["windspeed_10m_max"][i],
                "feels_like_max": daily["apparent_temperature_max"][i],
                "feels_like_min": daily["apparent_temperature_min"][i],
                "uv_index": daily["uv_index_max"][i],
                "sunrise": daily["sunrise"][i],
                "sunset": daily["sunset"][i],
                "windgusts_max": daily["windgusts_10m_max"][i],
            }
        }
        for i, day in enumerate(daily["time"])
    ]
    return jsonify(events)

@api_bp.route("/backfill/calendar", methods=["POST"])
def backfill_calendar():
    date_from = request.json.get("date_from")
    if not date_from:
        return jsonify({"error": "date_from required"}), 400
    count = CalendarIngester().backfill(datetime.fromisoformat(date_from))
    return jsonify({"count": count})

@api_bp.route("/gym/log", methods=["POST"])
def gym_log():
    data = request.json
    date = data.get("date")
    if not date:
        return jsonify({"error": "date required"}), 400
    timestamp = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    metadata = {
        "type": data.get("type", "workout"),
        "muscle_groups": data.get("muscle_groups", []),
        "distance_km": data.get("distance_km"),
        "duration_minutes": data.get("duration_minutes"),
        "notes": data.get("notes", ""),
    }
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO events (timestamp, source, event_type, metadata) VALUES (?,?,?,?)",
            (timestamp.isoformat(), "gym", "session", json.dumps(metadata))
        )
        return jsonify({"count": cur.rowcount})

@api_bp.route("/people/log", methods=["POST"])
def people_log():
    data = request.json
    date = data.get("date")
    notes = data.get("notes", "")
    people = data.get("people", [])
    if not date or not people:
        return jsonify({"error": "date and people required"}), 400
    timestamp = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    count = 0
    with get_connection() as conn:
        for i, person in enumerate(people):
            ts = timestamp + timedelta(microseconds=i)
            cur = conn.execute(
                "INSERT OR IGNORE INTO events (timestamp, source, event_type, metadata) VALUES (?,?,?,?)",
                (ts.isoformat(), "people", "meetup", json.dumps({
                    "name": person.get("name", "").strip(),
                    "tag": person.get("tag", "Friend"),
                    "notes": notes,
                }))
            )
            count += cur.rowcount
    return jsonify({"count": count})

@api_bp.route("/people/summary")
def people_summary():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                json_extract(metadata, '$.name') as name,
                json_extract(metadata, '$.tag') as tag,
                MAX(timestamp) as last_seen,
                json_extract((SELECT metadata FROM events e2
                    WHERE e2.source='people' AND e2.event_type='meetup'
                    AND json_extract(e2.metadata,'$.name') = json_extract(e1.metadata,'$.name')
                    ORDER BY e2.timestamp DESC LIMIT 1), '$.notes') as last_notes,
                COUNT(*) as total_meetups
            FROM events e1
            WHERE source='people' AND event_type='meetup'
              AND json_extract(metadata, '$.name') != ''
            GROUP BY json_extract(metadata, '$.name')
            ORDER BY last_seen DESC
        """).fetchall()
    return jsonify([dict(r) for r in rows])

_ALLOWED_IMG_CDNS = (
    "https://i.scdn.co/",
    "https://mosaic.scdn.co/",
    "https://image-cdn-ak.spotifycdn.com/",
    "https://image-cdn-fa.spotifycdn.com/",
    "https://image.tmdb.org/",
)

@api_bp.route("/img")
def proxy_image():
    url = request.args.get("url", "")
    if not any(url.startswith(p) for p in _ALLOWED_IMG_CDNS):
        return "", 400
    resp = req.get(url, timeout=5)
    return Response(resp.content, content_type=resp.headers.get("Content-Type", "image/jpeg"))

@api_bp.route("/movies/search")
def movies_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    api_key = get_cred("TMDB_API_KEY", "trellis-tmdb", "api_key")
    resp = req.get("https://api.themoviedb.org/3/search/movie", params={
        "api_key": api_key,
        "query": query,
    })
    resp.raise_for_status()
    results = resp.json().get("results", [])[:8]
    return jsonify([
        {
            "tmdb_id": r["id"],
            "title": r["title"],
            "year": r.get("release_date", "")[:4],
            "poster_path": r.get("poster_path"),
            "genre_ids": r.get("genre_ids", []),
            "overview": r.get("overview", ""),
        }
        for r in results
    ])

@api_bp.route("/movies/log", methods=["POST"])
def movies_log():
    data = request.json
    date = data.get("date")
    title = data.get("title", "").strip()
    if not date or not title:
        return jsonify({"error": "date and title required"}), 400
    now = datetime.now(timezone.utc)
    timestamp = datetime.fromisoformat(date).replace(
        tzinfo=timezone.utc,
        hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond
    )
    metadata = {
        "title": title,
        "tmdb_id": data.get("tmdb_id"),
        "year": data.get("year"),
        "poster_path": data.get("poster_path"),
        "genres": data.get("genres", []),
        "rating": data.get("rating"),
        "notes": data.get("notes", ""),
        "overview": data.get("overview", ""),
    }
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO events (timestamp, source, event_type, metadata) VALUES (?,?,?,?)",
            (timestamp.isoformat(), "movies", "watch", json.dumps(metadata))
        )
    return jsonify({"count": cur.rowcount})

@api_bp.route("/movies/watchlist", methods=["POST"])
def movies_watchlist_add():
    data = request.json
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
    now = datetime.now(timezone.utc)
    metadata = {
        "tmdb_id":    data.get("tmdb_id"),
        "title":      title,
        "year":       data.get("year"),
        "poster_path": data.get("poster_path"),
    }
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO events (timestamp, source, event_type, metadata) VALUES (?,?,?,?)",
            (now.isoformat(), "movies", "watchlist", json.dumps(metadata))
        )
    return jsonify({"id": cur.lastrowid})

@api_bp.route("/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    return jsonify({"deleted": cur.rowcount})

@api_bp.route("/events/<int:event_id>", methods=["PATCH"])
def update_event(event_id):
    new_meta = (request.json or {}).get("metadata", {})
    with get_connection() as conn:
        row = conn.execute("SELECT metadata FROM events WHERE id = ?", (event_id,)).fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        existing = json.loads(row[0])
        existing.update(new_meta)
        conn.execute("UPDATE events SET metadata = ? WHERE id = ?", (json.dumps(existing), event_id))
    return jsonify({"updated": 1})

@api_bp.route("/f1/schedule")
def f1_schedule():
    resp = req.get("https://api.jolpi.ca/ergast/f1/current.json", timeout=10)
    resp.raise_for_status()
    data = resp.json()["MRData"]["RaceTable"]
    season = data["season"]
    today = datetime.now(timezone.utc).date().isoformat()
    return jsonify({
        "season": season,
        "races": [
            {
                "round": int(r["round"]),
                "name": r["raceName"],
                "circuit": r["Circuit"]["circuitName"],
                "country": r["Circuit"]["Location"]["country"],
                "date": r["date"],
                "completed": r["date"] < today
            }
            for r in data["Races"]
        ]
    })

@api_bp.route("/f1/standings")
def f1_standings():
    d_resp = req.get("https://api.jolpi.ca/ergast/f1/current/driverStandings.json", timeout=10)
    d_resp.raise_for_status()
    c_resp = req.get("https://api.jolpi.ca/ergast/f1/current/constructorStandings.json", timeout=10)
    c_resp.raise_for_status()

    d_list = d_resp.json()["MRData"]["StandingsTable"]["StandingsLists"]
    c_list = c_resp.json()["MRData"]["StandingsTable"]["StandingsLists"]

    drivers = [
        {
            "position": int(s["position"]),
            "driver": f"{s['Driver']['givenName']} {s['Driver']['familyName']}",
            "team": s["Constructors"][0]["name"] if s["Constructors"] else "",
            "points": float(s["points"]),
            "wins": int(s["wins"]),
        }
        for s in (d_list[0]["DriverStandings"] if d_list else [])
    ]

    constructors = [
        {
            "position": int(s["position"]),
            "team": s["Constructor"]["name"],
            "points": float(s["points"]),
            "wins": int(s["wins"]),
        }
        for s in (c_list[0]["ConstructorStandings"] if c_list else [])
    ]

    return jsonify({"drivers": drivers, "constructors": constructors})

@api_bp.route("/f1/season-arc")
def f1_season_arc():
    resp = req.get("https://api.jolpi.ca/ergast/f1/current/results.json?limit=1000", timeout=15)
    resp.raise_for_status()
    races = resp.json()["MRData"]["RaceTable"]["Races"]

    race_names = []
    driver_points = {}

    for race in races:
        race_names.append(race["raceName"].replace(" Grand Prix", " GP"))
        for result in race.get("Results", []):
            name = f"{result['Driver']['givenName']} {result['Driver']['familyName']}"
            pts = float(result["points"])
            prev = driver_points.get(name, [])
            prev_total = prev[-1] if prev else 0
            while len(prev) < len(race_names) - 1:
                prev.append(prev[-1] if prev else 0)
            prev.append(prev_total + pts)
            driver_points[name] = prev

    final = {d: pts[-1] for d, pts in driver_points.items()}
    top5 = sorted(final, key=final.get, reverse=True)[:5]

    return jsonify({
        "races": race_names,
        "drivers": {d: driver_points[d] for d in top5}
    })

@api_bp.route("/f1/news")
def f1_news():
    import feedparser
    feeds = [
        ("https://www.autosport.com/rss/f1/news/", "Autosport"),
        ("https://www.racefans.net/feed/", "RaceFans"),
    ]
    items = []
    for url, source in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                pub = entry.get("published_parsed")
                items.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": f"{pub.tm_year}-{pub.tm_mon:02d}-{pub.tm_mday:02d}" if pub else "",
                    "source": source,
                })
        except Exception:
            continue
    return jsonify(items[:15])

@api_bp.route("/f1/race-results/<int:round>")
def f1_race_results(round):
    resp = req.get(
        f"https://api.jolpi.ca/ergast/f1/current/{round}/results.json",
        timeout=10
    )
    resp.raise_for_status()
    races = resp.json()["MRData"]["RaceTable"]["Races"]
    if not races:
        return jsonify(None)
    race = races[0]
    return jsonify({
        "name": race["raceName"],
        "date": race["date"],
        "circuit": race["Circuit"]["circuitName"],
        "results": [
            {
                "position": int(r["position"]),
                "driver": f"{r['Driver']['givenName']} {r['Driver']['familyName']}",
                "team": r["Constructor"]["name"],
                "points": float(r["points"]),
                "status": r["status"],
                "fastest_lap": r.get("FastestLap", {}).get("rank") == "1",
            }
            for r in race.get("Results", [])
        ]
    })

@api_bp.route("/f1/photos/upload", methods=["POST"])
def f1_photos_upload():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    result = cloudinary.uploader.upload(
        request.files["file"],
        folder="trellis/f1-photos",
    )
    return jsonify({"url": result["secure_url"]})

@api_bp.route("/f1/photos/log", methods=["POST"])
def f1_photos_log():
    data = request.json
    round_num = data.get("round")
    url = data.get("url", "").strip()
    if not round_num or not url:
        return jsonify({"error": "round and url required"}), 400
    metadata = {
        "round": int(round_num),
        "race_name": data.get("race_name", ""),
        "url": url,
        "caption": data.get("caption", ""),
    }
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO events (timestamp, source, event_type, metadata) VALUES (?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), "f1-photos", "race-photo", json.dumps(metadata))
        )
    return jsonify({"ok": True})

@api_bp.route("/f1/photos")
def f1_photos_list():
    round_filter = request.args.get("round")
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, metadata FROM events WHERE source='f1-photos' AND event_type='race-photo' ORDER BY timestamp DESC"
        ).fetchall()
    photos = [{"id": r[0], "timestamp": r[1], **json.loads(r[2])} for r in rows]
    if round_filter:
        photos = [p for p in photos if str(p.get("round")) == str(round_filter)]
    return jsonify(photos)

@api_bp.route("/f1/photos/<int:photo_id>", methods=["DELETE"])
def f1_photos_delete(photo_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM events WHERE id=? AND source='f1-photos'", (photo_id,))
    return jsonify({"ok": True})

@api_bp.route("/market/heartbeat")
def market_heartbeat():
    tickers = {
        "S&P 500": "^GSPC",
        "Nikkei": "^N225",
        "DAX": "^GDAXI",
        "FTSE": "^FTSE",
    }

    result = {}
    for name, symbol in tickers.items():
        hist = yf.Ticker(symbol).history(period="30d", interval="1d")
        closes = hist["Close"].tolist()
        dates = [d.strftime("%Y-%m-%d") for d in hist.index]
        if closes:
            base = closes[0]
            result[name] = {
                "pct": [(c - base) / base * 100 for c in closes],
                "dates": dates,
            }
    return jsonify(result)

@api_bp.route("/market/fear-greed")
def market_fear_greed():
    hist = yf.Ticker("^VIX").history(period="5d", interval="1d")
    vix = hist["Close"].iloc[-1]
    score = max(0, min(100, 100 - (vix - 10) / 30 * 100))
    return jsonify({"vix": round(vix, 2), "score": round(score, 1)})

@api_bp.route("/market/sector-rotation")
def market_sector_rotation():
    sectors = {
        "Tech": "XLK", "Energy": "XLE", "Health": "XLV",
        "Finance": "XLF", "Industrial": "XLI", "Comms": "XLC",
        "Consumer Disc": "XLY", "Consumer Stap": "XLP",
        "Utilities": "XLU", "Real Estate": "XLRE", "Materials": "XLB",
    }
    result = {}

    for name, symbol in sectors.items():
        data = yf.download(symbol, period="30d", interval="1d", progress=False, auto_adjust=True)
        closes = data["Close"].squeeze().tolist()
        if len(closes) >= 2:
            result[name] = round((closes[-1] - closes[0]) / closes[0] * 100, 2)
    return jsonify(result)

@api_bp.route("/market/crypto")
def market_crypto():
    resp = req.get("https://api.coingecko.com/api/v3/global", timeout=10)
    if resp.status_code == 429:
        return jsonify({"btc": 0, "eth": 0, "other": 0, "error": "rate_limited"}), 200
    resp.raise_for_status()
    data = resp.json()["data"]
    dominance = data["market_cap_percentage"]
    return jsonify({
        "btc": round(dominance.get("btc", 0), 1),
        "eth": round(dominance.get("eth", 0), 1),
        "other": round(100 - dominance.get("btc", 0) - dominance.get("eth", 0), 1),
    })

_BRIGHT_STARS = [
    # (name, RA_hours, Dec_deg, Vmag, spectral_letter)
    ("Sirius",          6.7525, -16.7161, -1.46, "A"),
    ("Canopus",         6.3992, -52.6957, -0.72, "A"),
    ("Rigil Kentaurus", 14.660, -60.8333, -0.27, "G"),
    ("Arcturus",        14.2612, 19.1822, -0.04, "K"),
    ("Vega",            18.6157, 38.7836,  0.03, "A"),
    ("Capella",          5.2788, 45.9980,  0.08, "G"),
    ("Rigel",            5.2422, -8.2017,  0.12, "B"),
    ("Procyon",          7.6552,  5.2250,  0.38, "F"),
    ("Achernar",         1.6286,-57.2368,  0.46, "B"),
    ("Betelgeuse",       5.9195,  7.4070,  0.50, "M"),
    ("Hadar",           14.0637,-60.3730,  0.61, "B"),
    ("Acrux",           12.4433,-63.0990,  0.76, "B"),
    ("Altair",          19.8464,  8.8683,  0.77, "A"),
    ("Aldebaran",        4.5987, 16.5093,  0.85, "K"),
    ("Antares",         16.4901,-26.4320,  0.96, "M"),
    ("Spica",           13.4199,-11.1613,  0.97, "B"),
    ("Pollux",           7.7553, 28.0261,  1.14, "K"),
    ("Fomalhaut",       22.9608,-29.6224,  1.16, "A"),
    ("Deneb",           20.6905, 45.2803,  1.25, "A"),
    ("Mimosa",          12.7952,-59.6885,  1.25, "B"),
    ("Regulus",         10.1395, 11.9672,  1.35, "B"),
    ("Adhara",           6.9771,-28.9720,  1.50, "B"),
    ("Castor",           7.5767, 31.8883,  1.57, "A"),
    ("Gacrux",          12.5194,-57.1133,  1.59, "M"),
    ("Shaula",          17.5601,-37.1033,  1.62, "B"),
    ("Bellatrix",        5.4186,  6.3497,  1.64, "B"),
    ("Elnath",           5.4381, 28.6074,  1.65, "B"),
    ("Alnilam",          5.6036, -1.2019,  1.69, "B"),
    ("AlNair",          22.1373,-46.9608,  1.73, "B"),
    ("Alnitak",          5.6793, -1.9426,  1.74, "O"),
    ("Alioth",          12.9005, 55.9598,  1.76, "A"),
    ("Kaus Australis",  18.4029,-34.3846,  1.79, "B"),
    ("Mirfak",           3.4053, 49.8612,  1.79, "F"),
    ("Dubhe",           11.0621, 61.7511,  1.79, "K"),
    ("Alkaid",          13.7923, 49.3133,  1.85, "B"),
    ("Avior",            8.3750,-59.5097,  1.86, "K"),
    ("Menkalinan",       5.9922, 44.9474,  1.90, "A"),
    ("Atria",           16.8115,-69.0277,  1.91, "K"),
    ("Alhena",           6.6283, 16.3993,  1.93, "A"),
    ("Peacock",         20.4273,-56.7350,  1.94, "B"),
    ("Mirzam",           6.3785,-17.9559,  1.98, "B"),
    ("Alphard",          9.4598, -8.6586,  1.98, "K"),
    ("Polaris",          2.5304, 89.2641,  1.97, "F"),
    ("Hamal",            2.1196, 23.4624,  2.00, "K"),
    ("Algieba",         10.3328, 19.8417,  2.01, "K"),
    ("Diphda",           0.7264,-17.9866,  2.02, "K"),
    ("Nunki",           18.9211,-26.2965,  2.02, "B"),
    ("Mizar",           13.3988, 54.9254,  2.04, "A"),
    ("Mirach",           1.1620, 35.6204,  2.06, "M"),
    ("Kochab",          14.8451, 74.1556,  2.08, "K"),
    ("Rasalhague",      17.5823, 12.5600,  2.08, "A"),
    ("Saiph",            5.7956, -9.6696,  2.09, "B"),
    ("Algol",            3.1361, 40.9554,  2.09, "B"),
    ("Denebola",        11.8175, 14.5720,  2.14, "A"),
    ("Gamma Cyg",       20.3706, 40.2567,  2.20, "F"),
    ("Alphecca",        15.5784, 26.7148,  2.22, "A"),
    ("Mintaka",          5.5334, -0.2991,  2.23, "O"),
    ("Schedar",          0.6751, 56.5373,  2.24, "K"),
    ("Caph",             0.1528, 59.1500,  2.27, "F"),
    ("Dschubba",        16.0053,-22.6217,  2.29, "B"),
    ("Epsilon Sco",     16.8357,-34.2930,  2.29, "K"),
    ("Izar",            14.7497, 27.0742,  2.35, "K"),
    ("Merak",           11.0307, 56.3824,  2.37, "A"),
    ("Sabik",           17.1726,-15.7248,  2.43, "A"),
    ("Phecda",          11.8976, 53.6948,  2.44, "A"),
    ("Gamma Cas",        0.9451, 60.7167,  2.47, "B"),
    ("Epsilon Cyg",     20.7702, 33.9703,  2.48, "K"),
    ("Zosma",           11.2350, 20.5236,  2.56, "A"),
    ("Ruchbah",          1.4304, 60.2353,  2.68, "A"),
    ("Tau Sco",         16.5987,-28.2160,  2.82, "B"),
    ("Delta Cru",       12.2519,-58.7490,  2.79, "B"),
    ("Delta Cyg",       20.7281, 45.1303,  2.87, "A"),
    ("Albireo",         19.5121, 27.9597,  3.08, "K"),
    ("Megrez",          12.2568, 57.0326,  3.31, "A"),
    ("Segin",            1.9064, 63.6700,  3.35, "B"),
    ("Meissa",           5.5882,  9.9340,  3.39, "O"),
]

_CONSTELLATION_LINES = [
    # Orion
    ["Betelgeuse", "Bellatrix"], ["Betelgeuse", "Alnilam"],
    ["Bellatrix", "Mintaka"], ["Mintaka", "Alnilam"], ["Alnilam", "Alnitak"],
    ["Alnitak", "Saiph"], ["Mintaka", "Rigel"], ["Rigel", "Saiph"],
    ["Betelgeuse", "Meissa"], ["Bellatrix", "Meissa"],
    # Ursa Major (Big Dipper)
    ["Dubhe", "Merak"], ["Merak", "Phecda"], ["Phecda", "Megrez"],
    ["Megrez", "Dubhe"], ["Megrez", "Alioth"], ["Alioth", "Mizar"], ["Mizar", "Alkaid"],
    # Cassiopeia
    ["Caph", "Schedar"], ["Schedar", "Gamma Cas"], ["Gamma Cas", "Ruchbah"], ["Ruchbah", "Segin"],
    # Scorpius
    ["Dschubba", "Antares"], ["Antares", "Tau Sco"], ["Tau Sco", "Epsilon Sco"], ["Epsilon Sco", "Shaula"],
    # Crux
    ["Acrux", "Gacrux"], ["Mimosa", "Delta Cru"],
    # Cygnus (Northern Cross)
    ["Deneb", "Gamma Cyg"], ["Gamma Cyg", "Albireo"],
    ["Gamma Cyg", "Delta Cyg"], ["Gamma Cyg", "Epsilon Cyg"],
    # Leo
    ["Regulus", "Algieba"], ["Algieba", "Zosma"], ["Zosma", "Denebola"],
    # Ursa Minor
    ["Polaris", "Kochab"],
    # Boötes
    ["Arcturus", "Izar"],
]


@api_bp.route("/sky/stars")
def sky_stars():
    lat = float(get_cred("WEATHER_LAT", "trellis-weather", "lat") or 40.0)
    lon = float(get_cred("WEATHER_LON", "trellis-weather", "lon") or -74.0)
    stars = [
        {"name": s[0], "ra": s[1], "dec": s[2], "mag": s[3], "spec": s[4]}
        for s in _BRIGHT_STARS
    ]
    return jsonify({"lat": lat, "lon": lon, "stars": stars, "constellations": _CONSTELLATION_LINES})


_apod_cache = {"date": None, "data": None}

@api_bp.route("/sky/apod")
def sky_apod():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if _apod_cache["date"] == today and _apod_cache["data"] is not None:
        return jsonify(_apod_cache["data"])
    api_key = get_cred("NASA_API_KEY", "trellis-nasa", "api_key") or "DEMO_KEY"
    try:
        resp = req.get("https://api.nasa.gov/planetary/apod", params={"api_key": api_key}, timeout=10)
        resp.raise_for_status()
    except Exception:
        if _apod_cache["data"] is not None:
            return jsonify(_apod_cache["data"])
        return jsonify(None)
    data = resp.json()
    result = {
        "date": data["date"],
        "title": data["title"],
        "explanation": data["explanation"],
        "url": data["url"] if data["media_type"] == "image" else None,
        "hdurl": data.get("hdurl") if data["media_type"] == "image" else None,
        "media_type": data["media_type"],
    }
    _apod_cache["date"] = today
    _apod_cache["data"] = result
    return jsonify(result)

@api_bp.route("/sky/flights")
def sky_flights():
    lat = float(get_cred("WEATHER_LAT", "trellis-weather", "lat") or 40.0)
    lon = float(get_cred("WEATHER_LON", "trellis-weather", "lon") or -74.0)
    delta = 8
    try:
        resp = req.get(
            "https://opensky-network.org/api/states/all",
            params={
                "lamin": lat - delta, "lamax": lat + delta,
                "lomin": lon - delta, "lomax": lon + delta,
            },
            timeout=15,
        )
        resp.raise_for_status()
        states = resp.json().get("states") or []
    except Exception:
        states = []
    planes = []
    for s in states:
        if s[5] is None or s[6] is None:
            continue
        planes.append({
            "callsign": (s[1] or "").strip(),
            "lon": s[5], "lat": s[6],
            "altitude": s[7] or 0,
            "heading": s[10] or 0,
            "on_ground": bool(s[8]),
        })
    return jsonify({"planes": planes, "center_lat": lat, "center_lon": lon})


@api_bp.route("/sky/iss")
def sky_iss():
    resp = req.get("https://api.wheretheiss.at/v1/satellites/25544", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return jsonify({
        "lat": round(data["latitude"], 4),
        "lon": round(data["longitude"], 4),
        "altitude_km": round(data["altitude"], 1),
        "velocity_kmh": round(data["velocity"], 1),
        "visibility": data.get("visibility", "")
    })

@api_bp.route("/sky/neo")
def sky_neo():
    api_key = get_cred("NASA_API_KEY", "trellis-nasa", "api_key") or "DEMO_KEY"
    today = datetime.now(timezone.utc).date()
    end = today + timedelta(days=7)
    try:
        resp = req.get(
            "https://api.nasa.gov/neo/rest/v1/feed",
            params={
                "start_date": today.isoformat(),
                "end_date": end.isoformat(),
                "api_key": api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return jsonify([])
    neos = []
    for day_neos in data.get("near_earth_objects", {}).values():
        for neo in day_neos:
            close = neo.get("close_approach_data", [{}])[0]
            neos.append({
                "name": neo["name"].strip("()"),
                "date": close.get("close_approach_date", ""),
                "miss_km": round(float(close.get("miss_distance", {}).get("kilometers", 0))),
                "diameter_m": round(float(neo.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_max", 0))),
                "hazardous": neo.get("is_potentially_hazardous_asteroid", False),
            })
    neos.sort(key=lambda x: x["date"])
    return jsonify(neos[:8])


@api_bp.route("/dreams/log", methods=["POST"])
def dreams_log():
    data = request.json
    date = data.get("date")
    title = data.get("title", "").strip()
    if not date or not title:
        return jsonify({"error": "date and title required"}), 400
    now = datetime.now(timezone.utc)
    timestamp = datetime.fromisoformat(date).replace(
        tzinfo=timezone.utc,
        hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond
    )
    metadata = {
        "title": title,
        "description": data.get("description", ""),
        "mood": data.get("mood", ""),
        "tags": data.get("tags", []),
        "lucid": data.get("lucid", False),
    }
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO events (timestamp, source, event_type, metadata) VALUES (?,?,?,?)",
            (timestamp.isoformat(), "dreams", "dream", json.dumps(metadata))
        )
    return jsonify({"count": cur.rowcount})

@api_bp.route("/dreams")
def dreams_list():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, metadata FROM events WHERE source='dreams' ORDER BY timestamp DESC"
        ).fetchall()
    return jsonify([
        {"id": r[0], "timestamp": r[1], **json.loads(r[2])}
        for r in rows
    ])

@api_bp.route("/photos/log", methods=["POST"])
def photos_log():
    data = request.json
    date = data.get("date")
    url = data.get("url", "").strip()
    if not date or not url:
        return jsonify({"error": "date and url required"}), 400
    timestamp = f"{date}T00:00:00+00:00"
    metadata = {
        "url": url,
        "caption": data.get("caption", ""),
    }
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT OR REPLACE INTO events (timestamp, source, event_type, metadata) VALUES (?,?,?,?)",
            (timestamp, "photos", "daily", json.dumps(metadata))
        )
    return jsonify({"count": cur.rowcount})

@api_bp.route("/photos")
def photos_list():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, metadata FROM events WHERE source='photos' ORDER BY timestamp DESC"
        ).fetchall()
    return jsonify([
        {"id": r[0], "date": r[1][:10], **json.loads(r[2])}
        for r in rows
    ])

@api_bp.route("/photos/upload", methods=["POST"])
def photos_upload():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    result = cloudinary.uploader.upload(
        request.files["file"],
        folder="trellis/photos",
    )
    return jsonify({"url": result["secure_url"]})

@api_bp.route("/letters/log", methods=["POST"])
def letters_log():
    data = request.json
    body = data.get("body", "").strip()
    unlock_date = data.get("unlock_date")
    if not body or not unlock_date:
        return jsonify({"error": "body and unlock_date required"}), 400
    now = datetime.now(timezone.utc)
    metadata = {
        "body": body,
        "unlock_date": unlock_date,
    }
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO events (timestamp, source, event_type, metadata) VALUES (?,?,?,?)",
            (now.isoformat(), "letters", "future", json.dumps(metadata))
        )
    return jsonify({"ok": True})

@api_bp.route("/letters")
def letters_list():
    today = datetime.now(timezone.utc).date().isoformat()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, metadata FROM events WHERE source='letters' ORDER BY timestamp DESC"
        ).fetchall()
    result = []
    for r in rows:
        meta = json.loads(r[2])
        unlocked = meta["unlock_date"] <= today
        result.append({
            "id": r[0],
            "timestamp": r[1],
            "unlock_date": meta["unlock_date"],
            "unlocked": unlocked,
            "body": meta["body"] if unlocked else None,
        })
    return jsonify(result)

@api_bp.route("/cron/check-letters")
def cron_check_letters():
    import smtplib
    from email.mime.text import MIMEText
    secret = os.environ.get("CRON_SECRET", "")
    if request.headers.get("Authorization") != f"Bearer {secret}":
        return jsonify({"error": "unauthorized"}), 401
    today = datetime.now(timezone.utc).date().isoformat()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT metadata FROM events WHERE source='letters' AND event_type='future'"
        ).fetchall()
    to_send = [
        json.loads(r[0]) for r in rows
        if json.loads(r[0]).get("unlock_date") == today
    ]
    if not to_send:
        return jsonify({"sent": 0})
    gmail_user = get_cred("GMAIL_USER", "trellis", "gmail_user") or "janavdshah30@gmail.com"
    password = get_cred("GMAIL_APP_PASSWORD", "trellis", "gmail_app_password")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(gmail_user, password)
        for letter in to_send:
            msg = MIMEText(letter["body"], "plain")
            msg["Subject"] = f"A letter from your past self — {today}"
            msg["From"] = gmail_user
            msg["To"] = gmail_user
            smtp.send_message(msg)
    return jsonify({"sent": len(to_send)})

@api_bp.route("/cron/ingest/<job>", methods=["POST"])
def cron_ingest(job):
    secret = os.environ.get("CRON_SECRET", "")
    if request.headers.get("Authorization") != f"Bearer {secret}":
        return jsonify({"error": "unauthorized"}), 401
    from scheduler import JOBS
    if job not in JOBS:
        return jsonify({"error": "unknown job"}), 404
    try:
        JOBS[job]()
        return jsonify({"ok": True, "job": job})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/quotes/log", methods=["POST"])
def quotes_log():
    data = request.json
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "text required"}), 400
    now = datetime.now(timezone.utc)
    metadata = {
        "text": text,
        "author": data.get("author", "").strip(),
        "source_title": data.get("source_title", "").strip(),
        "tags": data.get("tags", []),
    }
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO events (timestamp, source, event_type, metadata) VALUES (?,?,?,?)",
            (now.isoformat(), "quotes", "quote", json.dumps(metadata))
        )
    return jsonify({"ok": True})

@api_bp.route("/quotes")
def quotes_list():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, metadata FROM events WHERE source='quotes' ORDER BY timestamp DESC"
        ).fetchall()
    return jsonify([
        {"id": r[0], "timestamp": r[1], **json.loads(r[2])}
        for r in rows
    ])

@api_bp.route("/memories")
def memories():
    IST = timezone(timedelta(hours=5, minutes=30))
    today = datetime.now(IST).date()

    windows = [
        ("week",    "A week ago",    7),
        ("month",   "A month ago",   30),
        ("3months", "3 months ago",  90),
        ("6months", "6 months ago",  180),
        ("year",    "A year ago",    365),
    ]

    result = []
    with get_connection() as conn:
        for key, label, days in windows:
            target = (today - timedelta(days=days)).isoformat()
            rows = conn.execute(
                """SELECT id, timestamp, source, metadata
                   FROM events
                   WHERE source IN ('dreams', 'photos')
                     AND date(timestamp) = ?
                   ORDER BY timestamp""",
                (target,)
            ).fetchall()
            if rows:
                entries = [
                    {"id": r[0], "timestamp": r[1], "source": r[2], **json.loads(r[3])}
                    for r in rows
                ]
                result.append({"key": key, "label": label, "date": target, "entries": entries})

    return jsonify(result)


@api_bp.route("/habits")
def habits_list():
    today = datetime.now(timezone.utc).date().isoformat()
    with get_connection() as conn:
        habits = conn.execute("SELECT id, name, color FROM habits ORDER BY created_at").fetchall()
        checkins_today = conn.execute(
            "SELECT json_extract(metadata, '$.habit_id') as habit_id FROM events "
            "WHERE source='habits' AND event_type='checkin' AND timestamp LIKE ?",
            (f"{today}%",)
        ).fetchall()
    checked_ids = {int(r[0]) for r in checkins_today if r[0]}
    return jsonify([
        {"id": h[0], "name": h[1], "color": h[2], "done_today": h[0] in checked_ids}
        for h in habits
    ])

@api_bp.route("/habits", methods=["POST"])
def habits_create():
    data = request.json
    name = data.get("name", "").strip()
    color = data.get("color", "#6b9e6b")
    if not name:
        return jsonify({"error": "name required"}), 400
    with get_connection() as conn:
        conn.execute("INSERT INTO habits (name, color) VALUES (?, ?)", (name, color))
    return jsonify({"ok": True})

@api_bp.route("/habits/<int:habit_id>", methods=["DELETE"])
def habits_delete(habit_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
    return jsonify({"ok": True})

@api_bp.route("/habits/<int:habit_id>/checkin", methods=["POST"])
def habits_checkin(habit_id):
    today = datetime.now(timezone.utc).date().isoformat()
    with get_connection() as conn:
        habit = conn.execute("SELECT name FROM habits WHERE id = ?", (habit_id,)).fetchone()
        if not habit:
            return jsonify({"error": "not found"}), 404
        existing = conn.execute(
            "SELECT id FROM events WHERE source='habits' AND event_type='checkin' "
            "AND timestamp LIKE ? AND json_extract(metadata, '$.habit_id') = ?",
            (f"{today}%", habit_id)
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM events WHERE id = ?", (existing[0],))
            return jsonify({"done": False})
        now = datetime.now(timezone.utc)
        conn.execute(
            "INSERT INTO events (timestamp, source, event_type, metadata) VALUES (?,?,?,?)",
            (now.isoformat(), "habits", "checkin", json.dumps({"habit_id": habit_id, "habit_name": habit[0]}))
        )
    return jsonify({"done": True})

@api_bp.route("/spotify/top-tracks")
def spotify_top_tracks():
    range_ = request.args.get("range", "monthly")
    cutoff = _spotify_cutoff(range_)
    query = """
        SELECT json_extract(metadata, '$.track_name') as track,
               json_extract(metadata, '$.artist') as artist,
               COUNT(*) as plays
        FROM events
        WHERE source = 'spotify'
        """
    params = []
    if cutoff:
        query += " AND timestamp >= ?"
        params.append(cutoff)
    query += " GROUP BY track, artist ORDER BY plays DESC LIMIT 15"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])


@api_bp.route("/spotify/top-artists")
def spotify_top_artists():
    range_ = request.args.get("range", "monthly")
    cutoff = _spotify_cutoff(range_)
    query = """
        SELECT json_extract(metadata, '$.artist') as artist,
               COUNT(*) as plays
        FROM events
        WHERE source = 'spotify'
    """
    params = []
    if cutoff:
        query += " AND timestamp >= ?"
        params.append(cutoff)
    query += " GROUP BY artist ORDER BY plays DESC LIMIT 15"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])

@api_bp.route("/spotify/streak")
def spotify_streak():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT DISTINCT date(timestamp, 'localtime') as day
            FROM events
            WHERE source = 'spotify'
            ORDER BY day DESC
        """).fetchall()
    days = [r["day"] for r in rows]
    if not days:
        return jsonify({"streak": 0, "longest": 0})

    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    first = datetime.fromisoformat(days[0]).date()

    if first < yesterday:
        streak = 0
    else:
        streak = 0
        expected = first
        for day_str in days:
            d = datetime.fromisoformat(day_str).date()
            if d == expected:
                streak += 1
                expected = d - timedelta(days=1)
            else:
                break

    dates = sorted([datetime.fromisoformat(d).date() for d in days])
    longest, current = 1, 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1

    return jsonify({"streak": streak, "longest": longest})

@api_bp.route("/spotify/heatmap")
def spotify_heatmap():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                CAST(strftime('%w', timestamp, 'localtime') AS INTEGER) as dow,
                CAST(strftime('%H', timestamp, 'localtime') AS INTEGER) as hour,
                COUNT(*) as plays
            FROM events
            WHERE source = 'spotify'
            GROUP BY dow, hour
        """).fetchall()
    return jsonify([dict(r) for r in rows])

@api_bp.route("/github/languages")
def github_languages():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT DISTINCT json_extract(metadata, '$.repo') as repo
            FROM events
            WHERE source = 'github' AND event_type = 'commit'
        """).fetchall()

    gh = GitHubIngester()
    totals = {}
    for row in rows:
        repo = row["repo"]
        if not repo:
            continue
        try:
            resp = req.get(
                f"https://api.github.com/repos/{repo}/languages",
                headers=gh._headers(),
            )
            if resp.ok:
                for lang, b in resp.json().items():
                    totals[lang] = totals.get(lang, 0) + b
        except Exception:
            continue

    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    return jsonify([{"language": lang, "bytes": b} for lang, b in ranked])

@api_bp.route("/ideas", methods=["GET"])
def get_ideas():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, text, status, repo, created_at FROM ideas ORDER BY created_at DESC"
        ).fetchall()
    return jsonify([dict(r) for r in rows])

@api_bp.route("/ideas", methods=["POST"])
def create_idea():
    body = request.json or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"error": "text required"}), 400
    status = body.get("status", "active")
    repo = body.get("repo") or None
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO ideas (text, status, repo) VALUES (?, ?, ?)",
            (text, status, repo),
        )
    return jsonify({"id": cur.lastrowid}), 201

@api_bp.route("/ideas/<int:idea_id>", methods=["PATCH"])
def update_idea(idea_id):
    body = request.json or {}
    fields, values = [], []
    if "status" in body:
        fields.append("status = ?"); values.append(body["status"])
    if "repo" in body:
        fields.append("repo = ?"); values.append(body["repo"] or None)
    if "text" in body:
        fields.append("text = ?"); values.append(body["text"])
    if not fields:
        return jsonify({"error": "nothing to update"}), 400
    values.append(idea_id)
    with get_connection() as conn:
        conn.execute(f"UPDATE ideas SET {', '.join(fields)} WHERE id = ?", values)
    return jsonify({"ok": True})

@api_bp.route("/ideas/<int:idea_id>", methods=["DELETE"])
def delete_idea(idea_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
    return jsonify({"ok": True})

@api_bp.route("/proxy-wallpaper")
def proxy_wallpaper():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "missing url"}), 400
    try:
        r = req.get(url, timeout=10, stream=True)
        content_type = r.headers.get("Content-Type", "image/jpeg")
        if not content_type.startswith("image/"):
            return jsonify({"error": "not an image"}), 400
        return Response(r.content, content_type=content_type)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

def _ytdlp_video_url(url):
    opts = {"quiet": True, "no_warnings": True}
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("url")
    except Exception:
        return None

_WALLPAPER_DIR = os.path.join(
    os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), '..', 'uploads')),
    "wallpapers"
)
os.makedirs(_WALLPAPER_DIR, exist_ok=True)

_PINTEREST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.pinterest.com/",
    "Accept": "image/webp,image/avif,image/*,video/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def _extract_pinterest_media(html):
    for pattern in [
        r'property=["\']og:video:url["\'][^>]+content=["\']([^"\']+)["\']',
        r'content=["\']([^"\']+)["\'][^>]+property=["\']og:video:url["\']',
    ]:
        m = re.search(pattern, html)
        if m:
            return m.group(1).replace("&amp;", "&"), "video"

    for pattern in [
        r'property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    ]:
        m = re.search(pattern, html)
        if m:
            og_url = m.group(1).replace("&amp;", "&")
            full_res = re.sub(r'https://i\.pinimg\.com/[^/]+/', 'https://i.pinimg.com/originals/', og_url)
            return full_res, "image"

    return None, None

@api_bp.route("/wallpaper/save", methods=["POST"])
def wallpaper_save():
    url = (request.json or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "missing url"}), 400
    try:
        r = req.get(url, timeout=30, headers=_PINTEREST_HEADERS)
        r.raise_for_status()
    except Exception as e:
        return jsonify({"error": str(e)}), 502

    content_type = r.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()

    if content_type.startswith("text/html"):
        video_url = _ytdlp_video_url(url)
        if video_url:
            r = req.get(video_url, timeout=60, headers=_PINTEREST_HEADERS, stream=True)
            r.raise_for_status()
            content_type = r.headers.get("Content-Type", "video/mp4").split(";")[0].strip()
            url = video_url
        else:
            media_url, _ = _extract_pinterest_media(r.text)
            if not media_url:
                return jsonify({"error": "No media found in that Pinterest page."}), 400
            try:
                r = req.get(media_url, timeout=30, headers=_PINTEREST_HEADERS)
                r.raise_for_status()
            except Exception as e:
                return jsonify({"error": str(e)}), 502
            content_type = r.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
            url = media_url

    ext = mimetypes.guess_extension(content_type) or ".bin"
    if ext == ".jpe":
        ext = ".jpg"

    fname = hashlib.md5(url.encode()).hexdigest() + ext
    fpath = os.path.join(_WALLPAPER_DIR, fname)
    with open(fpath, "wb") as f:
        for chunk in r.iter_content(65536):
            f.write(chunk)

    media_type = "video" if content_type.startswith("video/") else "image"
    return jsonify({"url": f"/api/wallpaper/serve/{fname}", "type": media_type})

@api_bp.route("/wallpaper/serve/<fname>")
def wallpaper_serve(fname):
    return send_from_directory(_WALLPAPER_DIR, fname)

@api_bp.route("/wallpaper/upload", methods=["POST"])
def wallpaper_upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file"}), 400
    content_type = f.content_type or "application/octet-stream"
    ext = mimetypes.guess_extension(content_type) or ".bin"
    if ext == ".jpe":
        ext = ".jpg"
    content = f.read()
    fname = hashlib.md5(content).hexdigest() + ext
    fpath = os.path.join(_WALLPAPER_DIR, fname)
    with open(fpath, "wb") as out:
        out.write(content)
    media_type = "video" if content_type.startswith("video/") else "image"
    return jsonify({"url": f"/api/wallpaper/serve/{fname}", "type": media_type})
