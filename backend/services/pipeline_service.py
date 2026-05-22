from __future__ import annotations

from typing import Any

from backend.agent_graph import LegalScreeningPipeline
from backend.api.schemas import RetrievedDoc, RiskIssue, ScreeningResult


def _map_risk_level(level: str) -> str:
    upper = (level or "MEDIUM").upper()
    if upper in ("HIGH", "MEDIUM", "LOW"):
        return upper
    return "MEDIUM"


def _issue_from_dict(item: dict[str, Any]) -> RiskIssue:
    citations: list[str] = []
    if item.get("legal_basis"):
        citations.append(str(item["legal_basis"]))
    return RiskIssue(
        id=str(item.get("id", "")),
        title=str(item.get("title", "")),
        clause_text=str(item.get("clause_text", "")),
        risk_level=_map_risk_level(str(item.get("risk_level", "MEDIUM"))),
        description=str(item.get("description", "")),
        legal_basis=item.get("legal_basis"),
        legal_basis_text=item.get("legal_basis_text"),
        citations=citations,
    )


def _doc_from_dict(doc: dict[str, Any]) -> RetrievedDoc:
    return RetrievedDoc(
        id=str(doc.get("id", "")),
        category=str(doc.get("category", "")),
        clause=str(doc.get("clause", "")),
        content=str(doc.get("content", "")),
    )


def map_state_to_screening_result(job_id: str, state: dict[str, Any]) -> ScreeningResult:
    issues = [_issue_from_dict(i) for i in state.get("issues", [])]
    verified = [_issue_from_dict(i) for i in state.get("verified_issues", [])]
    docs = [_doc_from_dict(d) for d in state.get("retrieved_docs", [])]

    high = sum(1 for i in verified if i.risk_level == "HIGH")
    medium = sum(1 for i in verified if i.risk_level == "MEDIUM")
    low = sum(1 for i in verified if i.risk_level == "LOW")

    # 간단 안전 점수: HIGH -20, MEDIUM -10, LOW -5 (최소 0)
    penalty = high * 20 + medium * 10 + low * 5
    safety_score = max(0, min(100, 100 - penalty))

    return ScreeningResult(
        job_id=job_id,
        status="completed",
        issues=issues,
        verified_issues=verified,
        retrieved_docs=docs,
        output_report=state.get("output_report", ""),
        output_email=state.get("output_email", ""),
        contract_masked=state.get("contract_masked"),
        high_risk_count=high,
        medium_risk_count=medium,
        low_risk_count=low,
        safety_score=safety_score,
    )


def run_screening(job_id: str, contract_text: str) -> ScreeningResult:
    pipeline = LegalScreeningPipeline()
    state = pipeline.run(contract_text)
    return map_state_to_screening_result(job_id, state)
