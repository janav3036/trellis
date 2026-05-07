import argparse
import sys
from datetime import datetime
import getpass
import keyring

def setup_github():
    token = getpass.getpass("GitHub personal access token: ")
    username = input("GitHub username: ")
    keyring.set_password("trellis-github", "token", token)
    keyring.set_password("trellis-github", "username", username)
    print("GitHub credentials saved")

def setup_spotify():
    client_id = getpass.getpass("Spotify client ID: ")
    client_secret = getpass.getpass("Spotify client secret: ")
    keyring.set_password("trellis-spotify", "client_id", client_id)
    keyring.set_password("trellis-spotify", "client_secret", client_secret)
    from ingesters.spotify import SpotifyIngester
    url = SpotifyIngester().get_auth_url()
    print("Visit this URL to authorize Spotify: ")
    print(url)
    print("(Flask must be running on port 5000)")

def setup_weather():
    lat = input("Enter latitude: ")
    lon = input("Enter longitude: ")
    keyring.set_password("trellis-weather", "lat", lat)
    keyring.set_password("trellis-weather", "lon", lon)
    print("Latitude and longitude saved")

def setup_calendar():
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.oauth2.credentials import Credentials
    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=8080)
    keyring.set_password("trellis-calendar", "token_json", creds.to_json())
    calendar_id = input("Calendar ID (find in Google Calendar settings): ")
    keyring.set_password("trellis-calendar", "calendar_id", calendar_id)
    print("Calendar credentials saved")

def cmd_setup(args):
    handlers = {
        "github": setup_github,
        "spotify": setup_spotify,
        "weather": setup_weather,
        "calendar": setup_calendar,
    }
    handlers[args.source]()

def cmd_backfill(args):
    since = datetime.strptime(args.since, "%Y-%m-%d")
    if args.source == "spotify":
        from ingesters.spotify import SpotifyIngester
        count = SpotifyIngester().backfill(since)
    elif args.source == "weather":
        from ingesters.weather import WeatherIngester
        count = WeatherIngester().backfill(since)
    elif args.source == "calendar":
        from ingesters.calendar import CalendarIngester
        count = CalendarIngester().backfill(since)
    else:
        from ingesters.github import GitHubIngester
        count = GitHubIngester().backfill(since)

    print(f"Backfilled {count} events from {args.source}")

def cmd_run(args): 
    from ingesters.spotify import SpotifyIngester
    from ingesters.github import GitHubIngester
    from ingesters.weather import WeatherIngester
    from ingesters.calendar import CalendarIngester

    for name, ingester in [
        ("spotify", SpotifyIngester()), 
        ("github", GitHubIngester()), 
        ("weather", WeatherIngester()),
        ("calendar", CalendarIngester())]:
        count = ingester.run()
        print(f"{name}: {count} new events")

def main():
    parser = argparse.ArgumentParser(prog="trellis")
    subs = parser.add_subparsers(dest="command")

    subs.add_parser("run")

    p_backfill = subs.add_parser("backfill")
    p_backfill.add_argument("source", choices=["spotify", "github", "weather", "calendar"])
    p_backfill.add_argument("since", help="YYYY-MM-DD")

    p_setup = subs.add_parser("setup")
    p_setup.add_argument("source", choices=["spotify", "github", "weather", "calendar"])

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    dispatch = {
        "setup": cmd_setup,
        "backfill": cmd_backfill,
        "run": cmd_run,
    }
    dispatch[args.command](args)


if __name__=="__main__":
    main()
