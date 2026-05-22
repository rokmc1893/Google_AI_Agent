from __future__ import annotations

import logging
from typing import List

from backend.config import get_settings

logger = logging.getLogger(__name__)

_model = None
_probe_ok: bool | None = None


def get_embedding_model():
    """sentence-transformers 싱글톤 lazy load."""
    global _model
    if _model is not None:
        return _model
    settings = get_settings()
    from sentence_transformers import SentenceTransformer

    logger.info("[RAG] Loading embedding model: %s", settings.embedding_model)
    _model = SentenceTransformer(settings.embedding_model)
    return _model


def embed_text(text: str) -> List[float]:
    if not text.strip():
        return []
    model = get_embedding_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    model = get_embedding_model()
    vecs = model.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vecs]


def probe_embedding_model() -> bool:
    """가벼운 probe — 전체 모델 로드."""
    global _probe_ok
    if _probe_ok is not None:
        return _probe_ok
    try:
        vec = embed_text("테스트 임베딩")
        _probe_ok = len(vec) > 0
        logger.info("[RAG] embedding dim=%s", len(vec))
    except Exception as exc:
        logger.warning("[RAG] embedding probe failed: %s", exc)
        _probe_ok = False
    return _probe_ok


if __name__ == "__main__":
    v = embed_text("하도급 지체상금")
    print(f"OK P3-Step3 embeddings dim={len(v)}")
