from __future__ import annotations

import logging
from typing import Any

from backend.config import get_settings
from backend.law_client import get_law_summary, search_related_laws
from backend.rag.chunking import chunk_document
from backend.rag.status import get_rag_status
from backend.rag.vector_store import (
    COLLECTION_CONTRACT,
    add_document_chunks,
    search_similar_chunks,
)

logger = logging.getLogger(__name__)


def build_law_context(
    contract_text: str,
    issues: list[dict[str, Any]] | None = None,
    *,
    filename: str = "contract",
) -> dict[str, Any]:
    """
    Phase 3 - 법령·계약 맥락 수집 (semantic + Law API).
    실패해도 빈 구조 반환.
    """
    issues = issues or []
    enabled, chroma_status, _ = get_rag_status()
    settings = get_settings()

    result: dict[str, Any] = {
        "law_context": "",
        "related_laws": [],
        "retrieved_chunks": [],
        "retrieved_docs": [],
        "rag_used": False,
        "chroma_status": chroma_status,
    }

    queries: list[str] = []
    if issues:
        for issue in issues[:5]:
            queries.append(f"{issue.get('title', '')} {issue.get('description', '')}")
    else:
        queries.append(contract_text[:500])

    # 국가법령 API (항상 시도, local fallback 내장)
    seen_ids: set[str] = set()
    for q in queries[:3]:
        for law in search_related_laws(q, limit=2):
            lid = law.get("law_id", "")
            if lid in seen_ids:
                continue
            seen_ids.add(lid)
            summary = get_law_summary(lid)
            result["related_laws"].append({**law, "detail": summary.get("summary", "")})

    # Chroma semantic (rag_enabled일 때만)
    if enabled:
        try:
            result["rag_used"] = True
            chunks = chunk_document(contract_text, source="contract", filename=filename)
            chunk_dicts = [
                {
                    "text": c.text,
                    "source": c.source,
                    "filename": c.filename,
                    "chunk_index": c.chunk_index,
                }
                for c in chunks
            ]
            if chunk_dicts:
                add_document_chunks(chunk_dicts, collection_name=COLLECTION_CONTRACT)

            for q in queries[:3]:
                legal_hits = search_similar_chunks(q, top_k=2)
                contract_hits = search_similar_chunks(
                    q, top_k=2, collection_name=COLLECTION_CONTRACT
                )
                for hit in legal_hits + contract_hits:
                    result["retrieved_chunks"].append(hit)
                    meta = hit.get("metadata", {})
                    result["retrieved_docs"].append({
                        "id": meta.get("id", hit.get("id", "")),
                        "category": meta.get("filename", meta.get("category", "RAG")),
                        "clause": meta.get("clause", "검색 조항"),
                        "content": hit.get("content", ""),
                        "keywords": [],
                        "score": hit.get("score", 0),
                    })
        except Exception as exc:
            logger.warning("[RAG] retrieve_law_context chroma failed: %s", exc)
            result["rag_used"] = False

    # law_context 텍스트 조립
    parts: list[str] = []
    if result["related_laws"]:
        parts.append("## 관련 법령 (국가법령정보센터/로컬DB)")
        for law in result["related_laws"][:5]:
            parts.append(f"- {law.get('title')}: {law.get('summary', '')[:400]}")
            if law.get("detail"):
                parts.append(f"  상세: {str(law['detail'])[:300]}")

    if result["retrieved_chunks"]:
        parts.append("## RAG 검색 근거")
        for i, ch in enumerate(result["retrieved_chunks"][:5], 1):
            parts.append(f"{i}. (score={ch.get('score', 0):.2f}) {ch.get('content', '')[:350]}")

    result["law_context"] = "\n".join(parts)
    if not result["law_context"] and not settings.law_api_key.strip():
        result["law_context"] = "(법령 RAG 비활성 - 규칙/키워드 fallback 사용)"

    logger.info(
        "[RAG] context_len=%s laws=%s chunks=%s rag_used=%s",
        len(result["law_context"]),
        len(result["related_laws"]),
        len(result["retrieved_chunks"]),
        result["rag_used"],
    )
    return result
