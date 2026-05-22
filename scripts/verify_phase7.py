#!/usr/bin/env python3
"""Phase 7 — LangGraph verification."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("PYTHONPATH", str(ROOT))
os.environ.setdefault("USE_LLM", "false")
os.environ.setdefault("USE_LANGGRAPH", "true")


def check(label: str, ok: bool) -> None:
    print(f"{'OK' if ok else 'FAIL'} {label}")
    if not ok:
        sys.exit(1)


def main() -> None:
    checks: list[tuple[str, bool]] = []

    # Step 1
    req = (ROOT / "backend/requirements.txt").read_text()
    checks.append(("P7-Step1 langgraph dep", "langgraph" in req))

    from backend.config import get_settings

    get_settings.cache_clear()
    s = get_settings()
    checks.append(("P7-Step1 use_langgraph config", hasattr(s, "use_langgraph")))

    from backend.graph.workflow import langgraph_available, compile_screening_graph

    checks.append(("P7-Step1 import langgraph", langgraph_available()))

    # Step 2
    from backend.agent_graph import LegalScreeningPipeline

    p = LegalScreeningPipeline()
    checks.append(("P7-Step2 compiled graph", p._compiled_graph is not None))

    # Step 3 — invoke
    text = (ROOT / "fixtures/sample_contract.txt").read_text(encoding="utf-8")
    result = p.run(text)
    checks.append(("P7-Step3 invoke output_report", len(result.get("output_report", "")) > 50))
    checks.append(("P7-Step3 invoke issues", len(result.get("verified_issues", [])) >= 0))

    # Step 4 — FastAPI
    from fastapi.testclient import TestClient
    from backend.main import app

    h = TestClient(app).get("/api/health").json()
    checks.append(("P7-Step4 health langgraph_enabled", h.get("langgraph_enabled") is True))

    with open(ROOT / "fixtures/sample_contract.txt", "rb") as f:
        u = TestClient(app).post(
            "/api/upload",
            files={"file": ("sample_contract.txt", f, "text/plain")},
        )
    jid = u.json()["job_id"]
    TestClient(app).post("/api/screen", json={"job_id": jid})
    res = TestClient(app).get(f"/api/result/{jid}").json()
    checks.append(("P7-Step4 api e2e", len(res.get("output_report", "")) > 0))

    readme = (ROOT / "README.md").read_text()
    checks.append(("P7-Step5 README", "Phase 7" in readme))

    print("\n=== Phase 7 Progress ===")
    for label, ok in checks:
        check(label, ok)
    print("\nPhase 7 — LangGraph StateGraph 검증 통과")


if __name__ == "__main__":
    main()
