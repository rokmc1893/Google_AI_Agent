from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from backend.config import get_settings
from backend.hybrid_rag import LAW_DATABASE
from backend.rag.embedding_service import embed_text, embed_texts

logger = logging.getLogger(__name__)

_client = None
_collection = None
_seeded = False
_probe_ok: bool | None = None

COLLECTION_LEGAL = "legal_knowledge"
COLLECTION_CONTRACT = "contract_chunks"


def probe_chroma() -> bool:
    global _probe_ok
    if _probe_ok is not None:
        return _probe_ok
    try:
        import chromadb  # noqa: F401

        settings = get_settings()
        path = Path(settings.chroma_dir)
        path.mkdir(parents=True, exist_ok=True)
        _probe_ok = True
    except Exception as exc:
        logger.warning("[RAG] chroma probe failed: %s", exc)
        _probe_ok = False
    return _probe_ok


def get_vector_store():
    global _client
    if _client is None:
        import chromadb

        settings = get_settings()
        path = Path(settings.chroma_dir)
        path.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(path))
        logger.info("[RAG] Chroma persistent path=%s", path)
    return _client


def _get_collection(name: str):
    client = get_vector_store()
    return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def _seed_legal_knowledge() -> None:
    global _seeded
    if _seeded:
        return
    col = _get_collection(COLLECTION_LEGAL)
    if col.count() > 0:
        _seeded = True
        return

    ids, docs, metas, embs = [], [], [], []
    for doc in LAW_DATABASE:
        text = f"{doc['clause']}\n{doc['content']}"
        ids.append(doc["id"])
        docs.append(text)
        metas.append({
            "source": "law_db",
            "filename": doc["category"],
            "chunk_index": 0,
            "category": doc["category"],
            "clause": doc["clause"],
        })
        embs.append(embed_text(text))

    if ids:
        col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
        logger.info("[RAG] Seeded %s legal docs into Chroma", len(ids))
    _seeded = True


def add_document_chunks(
    chunks: list[dict[str, Any]],
    collection_name: str = COLLECTION_CONTRACT,
) -> int:
    """chunks: {text, source, filename, chunk_index}"""
    if not chunks:
        return 0
    _seed_legal_knowledge()
    col = _get_collection(collection_name)
    ids, docs, metas = [], [], []
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    for i, c in enumerate(chunks):
        cid = c.get("id") or f"{c.get('source','doc')}_{c.get('chunk_index', i)}_{uuid.uuid4().hex[:8]}"
        ids.append(cid)
        docs.append(c["text"])
        metas.append({
            "source": c.get("source", "contract"),
            "filename": c.get("filename", ""),
            "chunk_index": int(c.get("chunk_index", i)),
        })

    col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
    return len(ids)


def search_similar_chunks(
    query: str,
    top_k: int = 3,
    collection_name: str = COLLECTION_LEGAL,
) -> list[dict[str, Any]]:
    if not query.strip():
        return []
    try:
        _seed_legal_knowledge()
        col = _get_collection(collection_name)
        if col.count() == 0:
            return []
        q_emb = embed_text(query)
        res = col.query(query_embeddings=[q_emb], n_results=min(top_k, col.count()))
        out: list[dict[str, Any]] = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            out.append({
                "content": doc,
                "metadata": meta or {},
                "score": 1.0 - float(dist) if dist is not None else 0.0,
                "id": meta.get("id", "") if meta else "",
            })
        return out
    except Exception as exc:
        logger.warning("[RAG] search_similar_chunks failed: %s", exc)
        return []


if __name__ == "__main__":
    _seed_legal_knowledge()
    hits = search_similar_chunks("지식재산권 일방 귀속", top_k=2)
    print(f"OK P3-Step4 chroma hits={len(hits)}")
    for h in hits:
        print(h["content"][:80], "score=", round(h["score"], 3))
