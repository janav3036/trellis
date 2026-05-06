import requests
import keyring
from datetime import datetime
from ingesters.base import Ingester
from storage.db import get_connection, DB_PATH

KEYRING_SERVICE = "trellis-github"
API_BASE = "https://api.github.com"

class GitHubIngester(Ingester):
    def __init__(self):
        super().__init__(str(DB_PATH))
        self.token = keyring.get_password(KEYRING_SERVICE, "token")
        self.username = keyring.get_password(KEYRING_SERVICE, "username")

    def _headers(self):
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }
    
    def _search(self, endpoint, query, date_filter=None):
        q = f"author:{self.username}" if not query else f"{query} author:{self.username}"
        if date_filter:
            q += f" {date_filter}"

        results = []
        page = 1
        while True:
            resp = requests.get(
                f"{API_BASE}/search/{endpoint}",
                headers = self._headers(),
                params = {"q":q, "per_page": 100, "page":page},

            )
            resp.raise_for_status()
            results.extend(resp.json().get("items", []))
            if 'rel="next"' not in resp.headers.get("Link", ""):
                break
            page+=1
        return results
    
    def run(self):
        since = datetime.now().strftime("%Y-%m-%d")
        with get_connection() as conn:
            return self._ingest(conn, date_filter = f"committer-date:>={since}")
        
    def backfill(self, start_date):
        since = start_date.strftime("%Y-%m-%d")
        with get_connection() as conn:
            return self._ingest(conn, date_filter = f"committer-date:>={since}")
        
    def _ingest(self, conn, date_filter=None):
        count=0
        for commit in self._search("commits", "", date_filter):
            ts = datetime.fromisoformat(
                commit["commit"]["committer"]["date"].replace("Z", "+00:00")
            )

            count+=self._insert_event(conn, timestamp=ts, source="github",
                               event_type = "commit", metadata = {
                                "sha": commit["sha"][:7],
                                "message": commit["commit"]["message"].split("\n")[0],
                                "repo": commit["repository"]["full_name"]
                               })

        for pr in self._search("issues", "type:pr"):
            ts= datetime.fromisoformat(
                pr["created_at"].replace("Z", "+00:00")
            )

            count+=self._insert_event(conn, timestamp=ts, source="github",
                               event_type="pr", metadata={
                                "title": pr["title"],
                                "repo": pr["repository_url"].split("/")[-2] + "/" + pr["repository_url"].split("/")[-1],
                                "number": pr["number"],
                                "state": pr["state"],
                               })
        return count