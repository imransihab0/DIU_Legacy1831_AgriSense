"""ChromaDB (embedded) knowledge base store — Tier 0 #7 (RAG)."""
import chromadb
from ..config import CHROMA_DIR

_client = None
_collection = None


def get_collection(create: bool = False):
    global _client, _collection
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    if _collection is None:
        _collection = _client.get_or_create_collection("agrisense_kb")
    return _collection


def search_knowledge_base(query: str, top_k: int = 4) -> dict:
    col = get_collection()
    if col.count() == 0:
        return {"error": "Knowledge base is empty. Run: python -m app.rag.ingest"}
    res = col.query(query_texts=[query], n_results=min(int(top_k), 8))
    chunks = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        chunks.append({
            "source": meta.get("source"),
            "chunk_index": meta.get("chunk"),
            "relevance": round(1 - dist, 3),
            "text": doc,
        })
    return {"query": query, "retrieved_chunks": chunks}
