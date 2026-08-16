"""
Pluggable vector store for RAG.

Primary path: ChromaDB persistent local collection.
Fallback path: a tiny in-process in-memory store using cosine similarity -
functionally sufficient for a handful of SOC runbooks and requires zero
extra services, keeping local dev lightweight on an 8GB laptop.
"""
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.logging import get_logger
from app.rag.embeddings import cosine_similarity

logger = get_logger(__name__)


@dataclass
class StoredChunk:
    id: str
    text: str
    metadata: dict
    embedding: list[float]


class InMemoryVectorStore:
    """Simple fallback store: linear-scan cosine similarity search."""

    def __init__(self):
        self._chunks: list[StoredChunk] = []

    def clear(self) -> None:
        self._chunks = []

    def add(self, chunk_id: str, text: str, embedding: list[float], metadata: dict) -> None:
        self._chunks.append(StoredChunk(id=chunk_id, text=text, metadata=metadata, embedding=embedding))

    def query(self, query_embedding: list[float], top_k: int = 3, metadata_filter: dict | None = None) -> list[dict]:
        candidates = self._chunks
        if metadata_filter:
            candidates = [
                c for c in candidates if all(c.metadata.get(k) == v for k, v in metadata_filter.items())
            ]

        scored = [
            {"id": c.id, "text": c.text, "metadata": c.metadata, "score": cosine_similarity(query_embedding, c.embedding)}
            for c in candidates
        ]
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def is_empty(self) -> bool:
        return len(self._chunks) == 0


def try_get_chromadb_collection():
    """Attempt to get a persistent ChromaDB collection. Returns None on failure."""
    settings = get_settings()
    try:
        import chromadb

        client = chromadb.PersistentClient(path=settings.vector_db_path)
        collection = client.get_or_create_collection(name="soc_runbooks")
        return collection
    except Exception as exc:  # noqa: BLE001
        logger.warning("ChromaDB unavailable (%s) - using in-memory vector store fallback", exc)
        return None


_store_singleton: InMemoryVectorStore | None = None


def get_fallback_store() -> InMemoryVectorStore:
    global _store_singleton
    if _store_singleton is None:
        _store_singleton = InMemoryVectorStore()
    return _store_singleton
