from noterag import embedder, store 

def retrieve(query: str, n: int = 5) -> list[dict]:
    embedding = embedder.embed([query])[0]
    return store.query(embedding, n_results=n)