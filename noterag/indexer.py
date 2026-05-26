from storage.db import get_connection
from noterag.chunker import chunk_event
from noterag import embedder, store

BATCH_SIZE = 64

def index_events() -> int:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, source, event_type, metadata FROM events WHERE embedding_id IS NULL"
        ).fetchall()

    if not rows:
        return 0
    
    ids, texts, metadata, event_ids = [], [], [], []

    for row in rows:
        chunk = chunk_event(row)
        if chunk is None:
            continue
        doc_id = f"evt-{row['id']}"
        ids.append(doc_id)
        texts.append(chunk["text"])
        metadata.append(chunk["metadata"])
        event_ids.append(row["id"])

    total = 0
    for i in range(0, len(ids), BATCH_SIZE):
        batch_ids = ids[i: i + BATCH_SIZE]
        batch_texts = texts[i: i + BATCH_SIZE]
        batch_metas = metadata[i: i + BATCH_SIZE]
        batch_event_ids = event_ids[i: i + BATCH_SIZE]

        embeddings = embedder.embed(batch_texts)
        store.add(batch_ids, embeddings, batch_texts, batch_metas)

        with get_connection() as conn:
            for j, eid in enumerate(batch_event_ids):
                conn.execute(
                    "UPDATE events SET embedding_id = ? WHERE id = ?",
                    (batch_ids[j], eid)
                )
        total += len(batch_ids)
    
    return total