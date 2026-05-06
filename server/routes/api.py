import json
from flask import Blueprint, jsonify, redirect, request
from storage.db import get_connection
from ingesters.spotify import SpotifyIngester

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


