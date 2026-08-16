"""
Phase 4: RAG-based SOC runbook retrieval.

Loads Markdown runbooks from the /runbooks directory, chunks them, embeds
them (via the pluggable embedding provider), and serves similarity search
with a relevance threshold, metadata filtering, and source citations.

If nothing clears the relevance threshold, retrieval returns an explicit
"no relevant runbook found" result rather than forcing a low-quality match -
the LLM must never be told to cite a runbook that isn't actually relevant.
"""
import re
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import get_logger
from app.rag.chunking import chunk_markdown
from app.rag.embeddings import embed_texts
from app.rag.vector_store import get_fallback_store, try_get_chromadb_collection

logger = get_logger(__name__)

_indexed = False
_active_embedding_provider = "unknown"


def _parse_frontmatter(text: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip("[]").replace("'", "").replace('"', "")
    return meta


def _runbooks_dir() -> Path:
    # backend/app/rag/retriever.py -> repo_root/runbooks
    return Path(__file__).resolve().parents[3] / "runbooks"


def index_runbooks(force: bool = False) -> dict:
    """Load, chunk, embed, and index all runbooks. Idempotent unless force=True."""
    global _indexed, _active_embedding_provider

    if _indexed and not force:
        return {"status": "already_indexed", "provider": _active_embedding_provider}

    runbooks_path = _runbooks_dir()
    if not runbooks_path.exists():
        logger.warning("Runbooks directory not found at %s", runbooks_path)
        return {"status": "no_runbooks_dir", "chunks_indexed": 0}

    all_chunks = []
    for md_file in sorted(runbooks_path.glob("*.md")):
        raw = md_file.read_text(encoding="utf-8")
        meta = _parse_frontmatter(raw)
        for chunk in chunk_markdown(raw):
            all_chunks.append(
                {
                    "id": f"{md_file.stem}::{chunk['heading']}",
                    "text": chunk["text"],
                    "source_file": md_file.name,
                    "title": meta.get("title", md_file.stem),
                    "category": meta.get("category", "uncategorized"),
                    "heading": chunk["heading"],
                }
            )

    if not all_chunks:
        return {"status": "no_chunks_found", "chunks_indexed": 0}

    texts = [c["text"] for c in all_chunks]
    embeddings, provider = embed_texts(texts)
    _active_embedding_provider = provider

    collection = try_get_chromadb_collection()
    if collection is not None:
        collection.upsert(
            ids=[c["id"] for c in all_chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[
                {"source_file": c["source_file"], "title": c["title"], "category": c["category"], "heading": c["heading"]}
                for c in all_chunks
            ],
        )
    else:
        store = get_fallback_store()
        store.clear()
        for chunk, embedding in zip(all_chunks, embeddings):
            store.add(
                chunk_id=chunk["id"],
                text=chunk["text"],
                embedding=embedding,
                metadata={
                    "source_file": chunk["source_file"],
                    "title": chunk["title"],
                    "category": chunk["category"],
                    "heading": chunk["heading"],
                },
            )

    _indexed = True
    logger.info("Indexed %d runbook chunks using %s embedding provider", len(all_chunks), provider)
    return {"status": "indexed", "chunks_indexed": len(all_chunks), "provider": provider}


def retrieve_runbook(query: str, top_k: int = 3, category: str | None = None) -> dict:
    """
    Retrieve the most relevant runbook chunk(s) for a query.
    Returns {"found": bool, "results": [...], "provider": str} - results
    include source file, heading, text, and similarity score for citation.
    """
    settings = get_settings()
    index_runbooks()  # no-op if already indexed

    query_embedding, provider = embed_texts([query])
    query_vec = query_embedding[0]

    collection = try_get_chromadb_collection()
    metadata_filter = {"category": category} if category else None

    if collection is not None:
        where = {"category": category} if category else None
        raw = collection.query(query_embeddings=[query_vec], n_results=top_k, where=where)
        results = []
        if raw.get("ids") and raw["ids"][0]:
            for i, chunk_id in enumerate(raw["ids"][0]):
                distance = raw["distances"][0][i]
                score = 1 - distance  # chroma default is L2/cosine distance; approximate conversion
                results.append(
                    {
                        "id": chunk_id,
                        "text": raw["documents"][0][i],
                        "metadata": raw["metadatas"][0][i],
                        "score": score,
                    }
                )
    else:
        store = get_fallback_store()
        results = store.query(query_vec, top_k=top_k, metadata_filter=metadata_filter)

    relevant = [r for r in results if r["score"] >= settings.rag_relevance_threshold]

    if not relevant:
        return {"found": False, "results": [], "provider": provider, "message": "No relevant runbook found"}

    return {"found": True, "results": relevant, "provider": provider}


def format_citation(result: dict) -> str:
    meta = result["metadata"]
    return f"[{meta['title']} - {meta['heading']}] (source: runbooks/{meta['source_file']}, score={result['score']:.2f})"
