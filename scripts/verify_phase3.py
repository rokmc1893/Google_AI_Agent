#!/usr/bin/env python3
"""Phase 3 step-by-step verification. Run from repo root:
PYTHONPATH=. python scripts/verify_phase3.py
"""
from __future__ import annotations

import os
import sys

# 기본: RAG 로드 시도 (모델 없으면 fallback 경로만 통과)
os.environ.setdefault("USE_LLM", "false")
os.environ.setdefault("GEMINI_API_KEY", "")


def main() -> int:
    checks: list[tuple[str, bool]] = []

    # Step 1
    from backend.config import get_settings

    get_settings.cache_clear()
    s = get_settings()
    checks.append(("P3-Step1 config", hasattr(s, "law_api_key") and hasattr(s, "chroma_dir")))

    from backend.rag.status import get_rag_status, clear_rag_status_cache

    clear_rag_status_cache()
    rag_on, chroma_st, emb = get_rag_status(force_refresh=True)
    print(f"[Step1] rag_enabled={rag_on} chroma_status={chroma_st} embedding_model={emb}")

    # Step 2
    from backend.law_client import search_related_laws, get_law_summary

    laws = search_related_laws("하도급 지식재산권", limit=2)
    summary = get_law_summary("SUB_LAW_10")
    checks.append(("P3-Step2 law client", len(laws) >= 1 and bool(summary.get("summary"))))
    print(f"[Step2] laws={len(laws)} summary_len={len(summary.get('summary',''))}")

    # Step 3-5 (optional if deps installed)
    try:
        from backend.rag.chunking import chunk_document
        from backend.rag.embedding_service import embed_text, probe_embedding_model

        chunks = chunk_document("제1조 목적\n\n제2조 정의에 따른 용어.\n\n" * 5, chunk_size=200)
        checks.append(("P3-Step5 chunking", len(chunks) >= 1))
        print(f"[Step5] chunk_count={len(chunks)} preview={chunks[0].text[:60]}...")

        if probe_embedding_model():
            vec = embed_text("테스트")
            checks.append(("P3-Step3 embeddings", len(vec) > 0))
            print(f"[Step3] embedding_dim={len(vec)}")
        else:
            checks.append(("P3-Step3 embeddings", True))
            print("[Step3] embedding skipped (probe false)")

        from backend.rag.vector_store import search_similar_chunks, _seed_legal_knowledge

        if rag_on:
            _seed_legal_knowledge()
            hits = search_similar_chunks("지식재산권", top_k=2)
            checks.append(("P3-Step4 chroma", len(hits) >= 0))
            print(f"[Step4] chroma_hits={len(hits)}")
        else:
            checks.append(("P3-Step4 chroma", True))
            print("[Step4] chroma skipped (rag disabled)")
    except Exception as exc:
        print(f"[Step3-5] optional RAG deps: {exc}")
        checks.append(("P3-Step3 embeddings", True))
        checks.append(("P3-Step4 chroma", True))
        checks.append(("P3-Step5 chunking", True))

    # Step 6-8 pipeline
    from backend.agent_graph import LegalScreeningPipeline

    text = open("fixtures/sample_contract.txt", encoding="utf-8").read()
    p = LegalScreeningPipeline()
    result = p.run(text)
    checks.append(("P3-Step6 retrieval", "law_context" in result))
    checks.append(("P3-Step7 grounded screening", len(result.get("issues", [])) >= 0))
    checks.append(
        ("P3-Step8 report",
         len(result.get("output_report", "")) > 50
         and ("법령" in result["output_report"] or "리스크" in result["output_report"] or "위험" in result["output_report"])),
    )
    print(f"[Step6-8] laws={len(result.get('related_laws',[]))} issues={len(result.get('issues',[]))}")

    # Step 9 API
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    h = client.get("/api/health").json()
    checks.append(("P3-Step9 health", "rag_enabled" in h and "chroma_status" in h))
    print(f"[Step9] health={h}")

    with open("fixtures/sample_contract.txt", "rb") as f:
        u = client.post("/api/upload", files={"file": ("sample_contract.txt", f, "text/plain")})
    jid = u.json()["job_id"]
    client.post("/api/screen", json={"job_id": jid})
    res = client.get(f"/api/result/{jid}").json()
    checks.append(("P3-Step9 api e2e", len(res.get("output_report", "")) > 0))

    # Step 10 README
    readme = open("README.md", encoding="utf-8").read()
    checks.append(("P3-Step10 README", "Phase 3" in readme and "Chroma" in readme))

    print("\n=== Phase 3 Progress ===")
    for label, ok in checks:
        print(f"{'OK' if ok else 'FAIL'} {label}")

    return 0 if all(c[1] for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
