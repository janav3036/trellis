import json
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import keyring
from ingesters.base import Ingester
from storage.db import DB_PATH, get_connection

KEYRING_SERVICE = "trellis-calendar"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_FILE = "credentials.json"

class CalendarIngester(Ingester):
    def __init__(self):
        super().__init__(str(DB_PATH))
        self.calendar_id = keyring.get_password(KEYRING_SERVICE, "calendar_id")
        token_json = keyring.get_password(KEYRING_SERVICE, "token_json")
        creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
        self.service = build("calendar", "v3", credentials=creds)

    def _fetch_events(self, time_min: datetime, time_max: datetime) -> list:
        result = self.service.events().list(
            calendarId = self.calendar_id,
            timeMin = time_min.isoformat(),
            timeMax = time_max.isoformat(),
            singleEvents = True,
            orderBy = "startTime"
        ).execute()
        return result.get("items", [])
    
    def _save(self, conn, events: list) -> int:
        count = 0
        for event in events:
            start_raw = event["start"].get("dateTime") or event["start"].get("date")
            end_raw = event["end"].get("dateTime") or event["end"].get("date")

            if "T" in start_raw:
                start_dt = datetime.fromisoformat(start_raw)
                end_dt = datetime.fromisoformat(end_raw)
                duration = int((end_dt-start_dt).total_seconds()/60)
            else:
                start_dt = datetime.fromisoformat(f"{start_raw}T00:00:00+00:00")
                duration=0

            count+= self._insert_event(
                conn, 
                timestamp=start_dt,
                source="calendar",
                event_type="event",
                metadata={
                    "title": event.get("summary", ""),
                    "duration_minutes": duration,
                    "calendar_name": event.get("organizer", {}).get("displayName", ""),
                })
        return count
    
    def run(self) -> int:
        now = datetime.now(timezone.utc)
        time_min = now - timedelta(days=2)
        events = self._fetch_events(time_min, now)
        with get_connection() as conn:
            return self._save(conn, events)
        
    def backfill(self, start_date: datetime) -> int:
        now = datetime.now(timezone.utc)
        events = self._fetch_events(start_date, now)
        with get_connection() as conn:
            return self._save(conn, events)
        
