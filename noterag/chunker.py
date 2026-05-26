import json

def chunk_event(row) -> dict | None:
    meta = json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"]
    source = row["source"]
    event_type = row["event_type"]
    date = row["timestamp"][:10]

    if source == "spotify" and event_type == "play":
        text = f"Listened to {meta.get('track_name', '')} by {meta.get('artist', '')} from the album {meta.get('album', '')} on {date}"
    elif source == "github" and event_type == "commit":
        text = f"GitHub commit on {date} in {meta.get('repo', '')}: {meta.get('message', '')}"
    elif source == "github" and event_type == "pr":
        text = f"GitHub pull request on {date} in {meta.get('repo', '')}: {meta.get('title', '')} ({meta.get('state', '')})"
    elif source == "dreams" and event_type == "dream":
        mood = meta.get("mood", "")
        lucid = " (lucid)" if meta.get("lucid") else ""
        text = f"Dream journal{lucid} on {date}: {meta.get('title', '')}. {meta.get('description', '')}. Mood: {mood}"
    elif source == "movies" and event_type == "watch":
        genres = ", ".join(str(g) for g in meta.get("genres", []))
        text = f"Watched {meta.get('title', '')} ({meta.get('year', '')}) on {date}. Genres: {genres}. {meta.get('overview', '')} Notes: {meta.get('notes', '')}"
    elif source == "people" and event_type == "meetup":
        text = f"Met {meta.get('name', '')} ({meta.get('tag', '')}) on {date}. Notes: {meta.get('notes', '')}"
    elif source == "letters" and event_type == "future":
        text = f"Letter to future self written on {date}, to be opened {meta.get('unlock_date', '')}: {meta.get('body', '')}"
    elif source == "quotes" and event_type == "quote":
        text = f"Quote saved on {date}: \"{meta.get('text', '')}\" — {meta.get('author', '')}"
    elif source == "habits" and event_type == "checkin":
        text = f"Completed habit '{meta.get('habit_name', '')}' on {date}"
    elif source == "gym" and event_type == "session":
        groups = ", ".join(meta.get("muscle_groups", []))
        text = f"Gym session on {date}: {meta.get('type', '')}. Muscle groups: {groups}. Notes: {meta.get('notes', '')}"
    elif source == "calendar" and event_type == "event":
        text = f"Calendar event on {date}: {meta.get('title', '')} ({meta.get('duration_minutes', '')} min, {meta.get('calendar_name', '')})"
    elif source == "weather" and event_type == "daily":
        text = f"Weather on {date}: max {meta.get('temp_max', '')}°C, min {meta.get('temp_min', '')}°C, precipitation {meta.get('precipitation', '')}mm"
    elif source == "photos" and event_type == "daily":
        text = f"Photo of the day on {date}: {meta.get('caption', '')}"
    else:
        return None

    if not text.strip():
        return None

    return {
        "text": text,
        "metadata": {
            "source": source,
            "event_type": event_type,
            "date": date,
            "event_id": str(row["id"]),
        },
    }


def chunk_text(text: str, filepath: str, chunk_size: int = 1000, overlap: int = 100) -> list[dict]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append({
                "text": chunk,
                "metadata": {
                    "source": "file",
                    "event_type": "text_chunk",
                    "filepath": filepath,
                    "date": "",
                    "event_id": "",
                    "chunk_index": len(chunks),
                },
            })
        start += chunk_size - overlap
    return chunks
