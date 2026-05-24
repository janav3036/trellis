import json
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from ingesters.base import Ingester
from storage.credentials import get as get_cred
from storage.db import DB_PATH, get_connection

KEYRING_SERVICE = "trellis-calendar"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

class CalendarIngester(Ingester):
    def __init__(self):
        super().__init__(str(DB_PATH))
        token_json = get_cred("GOOGLE_CALENDAR_TOKEN_JSON", KEYRING_SERVICE, "token_json")
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
        self.service = build("calendar", "v3", credentials=creds)

    def _fetch_events(self, time_min: datetime, time_max: datetime) -> list:
        if time_min.tzinfo is None:
            time_min = time_min.replace(tzinfo=timezone.utc)
        if time_max.tzinfo is None:
            time_max = time_max.replace(tzinfo=timezone.utc)
        calendars = self.service.calendarList().list().execute().get("items", [])
        all_events = []
        for cal in calendars:
            result = self.service.events().list(
                calendarId=cal["id"],
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            for event in result.get("items", []):
                event["_calendar_name"] = cal["summary"]
            all_events.extend(result.get("items", []))
        return all_events

    def _save(self, conn, events: list) -> int:
        count = 0
        for event in events:
            start_raw = event["start"].get("dateTime") or event["start"].get("date")
            end_raw = event["end"].get("dateTime") or event["end"].get("date")

            if "T" in start_raw:
                start_dt = datetime.fromisoformat(start_raw)
                end_dt = datetime.fromisoformat(end_raw)
                duration = int((end_dt - start_dt).total_seconds() / 60)
            else:
                start_dt = datetime.fromisoformat(f"{start_raw}T00:00:00+00:00")
                duration = 0

            count += self._insert_event(
                conn,
                timestamp=start_dt,
                source="calendar",
                event_type="event",
                metadata={
                    "title": event.get("summary", ""),
                    "duration_minutes": duration,
                    "calendar_name": event.get("_calendar_name", ""),
                })
        return count

    def run(self) -> int:
        now = datetime.now(timezone.utc)
        time_min = now - timedelta(days=2)
        time_max = now + timedelta(days=60)
        events = self._fetch_events(time_min, time_max)
        with get_connection() as conn:
            return self._save(conn, events)

    def backfill(self, start_date: datetime) -> int:
        now = datetime.now(timezone.utc)
        events = self._fetch_events(start_date, now)
        with get_connection() as conn:
            return self._save(conn, events)
