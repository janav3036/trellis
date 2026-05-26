from pathlib import Path
import chromadb

_DATA_DIR = Path(__file__).parent.parent / "data" / "chroma"
_client = None
_collection = None

def _get_collection():
    global _client, _collection

    if _collection is None:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(_DATA_DIR))
        _collection = _client.get_or_create_collection("trellis_notes")
    return _collection

def add(ids: list[str], embeddings: list[list[float]], documents: list[str], metadatas: list[dict]):
    col = _get_collection()
    col.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

def query(embedding: list[float], n_results: int = 5) -> list[dict]:
    col = _get_collection()
    results = col.query(query_embeddings=[embedding], n_results=n_results)
    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return chunks

def count() -> int:
    return _get_collection().count()

def delete_by_ids(ids: list[str]): 
    _get_collection().delete(ids=ids)

