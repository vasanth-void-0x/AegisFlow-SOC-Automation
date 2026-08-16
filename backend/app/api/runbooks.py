"""Phase 4 API: SOC runbook RAG retrieval."""
from fastapi import APIRouter, Query

from app.rag.retriever import format_citation, index_runbooks, retrieve_runbook

router = APIRouter(tags=["runbooks"])


@router.post("/runbooks/index")
def reindex_runbooks() -> dict:
    """Force re-indexing of runbooks (e.g. after editing a runbook file)."""
    return index_runbooks(force=True)


@router.get("/runbooks/search")
def search_runbooks(query: str, top_k: int = Query(default=3, ge=1, le=10), category: str | None = None) -> dict:
    """Search SOC runbooks by semantic similarity, with source citations."""
    result = retrieve_runbook(query, top_k=top_k, category=category)
    if result["found"]:
        for r in result["results"]:
            r["citation"] = format_citation(r)
    return result
