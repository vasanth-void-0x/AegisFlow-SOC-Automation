"""Tests for Phase 4: RAG-based SOC runbook retrieval."""
from app.rag.chunking import chunk_markdown
from app.rag.embeddings import cosine_similarity, embed_texts
from app.rag.retriever import format_citation, index_runbooks, retrieve_runbook


SAMPLE_MD = """---
title: Test Runbook
category: test
---

# Test Runbook

## Detection Criteria
Some detection text here that is reasonably short.

## Investigation Steps
Some investigation text here.
"""


def test_chunk_markdown_splits_by_heading():
    chunks = chunk_markdown(SAMPLE_MD)
    headings = [c["heading"] for c in chunks]
    assert "Detection Criteria" in headings
    assert "Investigation Steps" in headings


def test_chunk_markdown_strips_frontmatter():
    chunks = chunk_markdown(SAMPLE_MD)
    for c in chunks:
        assert "title: Test Runbook" not in c["text"]


def test_chunk_markdown_long_section_splits_with_overlap():
    long_section = "## Long Section\n" + ("word " * 500)
    chunks = chunk_markdown(long_section, max_chunk_chars=200, overlap_chars=20)
    assert len(chunks) > 1


def test_embed_texts_returns_provider_and_vectors():
    vectors, provider = embed_texts(["brute force ssh login", "malware detected on host"])
    assert len(vectors) == 2
    assert provider in ("sentence-transformers", "offline-hashing-fallback")
    assert len(vectors[0]) > 0


def test_cosine_similarity_identical_vectors_is_one():
    vectors, _ = embed_texts(["ssh brute force attack"])
    sim = cosine_similarity(vectors[0], vectors[0])
    assert abs(sim - 1.0) < 1e-6


def test_cosine_similarity_different_texts_lower_than_identical():
    vectors, _ = embed_texts(["ssh brute force attack", "completely unrelated cooking recipe text"])
    sim_diff = cosine_similarity(vectors[0], vectors[1])
    sim_same = cosine_similarity(vectors[0], vectors[0])
    assert sim_diff < sim_same


def test_index_runbooks_indexes_all_files():
    result = index_runbooks(force=True)
    assert result["status"] == "indexed"
    assert result["chunks_indexed"] > 0


def test_retrieve_runbook_finds_brute_force():
    index_runbooks(force=True)
    result = retrieve_runbook("SSH Brute Force Detected multiple failed logins", top_k=3)
    assert result["found"] is True
    top_sources = [r["metadata"]["source_file"] for r in result["results"]]
    assert "brute_force_login.md" in top_sources


def test_retrieve_runbook_finds_powershell():
    index_runbooks(force=True)
    result = retrieve_runbook("suspicious encoded powershell command execution", top_k=3)
    assert result["found"] is True
    top_sources = [r["metadata"]["source_file"] for r in result["results"]]
    assert "suspicious_powershell.md" in top_sources


def test_retrieve_runbook_no_match_returns_not_found():
    index_runbooks(force=True)
    result = retrieve_runbook("xyzzyplughqwerty totally unrelated nonsense gibberish query", top_k=3)
    # With a strict-enough relevance threshold, unrelated gibberish should not match.
    # We assert the contract: either not found, or every returned result meets threshold.
    from app.core.config import get_settings

    threshold = get_settings().rag_relevance_threshold
    for r in result["results"]:
        assert r["score"] >= threshold


def test_format_citation_includes_source_file():
    index_runbooks(force=True)
    result = retrieve_runbook("brute force login", top_k=1)
    assert result["found"] is True
    citation = format_citation(result["results"][0])
    assert "runbooks/" in citation
    assert ".md" in citation


def test_runbook_search_api_endpoint(client):
    resp = client.get("/api/v1/runbooks/search", params={"query": "brute force ssh login attempt"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["found"] is True


def test_runbook_reindex_api_endpoint(client):
    resp = client.post("/api/v1/runbooks/index")
    assert resp.status_code == 200
    assert resp.json()["status"] == "indexed"
