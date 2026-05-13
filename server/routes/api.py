import json
from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, redirect, request, Response
from storage.db import get_connection
from ingesters.spotify import SpotifyIngester
from ingesters.github import GitHubIngester
from ingesters.weather import WeatherIngester
from ingesters.calendar import CalendarIngester

import keyring
import requests as req

api_bp = Blueprint("api", __name__)

@api_bp.route("/events")
def get_events():
    source = request.args.get("source")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    event_type = request.args.get("event_type")

    query ="SELECT * FROM events WHERE 1=1"
    params = []

    if source:
        query += " AND source = ?"
        params.append(source)
    if date_from:
        query +=" AND timestamp >= ?"
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
    ingester = SpotifyIngester()
    resp = req.get(
        "https://api.spotify.com/v1/me/player/currently-playing",
        headers=ingester._get_headers()
    )
    if resp.status_code == 401:
        ingester._refresh_token()
        resp = req.get(
            "https://api.spotify.com/v1/me/player/currently-playing",
            headers=ingester._get_headers()
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
        return jsonify({"error": "date_from required" }), 400
    count  = WeatherIngester().backfill(datetime.fromisoformat(date_from))
    return jsonify({"count": count})

@api_bp.route("/weather/forecast")
def weather_forecast():
    ingester = WeatherIngester()
    resp = req.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": ingester.lat,
        "longitude": ingester.lon,
        "forecast_days": 14,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,windspeed_10m_max",
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
                "windspeed_max": daily["windspeed_10m_max"][i]
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
    api_key = keyring.get_password("trellis-tmdb", "api_key")
    resp = req.get("https://api.themoviedb.org/3/search/movie", params ={
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


@api_bp.route("/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
    return jsonify({"deleted": cur.rowcount})

@api_bp.route("/f1/schedule")
def f1_schedule():
    resp = req.get("https://api.jolpi.ca/ergast/f1/current.json", timeout = 10)
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
