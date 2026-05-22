from __future__ import annotations

import logging
from functools import lru_cache
from typing import Tuple

from backend.config import get_settings

logger = logging.getLogger(__name__)

_cached: Tuple[bool, str, str] | None = None


def get_rag_status(force_refresh: bool = False) -> tuple[bool, str, str]:
    """
    (rag_enabled, chroma_status, embedding_model_name)
    startup 시 크래시 없이 lazy probe.
    """
    global _cached
    if _cached is not None and not force_refresh:
        return _cached

    settings = get_settings()
    model_name = settings.embedding_model

    if not settings.use_rag:
        _cached = (False, "disabled", model_name)
        return _cached

    try:
        from backend.rag.embedding_service import probe_embedding_model
        from backend.rag.vector_store import probe_chroma

        emb_ok = probe_embedding_model()
        chroma_ok = probe_chroma()
        if emb_ok and chroma_ok:
            _cached = (True, "ready", model_name)
            logger.info("[RAG] rag_enabled=true chroma=ready model=%s", model_name)
        else:
            reason = []
            if not emb_ok:
                reason.append("embedding_unavailable")
            if not chroma_ok:
                reason.append("chroma_unavailable")
            _cached = (False, "unavailable:" + ",".join(reason), model_name)
    except Exception as exc:
        logger.warning("[RAG] probe failed: %s", exc)
        _cached = (False, f"error:{exc.__class__.__name__}", model_name)

    return _cached


def clear_rag_status_cache() -> None:
    global _cached
    _cached = None
    get_rag_status.cache_clear() if hasattr(get_rag_status, "cache_clear") else None
