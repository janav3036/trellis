import os
import sys
import logging
from ingesters.spotify import SpotifyIngester
from ingesters.github import GitHubIngester
from ingesters.weather import WeatherIngester
from ingesters.calendar import CalendarIngester

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def spotify_1pm():
    log.info("spotify 1pm: %d new events", SpotifyIngester().run())

def spotify_6pm():
    log.info("spotify 6pm: %d new events", SpotifyIngester().run())

def spotify_11pm():
    log.info("spotify 11pm: %d new events", SpotifyIngester().run())

def spotify_3am():
    log.info("spotify 3am: %d new events", SpotifyIngester().run())

def github_nightly():
    log.info("github nightly: %d new events", GitHubIngester().run())

def weather_daily():
    log.info("weather daily: %d new events", WeatherIngester().run())

def calendar_daily():
    log.info("calendar daily: %d new events", CalendarIngester().run())


JOBS = {
    "spotify_1pm": spotify_1pm,
    "spotify_6pm": spotify_6pm,
    "spotify_11pm": spotify_11pm,
    "spotify_3am": spotify_3am,
    "github_nightly": github_nightly,
    "weather_daily": weather_daily,
    "calendar_daily": calendar_daily,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in JOBS:
        print(f"Usage: scheduler.py <job>  Jobs: {', '.join(JOBS)}")
        sys.exit(1)
    JOBS[sys.argv[1]]()
