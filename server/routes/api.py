import json
from datetime import datetime
from flask import Blueprint, jsonify, redirect, request
from storage.db import get_connection
from ingesters.spotify import SpotifyIngester
from ingesters.github import GitHubIngester
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
        "cover": item["album"]["images"][0]["url"] if item["album"]["images"] else None,
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
            "cover": p["images"][0]["url"] if p["images"] else None,
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