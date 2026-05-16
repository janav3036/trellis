import json
import smtplib
import keyring
from datetime import datetime, timezone
from email.mime.text import MIMEText
from storage.db import get_connection

GMAIL_USER = "janavdshah30@gmail.com"

def main():
    today = datetime.now(timezone.utc).date().isoformat()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, metadata FROM events WHERE source='letters' AND event_type='future'"
        ).fetchall()

    to_send = [
        json.loads(r[1]) for r in rows
        if json.loads(r[1]).get("unlock_date") == today
    ]

    if not to_send:
        return

    password = keyring.get_password("trellis", "gmail_app_password")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, password)
        for letter in to_send:
            msg = MIMEText(letter["body"], "plain")
            msg["Subject"] = f"A letter from your past self — {today}"
            msg["From"] = GMAIL_USER
            msg["To"] = GMAIL_USER
            smtp.send_message(msg)
            print(f"Sent letter unlocked on {today}")

if __name__ == "__main__":
    main()
