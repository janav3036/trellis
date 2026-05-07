import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from ingesters.spotify import SpotifyIngester
from ingesters.github import GitHubIngester
from ingesters.weather import WeatherIngester
from ingesters.calendar import CalendarIngester

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)
scheduler = BlockingScheduler()

@scheduler.scheduled_job('cron', hour=13, minute=0)
def spotify_1pm():
    count = SpotifyIngester().run()
    log.info("spotify 1pm: %d new events", count)

@scheduler.scheduled_job('cron', hour=18, minute=0)
def spotify_6pm():
    count = SpotifyIngester().run()
    log.info("spotify 6pm: %d new events", count)

@scheduler.scheduled_job('cron', hour=23, minute=0)
def spotify_11pm():
    count = SpotifyIngester().run()
    log.info("spotify 11pm: %d new events", count)

@scheduler.scheduled_job('cron', hour=3, minute=0)
def spotify_3am():
    count = SpotifyIngester().run()
    log.info("spotify 3am: %d new events", count)

@scheduler.scheduled_job('cron', hour=23, minute=0)
def github_nightly():
    count = GitHubIngester().run()
    log.info("github nightly: %d new events", count)

@scheduler.scheduled_job('cron', hour=13, minute=0)
def weather_daily():
    count = WeatherIngester().run()
    log.info("weather daily: %d new events", count)

@scheduler.scheduled_job('cron', hour=7, minute=0)
def calendar_daily():
    count = CalendarIngester().run()
    log.info("calendar daily: %d new events", count)

if __name__ == "__main__":
    log.info("scheduler starting")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("scheduler stopped")
