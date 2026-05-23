from __future__ import annotations

from functools import lru_cache
from collections.abc import Mapping
from typing import cast

from backend.agent_graph import LegalScreeningPipeline
from backend.api.schemas import RetrievedDoc, RiskIssue, RiskLevel, ScreeningResult


@lru_cache(maxsize=1)
def get_screening_pipeline() -> LegalScreeningPipeline:
    # LangGraph 컴파일과 임베딩/RAG 모델 로딩은 요청마다 반복하면 수 초~수십 초 지연을 유발한다.
    # 프로세스당 파이프라인 인스턴스를 한 번만 올려두면 이후 요청은 워크플로 실행만 하면 된다.
    return LegalScreeningPipeline()


def _map_risk_level(level: str) -> RiskLevel:
    upper = (level or "MEDIUM").upper()
    if upper in ("HIGH", "MEDIUM", "LOW"):
        return upper
    return "MEDIUM"


def _as_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _build_recommendation(item: Mapping[str, object]) -> str:
    explicit = _as_optional_str(item.get("recommendation"))
    if explicit:
        return explicit

    replacement = _as_optional_str(
        item.get("replacement_clause") or item.get("suggested_clause")
    )
    if replacement:
        return "아래 대체 조항을 기준으로 수정을 검토하세요."

    legal_basis = _as_optional_str(item.get("legal_basis") or item.get("legal_reference"))
    if legal_basis:
        return f"관련 법령({legal_basis})에 맞게 조항을 조정하세요."

    return "법무팀 검토 후 수정안을 확정하세요."


def _issue_from_dict(item: Mapping[str, object]) -> RiskIssue:
    citations: list[str] = []
    if item.get("legal_basis"):
        citations.append(str(item["legal_basis"]))
    replacement_clause = _as_optional_str(
        item.get("replacement_clause") or item.get("suggested_clause")
    )
    return RiskIssue(
        id=str(item.get("id", "")),
        title=str(item.get("title", "")),
        clause_text=str(item.get("clause_text", "")),
        risk_level=_map_risk_level(str(item.get("risk_level", "MEDIUM"))),
        description=str(item.get("description", "")),
        recommendation=_build_recommendation(item),
        replacement_clause=replacement_clause,
        legal_basis=_as_optional_str(item.get("legal_basis") or item.get("legal_reference")),
        legal_basis_text=_as_optional_str(item.get("legal_basis_text")),
        citations=citations,
    )


def _doc_from_dict(doc: Mapping[str, object]) -> RetrievedDoc:
    return RetrievedDoc(
        id=str(doc.get("id", "")),
        category=str(doc.get("category", "")),
        clause=str(doc.get("clause", "")),
        content=str(doc.get("content", "")),
    )


def _mapping_items(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    items = cast(list[object], value)
    return [cast(Mapping[str, object], item) for item in items if isinstance(item, dict)]


def map_state_to_screening_result(
    job_id: str,
    state: Mapping[str, object],
    full_text: str = "",
) -> ScreeningResult:
    issues = [_issue_from_dict(i) for i in _mapping_items(state.get("issues"))]
    verified = [_issue_from_dict(i) for i in _mapping_items(state.get("verified_issues"))]
    docs = [_doc_from_dict(d) for d in _mapping_items(state.get("retrieved_docs"))]
    contract_text = str(state.get("contract_parsed") or full_text or state.get("contract_raw", ""))
    masked_text = _as_optional_str(state.get("contract_masked"))

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
        output_report=str(state.get("output_report") or ""),
        output_email=str(state.get("output_email") or ""),
        full_text=contract_text,
        masked_text=masked_text,
        contract_masked=masked_text,
        high_risk_count=high,
        medium_risk_count=medium,
        low_risk_count=low,
        safety_score=safety_score,
    )


def run_screening(job_id: str, contract_text: str) -> ScreeningResult:
    pipeline = get_screening_pipeline()
    state = pipeline.run(contract_text)
    return map_state_to_screening_result(job_id, state, contract_text)
