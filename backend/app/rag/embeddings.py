"""
Pluggable embedding layer for RAG.

Primary path: sentence-transformers (local model, suitable for an 8GB laptop -
e.g. all-MiniLM-L6-v2, ~80MB). This requires the model weights to be
downloaded once from Hugging Face on first use.

Fallback path: a deterministic offline hashing-based bag-of-words vectorizer.
This has no external dependency at all and keeps RAG fully functional
(with lower semantic quality) in network-restricted environments, or before
the sentence-transformers model has been downloaded.

The active provider is always reported alongside retrieval results so the
system never silently claims semantic-embedding quality it didn't use.
"""
import hashlib
import math
import re
from functools import lru_cache

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_HASH_DIM = 384  # matches all-MiniLM-L6-v2 output dim, so both paths are interchangeable


@lru_cache(maxsize=1)
def _try_load_sentence_transformer():
    """Attempt to load the configured sentence-transformers model. Cached so we
    only try once per process. Returns None if unavailable for any reason."""
    settings = get_settings()
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(settings.embedding_model_name)
        logger.info("Loaded sentence-transformers model: %s", settings.embedding_model_name)
        return model
    except Exception as exc:  # noqa: BLE001 - any failure (no network, no package, etc.) -> fallback
        logger.warning(
            "sentence-transformers unavailable (%s) - using offline hashing embedding fallback", exc
        )
        return None


def _hash_embed(text: str, dim: int = _HASH_DIM) -> list[float]:
    """Deterministic offline embedding: hashed bag-of-words, L2-normalized."""
    tokens = _TOKEN_RE.findall(text.lower())
    vec = [0.0] * dim
    for tok in tokens:
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h // dim) % 2 == 0 else -1.0
        vec[idx] += sign

    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed_texts(texts: list[str]) -> tuple[list[list[float]], str]:
    """Returns (embeddings, provider_name) where provider_name is one of
    'sentence-transformers' or 'offline-hashing-fallback'."""
    model = _try_load_sentence_transformer()
    if model is not None:
        vectors = model.encode(texts, normalize_embeddings=True).tolist()
        return vectors, "sentence-transformers"

    vectors = [_hash_embed(t) for t in texts]
    return vectors, "offline-hashing-fallback"


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)
