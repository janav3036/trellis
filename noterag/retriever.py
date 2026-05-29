from noterag import embedder, store

def retrieve(query: str, n: int = 5) -> list[dict]:
    embedding = embedder.embed([query])[0]
    # Fetch a wider pool so Spotify (50k events) can't crowd out rarer sources
    raw = store.query(embedding, n_results=min(n * 8, 60))

    balanced, spotify_seen = [], 0
    for chunk in raw:
        is_spotify = chunk["metadata"].get("source") == "spotify"
        if is_spotify:
            if spotify_seen < 2:
                balanced.append(chunk)
                spotify_seen += 1
        else:
            balanced.append(chunk)
        if len(balanced) >= n:
            break

    return balanced