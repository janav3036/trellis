import base64
import json
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlencode

import keyring
import requests

from ingesters.base import Ingester
from storage.db import DB_PATH, get_connection

KEYRING_SERVICE = "trellis-spotify"
AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"
SCOPES = "user-read-recently-played"
REDIRECT_URI = "http://127.0.0.1:5000/api/callback/spotify"


class SpotifyIngester(Ingester):
    def __init__(self):
        super().__init__(str(DB_PATH))
        self.client_id = keyring.get_password(KEYRING_SERVICE, "client_id")
        self.client_secret = keyring.get_password(KEYRING_SERVICE, "client_secret")

    def get_auth_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
        }
        return f"{AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> None:
        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        resp = requests.post(
            TOKEN_URL,
            headers={"Authorization": f"Basic {credentials}"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
        )
        resp.raise_for_status()
        tokens = resp.json()
        keyring.set_password(KEYRING_SERVICE, "access_token", tokens["access_token"])
        keyring.set_password(KEYRING_SERVICE, "refresh_token", tokens["refresh_token"])

    def _refresh_token(self) -> str:
        refresh_token = keyring.get_password(KEYRING_SERVICE, "refresh_token")
        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()
        resp = requests.post(
            TOKEN_URL,
            headers={"Authorization": f"Basic {credentials}"},
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        )
        resp.raise_for_status()
        new_token = resp.json()["access_token"]
        keyring.set_password(KEYRING_SERVICE, "access_token", new_token)
        return new_token

    def _get_headers(self) -> dict:
        token = keyring.get_password(KEYRING_SERVICE, "access_token")
        return {"Authorization": f"Bearer {token}"}

    def _fetch_recent_plays(self, limit: int = 50, before: int | None = None) -> list:
        params = {"limit": limit}
        if before:
            params["before"] = before
        resp = requests.get(
            f"{API_BASE}/me/player/recently-played",
            headers=self._get_headers(),
            params=params,
        )
        if resp.status_code == 401:
            self._refresh_token()
            resp = requests.get(
                f"{API_BASE}/me/player/recently-played",
                headers=self._get_headers(),
                params=params,
            )
        resp.raise_for_status()
        return resp.json().get("items", [])

    def _items_to_events(self, conn: sqlite3.Connection, items: list) -> int:
        count = 0
        for item in items:
            track = item["track"]
            played_at = datetime.fromisoformat(
                item["played_at"].replace("Z", "+00:00")
            )
            count+=self._insert_event(
                conn,
                timestamp=played_at,
                source="spotify",
                event_type="play",
                metadata={
                    "track_id": track["id"],
                    "track_name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                    "duration_ms": track["duration_ms"],
                },
            )
        return count

    def run(self) -> int:
        items = self._fetch_recent_plays()
        with get_connection() as conn:
            count = self._items_to_events(conn, items)
        return count

    def backfill(self, start_date: datetime) -> int:
        start_ms = int(start_date.timestamp() * 1000)
        total = 0
        before = None
        with get_connection() as conn:
            while True:
                items = self._fetch_recent_plays(before=before)
                if not items:
                    break
                oldest = items[-1]
                oldest_ms = int(
                    datetime.fromisoformat(
                        oldest["played_at"].replace("Z", "+00:00")
                    ).timestamp() * 1000
                )
                total += self._items_to_events(conn, items)
                if oldest_ms <= start_ms:
                    break
                before = oldest_ms
        return total
