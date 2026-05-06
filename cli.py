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
    from ingesters.spotify import SpotifyIngester
    url = SpotifyIngester().get_auth_url()
    print("Visit this URL to authorize Spotify: ")
    print(url)
    print("(Flask must be running on port 5000)")

def cmd_setup(args):
    handlers = {
        "github": setup_github,
        "spotify": setup_spotify,
    }
    handlers[args.source]()

def cmd_backfill(args):
    since = datetime.strptime(args.since, "%Y-%m-%d")
    if args.source == "spotify":
        from ingesters.spotify import SpotifyIngester
        count = SpotifyIngester().backfill(since)
    else:
        from ingesters.github import GitHubIngester
        count = GitHubIngester().backfill(since)

    print(f"Backfilled {count} events from {args.source}")

def cmd_run(args): 
    from ingesters.spotify import SpotifyIngester
    from ingesters.github import GitHubIngester

    for name, ingester in [("spotify", SpotifyIngester()), ("github", GitHubIngester())]:
        count = ingester.run()
        print(f"{name}: {count} new events")

def main():
    parser = argparse.ArgumentParser(prog="trellis")
    subs = parser.add_subparsers(dest="command")

    subs.add_parser("run")

    p_backfill = subs.add_parser("backfill")
    p_backfill.add_argument("source", choices=["spotify", "github"])
    p_backfill.add_argument("since", help="YYYY-MM-DD")

    p_setup = subs.add_parser("setup")
    p_setup.add_argument("source", choices=["spotify", "github"])

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
