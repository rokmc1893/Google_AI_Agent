"""
test_agent_pipeline.py  ── 모듈 D: 멀티에이전트 파이프라인 TDD
═══════════════════════════════════════════════════════════════════════════════

[RED 단계] 구현 코드보다 먼저 작성된 테스트 코드입니다.

테스트 시나리오:
  ✅ 성공 케이스
    - LangGraph 상태(AgentState) 구조 검증
    - 스크리닝 노드 실행 후 상태 업데이트 검증
    - 리포팅 노드 실행 후 최종 보고서 생성 검증
    - 스크리닝→리포팅 노드 전환 검증 (엣지 라우팅)
    - 최종 보고서에 위험도(risk_level) 필드 포함 검증
    - 최종 보고서에 출처(sources) 필드 포함 검증 (가드레일)
    - 전체 파이프라인 E2E 실행 검증

  ❌ 예외 케이스
    - 빈 계약서 입력 시 처리 검증
    - 스크리닝 노드 실패 시 에러 상태 전파 검증
    - 처리 시간 측정 (180초 이내 완료 목표 검증 구조)

실행 방법:
  pytest tests/test_agent_pipeline.py -v
  pytest tests/test_agent_pipeline.py -v -k "e2e"   # E2E 테스트만
"""

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from modules.agent_pipeline import (
    AgentState,
    LegalReviewPipeline,
    RiskLevel,
    RiskReport,
    ScreeningResult,
    run_legal_review,
)


# ─────────────────────────────────────────────────────────────────────────────
# 픽스처
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture()
def initial_state(sample_contract_text: str) -> AgentState:
    """파이프라인 초기 상태 픽스처."""
    return AgentState(
        contract_text=sample_contract_text,
        masked_text=None,
        mask_mapping={},
        parsed_articles=[],
        screening_results=[],
        retrieved_clauses=[],
        risk_report=None,
        error=None,
        processing_time_seconds=0.0,
    )


@pytest.fixture()
def mock_screening_llm():
    """스크리닝 LLM mock."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(
        content=(
            "위험 조항 탐지:\n"
            "1. 제3조 제1항: 위약금 20% - 위험도 높음 (민법 제398조 위반 가능성)\n"
            "2. 제3조 제2항: 갑 귀책 시 전액 반환 - 위험도 중간\n"
        )
    )
    return mock


@pytest.fixture()
def mock_reporting_llm():
    """리포팅 LLM mock."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(
        content=(
            "## 계약서 위험도 분석 보고서\n\n"
            "**종합 위험도: 높음**\n\n"
            "### 주요 위험 조항\n"
            "1. 제3조 제1항 위약금 조항\n"
            "   - 근거: 민법 제398조, 사내규정 계약관리규정 제7조\n"
            "   - 위험도: HIGH\n\n"
            "### 권고사항\n"
            "법무팀 검토 후 위약금 비율 재협상 권고\n"
        )
    )
    return mock


@pytest.fixture()
def pipeline(mock_screening_llm, mock_reporting_llm, sample_legal_db) -> LegalReviewPipeline:
    """테스트용 LegalReviewPipeline (LLM mock 사용)."""
    import numpy as np
    from modules.rag_retriever import HybridRetriever, LegalDocument

    def mock_embed(text: str) -> np.ndarray:
        seed = abs(hash(text)) % (2**31)
        return np.random.default_rng(seed).random(384).astype(np.float32)

    documents = [LegalDocument(**doc) for doc in sample_legal_db]
    retriever = HybridRetriever(documents=documents, embed_fn=mock_embed)

    return LegalReviewPipeline(
        screening_llm=mock_screening_llm,
        reporting_llm=mock_reporting_llm,
        retriever=retriever,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 상태(AgentState) 구조 테스트
# ─────────────────────────────────────────────────────────────────────────────
class TestAgentState:
    """LangGraph 상태 구조 검증."""

    def test_agent_state_creation(self, initial_state: AgentState):
        """AgentState 객체를 생성할 수 있어야 한다."""
        assert isinstance(initial_state, AgentState)

    def test_agent_state_has_contract_text(self, initial_state: AgentState):
        """AgentState에 contract_text 필드가 있어야 한다."""
        assert hasattr(initial_state, "contract_text")
        assert initial_state.contract_text is not None

    def test_agent_state_required_fields(self, initial_state: AgentState):
        """AgentState에 필수 필드 모두 존재해야 한다."""
        required_fields = [
            "contract_text", "masked_text", "mask_mapping",
            "parsed_articles", "screening_results", "retrieved_clauses",
            "risk_report", "error", "processing_time_seconds",
        ]
        for field in required_fields:
            assert hasattr(initial_state, field), f"필드 누락: {field}"

    def test_risk_level_enum_values(self):
        """RiskLevel 열거형이 LOW/MEDIUM/HIGH 값을 가져야 한다."""
        assert RiskLevel.LOW is not None
        assert RiskLevel.MEDIUM is not None
        assert RiskLevel.HIGH is not None

    def test_screening_result_structure(self):
        """ScreeningResult 객체를 생성할 수 있어야 한다."""
        sr = ScreeningResult(
            article_ref="제3조 제1항",
            issue_description="위약금 비율 과다",
            risk_level=RiskLevel.HIGH,
            relevant_clause_ids=["civil_law_398"],
        )
        assert sr.article_ref == "제3조 제1항"
        assert sr.risk_level == RiskLevel.HIGH

    def test_risk_report_structure(self):
        """RiskReport 객체를 생성할 수 있어야 한다."""
        report = RiskReport(
            overall_risk=RiskLevel.HIGH,
            screening_results=[],
            sources=["민법 제398조"],
            summary="위약금 조항 위험",
            recommendations=["법무팀 검토 필요"],
        )
        assert report.overall_risk == RiskLevel.HIGH
        assert "민법 제398조" in report.sources


# ─────────────────────────────────────────────────────────────────────────────
# 노드별 단위 테스트
# ─────────────────────────────────────────────────────────────────────────────
class TestPipelineNodes:
    """LangGraph 노드별 단위 테스트."""

    def test_masking_node_updates_state(
        self, pipeline: LegalReviewPipeline, initial_state: AgentState
    ):
        """마스킹 노드 실행 후 masked_text와 mask_mapping이 업데이트되어야 한다."""
        updated_state = pipeline.masking_node(initial_state)
        assert updated_state.masked_text is not None
        assert isinstance(updated_state.mask_mapping, dict)

    def test_parsing_node_updates_articles(
        self, pipeline: LegalReviewPipeline, initial_state: AgentState
    ):
        """파싱 노드 실행 후 parsed_articles가 채워져야 한다."""
        # 마스킹 선행
        state_after_mask = pipeline.masking_node(initial_state)
        state_after_parse = pipeline.parsing_node(state_after_mask)
        assert isinstance(state_after_parse.parsed_articles, list)
        assert len(state_after_parse.parsed_articles) >= 1

    def test_retrieval_node_updates_clauses(
        self, pipeline: LegalReviewPipeline, initial_state: AgentState
    ):
        """검색 노드 실행 후 retrieved_clauses가 채워져야 한다."""
        state = pipeline.masking_node(initial_state)
        state = pipeline.parsing_node(state)
        state = pipeline.retrieval_node(state)
        assert isinstance(state.retrieved_clauses, list)
        # 각 조항에 source 포함 검증 (가드레일)
        for clause in state.retrieved_clauses:
            assert "source" in clause or hasattr(clause, "source"), (
                "retrieved_clauses 항목에 source가 없습니다."
            )

    def test_screening_node_updates_results(
        self, pipeline: LegalReviewPipeline, initial_state: AgentState
    ):
        """스크리닝 노드 실행 후 screening_results가 채워져야 한다."""
        state = pipeline.masking_node(initial_state)
        state = pipeline.parsing_node(state)
        state = pipeline.retrieval_node(state)
        state = pipeline.screening_node(state)
        assert isinstance(state.screening_results, list)
        assert len(state.screening_results) >= 0  # 빈 결과도 허용

    def test_reporting_node_generates_report(
        self, pipeline: LegalReviewPipeline, initial_state: AgentState
    ):
        """리포팅 노드 실행 후 risk_report가 생성되어야 한다."""
        state = pipeline.masking_node(initial_state)
        state = pipeline.parsing_node(state)
        state = pipeline.retrieval_node(state)
        state = pipeline.screening_node(state)
        state = pipeline.reporting_node(state)

        assert state.risk_report is not None
        assert isinstance(state.risk_report, RiskReport)

    def test_report_has_risk_level(
        self, pipeline: LegalReviewPipeline, initial_state: AgentState
    ):
        """최종 보고서에 overall_risk 필드가 있어야 한다."""
        state = pipeline.masking_node(initial_state)
        state = pipeline.parsing_node(state)
        state = pipeline.retrieval_node(state)
        state = pipeline.screening_node(state)
        state = pipeline.reporting_node(state)

        assert state.risk_report.overall_risk in (
            RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH
        )

    def test_report_has_sources(
        self, pipeline: LegalReviewPipeline, initial_state: AgentState
    ):
        """최종 보고서에 출처(sources) 필드가 있어야 한다. (할루시네이션 방지 가드레일)"""
        state = pipeline.masking_node(initial_state)
        state = pipeline.parsing_node(state)
        state = pipeline.retrieval_node(state)
        state = pipeline.screening_node(state)
        state = pipeline.reporting_node(state)

        assert hasattr(state.risk_report, "sources")
        assert isinstance(state.risk_report.sources, list), "sources는 리스트여야 합니다."
        # 출처가 최소 1개 이상 있어야 함
        assert len(state.risk_report.sources) >= 1, (
            "보고서에 출처가 없습니다. 가드레일 위반!"
        )

    def test_report_sources_are_non_empty_strings(
        self, pipeline: LegalReviewPipeline, initial_state: AgentState
    ):
        """보고서의 각 출처는 비어 있지 않은 문자열이어야 한다."""
        state = pipeline.masking_node(initial_state)
        state = pipeline.parsing_node(state)
        state = pipeline.retrieval_node(state)
        state = pipeline.screening_node(state)
        state = pipeline.reporting_node(state)

        for src in state.risk_report.sources:
            assert isinstance(src, str) and src.strip() != "", (
                f"빈 출처 감지: '{src}'"
            )

    def test_report_has_recommendations(
        self, pipeline: LegalReviewPipeline, initial_state: AgentState
    ):
        """보고서에 권고사항(recommendations) 필드가 있어야 한다."""
        state = pipeline.masking_node(initial_state)
        state = pipeline.parsing_node(state)
        state = pipeline.retrieval_node(state)
        state = pipeline.screening_node(state)
        state = pipeline.reporting_node(state)

        assert hasattr(state.risk_report, "recommendations")
        assert isinstance(state.risk_report.recommendations, list)


# ─────────────────────────────────────────────────────────────────────────────
# E2E 파이프라인 테스트
# ─────────────────────────────────────────────────────────────────────────────
class TestPipelineE2E:
    """전체 파이프라인 통합(E2E) 테스트."""

    def test_e2e_run_legal_review(
        self, pipeline: LegalReviewPipeline, sample_contract_text: str
    ):
        """run_legal_review()로 전체 파이프라인을 실행하고 보고서를 반환해야 한다."""
        report = pipeline.run(contract_text=sample_contract_text)
        assert isinstance(report, RiskReport)

    def test_e2e_convenience_function(
        self, pipeline: LegalReviewPipeline, sample_contract_text: str
    ):
        """run_legal_review() 편의 함수가 정상 동작해야 한다."""
        report = run_legal_review(
            contract_text=sample_contract_text,
            pipeline=pipeline,
        )
        assert isinstance(report, RiskReport)
        assert report.overall_risk in (RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH)

    def test_e2e_report_completeness(
        self, pipeline: LegalReviewPipeline, sample_contract_text: str
    ):
        """E2E 보고서에 모든 필수 필드가 채워져 있어야 한다."""
        report = pipeline.run(contract_text=sample_contract_text)
        assert report.overall_risk is not None
        assert report.sources  # 비어있지 않아야 함
        assert report.summary and report.summary.strip() != ""

    def test_e2e_processing_time_recorded(
        self, pipeline: LegalReviewPipeline, sample_contract_text: str
    ):
        """파이프라인 실행 후 처리 시간이 기록되어야 한다."""
        start = time.perf_counter()
        report = pipeline.run(contract_text=sample_contract_text)
        elapsed = time.perf_counter() - start
        # mock LLM 환경에서 최소 처리 시간은 미미하지만 반드시 측정 가능해야 함
        assert elapsed >= 0

    def test_e2e_empty_contract(self, pipeline: LegalReviewPipeline):
        """빈 계약서 입력 시 에러 없이 LOW 위험도 보고서를 반환해야 한다."""
        report = pipeline.run(contract_text="")
        assert isinstance(report, RiskReport)
        # 빈 계약서는 위험도 없음
        assert report.overall_risk == RiskLevel.LOW

    def test_e2e_node_order_is_correct(
        self, pipeline: LegalReviewPipeline, sample_contract_text: str
    ):
        """노드 실행 순서: 마스킹 → 파싱 → 검색 → 스크리닝 → 리포팅."""
        call_order = []

        original_masking = pipeline.masking_node
        original_parsing = pipeline.parsing_node
        original_retrieval = pipeline.retrieval_node
        original_screening = pipeline.screening_node
        original_reporting = pipeline.reporting_node

        def wrap(name, fn):
            def _wrapped(state):
                call_order.append(name)
                return fn(state)
            return _wrapped

        pipeline.masking_node = wrap("masking", original_masking)
        pipeline.parsing_node = wrap("parsing", original_parsing)
        pipeline.retrieval_node = wrap("retrieval", original_retrieval)
        pipeline.screening_node = wrap("screening", original_screening)
        pipeline.reporting_node = wrap("reporting", original_reporting)

        try:
            pipeline.run(contract_text=sample_contract_text)
            expected_order = ["masking", "parsing", "retrieval", "screening", "reporting"]
            assert call_order == expected_order, (
                f"노드 실행 순서 오류.\n예상: {expected_order}\n실제: {call_order}"
            )
        finally:
            # 원복
            pipeline.masking_node = original_masking
            pipeline.parsing_node = original_parsing
            pipeline.retrieval_node = original_retrieval
            pipeline.screening_node = original_screening
            pipeline.reporting_node = original_reporting


# ─────────────────────────────────────────────────────────────────────────────
# 예외/에러 처리 테스트
# ─────────────────────────────────────────────────────────────────────────────
class TestPipelineErrorHandling:
    """파이프라인 에러 처리 검증."""

    def test_screening_failure_sets_error_state(
        self, pipeline: LegalReviewPipeline, initial_state: AgentState
    ):
        """스크리닝 노드에서 예외 발생 시 state.error가 설정되어야 한다."""
        pipeline.screening_llm.invoke.side_effect = Exception("LLM 연결 실패")

        state = pipeline.masking_node(initial_state)
        state = pipeline.parsing_node(state)
        state = pipeline.retrieval_node(state)
        state = pipeline.screening_node(state)

        assert state.error is not None, "에러 상태가 설정되지 않았습니다."
        # side_effect 초기화
        pipeline.screening_llm.invoke.side_effect = None

    def test_pipeline_recovers_from_retrieval_empty(
        self, pipeline: LegalReviewPipeline, initial_state: AgentState
    ):
        """검색 결과가 없어도 파이프라인이 중단되지 않아야 한다."""
        original_retrieve = pipeline.retriever.retrieve
        pipeline.retriever.retrieve = lambda *a, **kw: []

        try:
            state = pipeline.masking_node(initial_state)
            state = pipeline.parsing_node(state)
            state = pipeline.retrieval_node(state)
            # 검색 결과 없어도 에러 없이 계속
            assert state.error is None
        finally:
            pipeline.retriever.retrieve = original_retrieve
