import keyring
import requests
from datetime import date, datetime, timedelta
from ingesters.base import Ingester
from storage.db import DB_PATH, get_connection

KEYRING_SERVICE = "trellis-weather"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DAILY_VARS = "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode,windspeed_10m_max"

class WeatherIngester(Ingester):
    def __init__(self):
        super().__init__(str(DB_PATH))
        self.lat = keyring.get_password(KEYRING_SERVICE, "lat")
        self.lon = keyring.get_password(KEYRING_SERVICE, "lon")

    def _fetch_archive(self, start: date, end: date) -> dict:
        resp = requests.get(ARCHIVE_URL, params={
            "latitude": self.lat,
            "longitude": self.lon,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": DAILY_VARS,
            "timezone": "auto"
        })
        resp.raise_for_status()
        return resp.json()["daily"]

    def _fetch_forecast(self, past_days: int) -> dict:
        resp = requests.get(FORECAST_URL, params={
            "latitude": self.lat,
            "longitude": self.lon,
            "past_days": past_days,
            "forecast_days": 1,
            "daily": DAILY_VARS,
            "timezone": "auto"
        })
        resp.raise_for_status()
        return resp.json()["daily"]


    def _save(self, conn, daily: dict) -> int:
        count = 0
        for i, day_str in enumerate(daily["time"]):
            ts = datetime.fromisoformat(f"{day_str}T12:00:00")
            count+= self._insert_event(conn, timestamp=ts, source="weather", 
                        event_type="daily", metadata={
                            "temp_max": daily["temperature_2m_max"][i],
                            "temp_min": daily["temperature_2m_min"][i],
                            "precipitation": daily["precipitation_sum"][i],
                            "weathercode": daily["weathercode"][i],
                            "windspeed_max": daily["windspeed_10m_max"][i]
                        })
        return count
    
    def run(self) -> int:
        daily = self._fetch_forecast(past_days=2)
        with get_connection() as conn:
            return self._save(conn, daily)
        
    def backfill(self, start_date: datetime) -> int:
        start = start_date.date
        end = date.today()
        daily = self._fetch_archive(start, end)
        with get_connection as conn:
            return self._save(conn, daily)