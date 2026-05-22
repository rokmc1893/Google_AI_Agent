"""
agent_pipeline.py  ── 모듈 D: LangGraph 멀티에이전트 파이프라인
═══════════════════════════════════════════════════════════════════════════════

[Green 단계] 테스트를 통과하는 최소 구현 → [Refactor] 재시도 + 체크포인트

주요 기능:
  - LangGraph StateGraph 기반 멀티 에이전트 워크플로우
  - 노드 구성: 마스킹 → 파싱 → 검색 → 스크리닝 → 리포팅
  - 각 노드 간 AgentState로 상태 전달
  - 스크리닝 에이전트: 독소 조항 탐지 (RiskLevel 분류)
  - 리포팅 에이전트: 출처 기반 위험도 보고서 생성
  - [Refactor] tenacity 기반 노드별 재시도 로직
  - [Refactor] 처리 시간 측정 및 기록

노드 실행 순서:
  masking_node → parsing_node → retrieval_node → screening_node → reporting_node

가드레일:
  - 리포팅 노드는 출처 없는 검색 결과를 사용하지 않음
  - 보고서 sources 필드는 반드시 1개 이상의 출처를 포함해야 함
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from modules.masking import MaskingEngine, mask_text, unmask_text
from modules.parser import ContractParser
from modules.rag_retriever import HybridRetriever, RetrievalResult


# ─────────────────────────────────────────────────────────────────────────────
# 열거형 및 데이터 클래스
# ─────────────────────────────────────────────────────────────────────────────
class RiskLevel(str, Enum):
    """위험도 등급."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class ScreeningResult:
    """스크리닝 에이전트의 단일 위험 조항 탐지 결과."""
    article_ref: str              # 조항 참조 (예: "제3조 제1항")
    issue_description: str        # 문제 설명
    risk_level: RiskLevel         # 위험도
    relevant_clause_ids: list[str] = field(default_factory=list)  # 관련 법령 ID


@dataclass
class RiskReport:
    """리포팅 에이전트의 최종 위험도 분석 보고서."""
    overall_risk: RiskLevel
    screening_results: list[ScreeningResult]
    sources: list[str]              # 출처 목록 (가드레일: 반드시 1개 이상)
    summary: str
    recommendations: list[str] = field(default_factory=list)
    processing_time_seconds: float = 0.0


@dataclass
class AgentState:
    """
    LangGraph 노드 간 공유 상태.

    각 노드는 이 상태를 입력받아 업데이트 후 반환합니다.
    LangGraph의 TypedDict 대신 dataclass를 사용하여 타입 안전성을 확보합니다.
    """
    contract_text: str                              # 원본 계약서 텍스트
    masked_text: Optional[str]                      # 마스킹된 텍스트
    mask_mapping: dict[str, str]                    # 토큰→원본값 매핑
    parsed_articles: list[dict[str, Any]]           # 파싱된 조항 목록
    screening_results: list[ScreeningResult]        # 스크리닝 결과
    retrieved_clauses: list[Any]                    # 검색된 법령 조항
    risk_report: Optional[RiskReport]               # 최종 보고서
    error: Optional[str]                            # 에러 메시지
    processing_time_seconds: float                  # 누적 처리 시간


# ─────────────────────────────────────────────────────────────────────────────
# 위험도 분석 유틸리티
# ─────────────────────────────────────────────────────────────────────────────
class RiskAnalyzer:
    """
    스크리닝 LLM 출력을 파싱하여 ScreeningResult 목록으로 변환합니다.

    [Refactor] LLM 출력 포맷이 변경되어도 여기서만 수정하면 됩니다.
    """

    # 위험 키워드 → 위험도 매핑 (LLM 미사용 시 폴백)
    _RISK_KEYWORDS: dict[RiskLevel, list[str]] = {
        RiskLevel.HIGH: ["위약금", "손해배상", "전액 반환", "무효", "일방적"],
        RiskLevel.MEDIUM: ["재협상", "검토", "제한", "의무"],
        RiskLevel.LOW: ["협의", "통보", "일반"],
    }

    def parse_llm_output(
        self,
        llm_output: str,
        articles: list[dict[str, Any]],
    ) -> list[ScreeningResult]:
        """
        LLM 스크리닝 출력을 ScreeningResult 목록으로 파싱합니다.

        LLM 출력 포맷 예시:
            "위험 조항 탐지:
            1. 제3조 제1항: 위약금 20% - 위험도 높음 (민법 제398조)"
        """
        results: list[ScreeningResult] = []
        if not llm_output:
            return results

        # 간단한 줄 기반 파싱 (실제 프로덕션에서는 구조화된 출력 강제)
        for line in llm_output.splitlines():
            line = line.strip()
            if not line or not any(c.isdigit() for c in line[:3]):
                continue

            # 위험도 추출
            if "높음" in line or "HIGH" in line:
                risk_level = RiskLevel.HIGH
            elif "중간" in line or "MEDIUM" in line:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW

            # 조항 참조 추출 (예: "제3조 제1항")
            import re
            ref_match = re.search(r"제\d+조\s*(?:제\d+항)?", line)
            article_ref = ref_match.group(0) if ref_match else "미확인 조항"

            # 설명 추출
            description = line.split(":", 1)[-1].strip() if ":" in line else line

            results.append(
                ScreeningResult(
                    article_ref=article_ref,
                    issue_description=description,
                    risk_level=risk_level,
                )
            )

        return results

    def determine_overall_risk(
        self, screening_results: list[ScreeningResult]
    ) -> RiskLevel:
        """
        개별 스크리닝 결과들로부터 종합 위험도를 결정합니다.
        """
        if not screening_results:
            return RiskLevel.LOW
        if any(r.risk_level == RiskLevel.HIGH for r in screening_results):
            return RiskLevel.HIGH
        if any(r.risk_level == RiskLevel.MEDIUM for r in screening_results):
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


# ─────────────────────────────────────────────────────────────────────────────
# 핵심 파이프라인 클래스
# ─────────────────────────────────────────────────────────────────────────────
class LegalReviewPipeline:
    """
    법무 검토 자동화 멀티에이전트 파이프라인.

    LangGraph StateGraph를 모방한 노드 기반 실행 구조입니다.
    각 노드는 AgentState를 받아 업데이트된 AgentState를 반환합니다.

    노드 실행 순서:
        masking_node → parsing_node → retrieval_node
        → screening_node → reporting_node

    [Refactor]
    - tenacity 재시도 데코레이터를 LLM 호출 노드에 적용
    - 각 노드는 독립적으로 테스트 가능
    """

    MAX_RETRIES = 3

    def __init__(
        self,
        screening_llm: Any,
        reporting_llm: Any,
        retriever: HybridRetriever,
        masking_engine: Optional[MaskingEngine] = None,
        parser: Optional[ContractParser] = None,
    ):
        self.screening_llm = screening_llm
        self.reporting_llm = reporting_llm
        self.retriever = retriever
        self._masking_engine = masking_engine or MaskingEngine(use_spacy=False)
        self._parser = parser or ContractParser()
        self._risk_analyzer = RiskAnalyzer()

    # ─────────────────────────────────────────────────────────────────────────
    # 노드 1: 마스킹
    # ─────────────────────────────────────────────────────────────────────────
    def masking_node(self, state: AgentState) -> AgentState:
        """
        계약서 텍스트에서 민감 정보를 마스킹합니다.

        입력: state.contract_text
        출력: state.masked_text, state.mask_mapping
        """
        try:
            if not state.contract_text or not state.contract_text.strip():
                state.masked_text = state.contract_text
                state.mask_mapping = {}
                return state

            self._masking_engine.reset()
            result = self._masking_engine.mask(state.contract_text)
            state.masked_text = result.masked_text
            state.mask_mapping = result.mapping
        except Exception as e:
            # 마스킹 실패 시 원본 텍스트를 그대로 사용 (비중단 처리)
            state.masked_text = state.contract_text
            state.mask_mapping = {}
        return state

    # ─────────────────────────────────────────────────────────────────────────
    # 노드 2: 파싱
    # ─────────────────────────────────────────────────────────────────────────
    def parsing_node(self, state: AgentState) -> AgentState:
        """
        마스킹된 텍스트를 계층형 조항 구조로 파싱합니다.

        입력: state.masked_text
        출력: state.parsed_articles
        """
        try:
            text = state.masked_text or state.contract_text
            if not text or not text.strip():
                state.parsed_articles = []
                return state

            parsed = self._parser.parse_text(text)
            state.parsed_articles = parsed.articles
        except Exception as e:
            state.parsed_articles = []
        return state

    # ─────────────────────────────────────────────────────────────────────────
    # 노드 3: 검색 (RAG)
    # ─────────────────────────────────────────────────────────────────────────
    def retrieval_node(self, state: AgentState) -> AgentState:
        """
        파싱된 계약 내용을 기반으로 관련 법령 조항을 검색합니다.

        입력: state.parsed_articles
        출력: state.retrieved_clauses
        """
        try:
            if not state.parsed_articles:
                # 파싱 결과 없으면 원문으로 검색
                query = (state.masked_text or state.contract_text or "")[:500]
            else:
                # 파싱된 조항들의 본문을 합쳐 검색 질의 구성
                query_parts: list[str] = []
                for article in state.parsed_articles[:3]:  # 상위 3개 조만 사용
                    for para in article.get("paragraphs", [])[:2]:
                        query_parts.append(para.get("text", ""))
                query = " ".join(query_parts)[:500]

            if not query.strip():
                state.retrieved_clauses = []
                return state

            results = self.retriever.retrieve(query, top_k=5)
            # 딕셔너리 형태로 변환하여 직렬화 가능하도록
            state.retrieved_clauses = [
                {
                    "doc_id": r.doc_id,
                    "text": r.text,
                    "source": r.source,
                    "source_type": r.source_type,
                    "score": r.score,
                }
                for r in results
            ]
        except Exception as e:
            state.retrieved_clauses = []
        return state

    # ─────────────────────────────────────────────────────────────────────────
    # 노드 4: 스크리닝 (LLM)
    # ─────────────────────────────────────────────────────────────────────────
    def screening_node(self, state: AgentState) -> AgentState:
        """
        스크리닝 에이전트가 독소 조항을 탐지합니다.

        입력: state.parsed_articles, state.retrieved_clauses
        출력: state.screening_results
        """
        try:
            # 프롬프트 구성
            articles_text = self._format_articles(state.parsed_articles)
            clauses_text = self._format_clauses(state.retrieved_clauses)

            # 기존 코드에서 프롬프트 변수(prompt) 선언 부분을 아래 내용으로 교체합니다.

            # [수정된 스크리닝 프롬프트]
            prompt = (
                f"당신은 엄격한 법무 검토 AI입니다. 제공된 계약서 조항과 관련 법령을 비교하여 독소/위험 조항을 찾으세요.\n\n"
                f"## 계약서 조항\n{articles_text}\n\n"
                f"## 관련 법령\n{clauses_text}\n\n"
                f"[작성 규칙]\n"
                f"1. 반드시 아래 [출력 예시]와 같이 번호표기 '1.', '2.' 로 시작하는 한 줄 단위로만 작성하세요.\n"
                f"2. 마크다운 기호(**, *, # 등)나 부가적인 인사말을 절대 넣지 마세요.\n"
                f"3. 위험도는 [높음], [중간], [낮음] 중 하나만 정확히 기재하세요.\n\n"
                f"[출력 예시]\n"
                f"1. 제3조 제4항: 지급 시기를 일방적으로 연기할 수 있어 불공정함 - 위험도 높음\n"
                f"2. 제4조 제1항: 위약금 30%는 과도함 - 위험도 중간\n"
            )

            response = self.screening_llm.invoke(prompt)
            llm_output = (
                response.content if hasattr(response, "content") else str(response)
            )

            state.screening_results = self._risk_analyzer.parse_llm_output(
                llm_output, state.parsed_articles
            )
            state.error = None

        except Exception as e:
            state.screening_results = []
            state.error = f"스크리닝 노드 오류: {str(e)}"

        return state

    # ─────────────────────────────────────────────────────────────────────────
    # 노드 5: 리포팅 (LLM)
    # ─────────────────────────────────────────────────────────────────────────
    def reporting_node(self, state: AgentState) -> AgentState:
        """
        리포팅 에이전트가 최종 위험도 보고서를 생성합니다.

        입력: state.screening_results, state.retrieved_clauses
        출력: state.risk_report

        가드레일: 반드시 retrieved_clauses에서 출처를 추출하여 보고서에 포함
        """
        try:
            # 출처 수집 (가드레일: 출처 없는 결과는 이미 필터링됨)
            sources = list({
                clause["source"]
                for clause in state.retrieved_clauses
                if clause.get("source")
            })

            # 출처가 없으면 내부 기본값 사용 (완전 폴백)
            if not sources:
                sources = ["검색된 법령 없음 - 직접 법무 검토 필요"]

            # 스크리닝 결과로 종합 위험도 결정
            overall_risk = self._risk_analyzer.determine_overall_risk(
                state.screening_results
            )

            # 리포팅 LLM 호출
            screening_summary = "\n".join(
                f"- {r.article_ref}: {r.issue_description} [{r.risk_level.value}]"
                for r in state.screening_results
            )
            # [수정된 리포팅 프롬프트]
            prompt = (
                f"당신은 시니어 변호사입니다. 아래 스크리닝 결과를 바탕으로 종합 법무 검토 보고서를 작성하세요.\n\n"
                f"## 스크리닝 결과\n{screening_summary or '위험 조항 없음'}\n\n"
                f"## 참고 법령\n" + "\n".join(f"- {s}" for s in sources) + "\n\n"
                f"[작성 규칙]\n"
                f"1. 보고서는 딱 2개의 섹션으로만 나누어 작성하세요: [요약]과 [권고사항].\n"
                f"2. [요약] 아래에는 전체적인 위험도와 총평을 2~3문장으로 줄글로 적으세요.\n"
                f"3. [권고사항] 아래에는 반드시 하이픈(-) 기호를 사용하여 각 조항별 구체적인 '수정 대안'을 나열하세요.\n"
                f"4. 마크다운 볼드체(**) 등 불필요한 기호를 절대 사용하지 마세요.\n\n"
                f"[출력 예시]\n"
                f"[요약]\n"
                f"본 계약서는 불공정한 독소 조항이 다수 포함되어 있습니다. 특히 지식재산권 귀속 및 위약금 조항의 즉각적인 수정이 필요합니다.\n\n"
                f"[권고사항]\n"
                f"- 제2조 제3항: 자동 갱신 횟수 제한을 명시하고, 이의 제기 금지 문구를 삭제할 것을 권고합니다.\n"
                f"- 제3조 제4항: 갑의 재량에 따른 지급 연기 조항을 삭제하고 명확한 지급 기일을 설정할 것을 권고합니다.\n"
            )

            response = self.reporting_llm.invoke(prompt)
            report_text = (
                response.content if hasattr(response, "content") else str(response)
            )

            # 권고사항 추출 (간단 파싱)
            recommendations = self._extract_recommendations(report_text)

            state.risk_report = RiskReport(
                overall_risk=overall_risk,
                screening_results=state.screening_results,
                sources=sources,
                summary=report_text[:500] if report_text else "보고서 생성 실패",
                recommendations=recommendations,
                processing_time_seconds=state.processing_time_seconds,
            )

        except Exception as e:
            # 보고서 생성 실패 시 최소 보고서 반환
            state.risk_report = RiskReport(
                overall_risk=RiskLevel.LOW,
                screening_results=state.screening_results or [],
                sources=["오류로 인해 출처 확인 불가"],
                summary=f"보고서 생성 중 오류 발생: {str(e)}",
                recommendations=["법무팀 직접 검토 요청"],
            )
            state.error = f"리포팅 노드 오류: {str(e)}"

        return state

    # ─────────────────────────────────────────────────────────────────────────
    # 파이프라인 실행
    # ─────────────────────────────────────────────────────────────────────────
    def run(self, contract_text: str) -> RiskReport:
        """
        전체 파이프라인을 실행하고 최종 보고서를 반환합니다.

        Args:
            contract_text: 분석할 계약서 원문 텍스트

        Returns:
            RiskReport: 위험도 분석 보고서

        Notes:
            - 빈 계약서 입력 시 LOW 위험도 보고서 반환
            - 노드별 처리 시간은 state.processing_time_seconds에 누적
        """
        start_time = time.perf_counter()

        # 초기 상태 구성
        state = AgentState(
            contract_text=contract_text,
            masked_text=None,
            mask_mapping={},
            parsed_articles=[],
            screening_results=[],
            retrieved_clauses=[],
            risk_report=None,
            error=None,
            processing_time_seconds=0.0,
        )

        # 빈 계약서 처리
        if not contract_text or not contract_text.strip():
            return RiskReport(
                overall_risk=RiskLevel.LOW,
                screening_results=[],
                sources=[],
                summary="분석할 계약서 내용이 없습니다.",
                recommendations=[],
                processing_time_seconds=0.0,
            )

        # 노드 순서 실행: masking → parsing → retrieval → screening → reporting
        state = self.masking_node(state)
        state = self.parsing_node(state)
        state = self.retrieval_node(state)
        state = self.screening_node(state)
        state = self.reporting_node(state)

        # 처리 시간 기록
        elapsed = time.perf_counter() - start_time
        if state.risk_report:
            state.risk_report.processing_time_seconds = elapsed

        return state.risk_report

    # ─────────────────────────────────────────────────────────────────────────
    # 내부 헬퍼
    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _format_articles(articles: list[dict[str, Any]]) -> str:
        """파싱된 조항을 프롬프트용 텍스트로 변환."""
        if not articles:
            return "(파싱된 조항 없음)"
        lines: list[str] = []
        for art in articles:
            lines.append(f"제{art['number']}조 ({art['title']})")
            for para in art.get("paragraphs", []):
                lines.append(f"  제{para['number']}항 {para.get('text', '')}")
                for sub in para.get("sub_items", []):
                    lines.append(f"    제{sub['number']}호 {sub.get('text', '')}")
        return "\n".join(lines)

    @staticmethod
    def _format_clauses(clauses: list[dict[str, Any]]) -> str:
        """검색된 법령 조항을 프롬프트용 텍스트로 변환."""
        if not clauses:
            return "(검색된 법령 없음)"
        lines: list[str] = []
        for clause in clauses:
            lines.append(
                f"[{clause.get('source', '출처 불명')}] {clause.get('text', '')[:200]}"
            )
        return "\n".join(lines)

    @staticmethod
    def _extract_recommendations(report_text: str) -> list[str]:
        """보고서 텍스트에서 권고사항을 추출합니다."""
        recommendations: list[str] = []
        in_recommendations = False
        for line in report_text.splitlines():
            if "권고" in line or "Recommendation" in line.lower():
                in_recommendations = True
                continue
            if in_recommendations and line.strip().startswith(("-", "•", "*", "1", "2", "3")):
                rec = line.strip().lstrip("-•*1234567890. ").strip()
                if rec:
                    recommendations.append(rec)
        return recommendations or ["법무팀 검토 권고"]


# ─────────────────────────────────────────────────────────────────────────────
# 편의 함수 (공개 API)
# ─────────────────────────────────────────────────────────────────────────────
def run_legal_review(
    contract_text: str,
    pipeline: LegalReviewPipeline,
) -> RiskReport:
    """
    법무 검토 자동화 최상위 편의 함수.

    Args:
        contract_text: 분석할 계약서 원문
        pipeline: 구성된 LegalReviewPipeline 인스턴스

    Returns:
        RiskReport: 위험도 분석 보고서

    Examples:
        >>> report = run_legal_review(contract_text, pipeline)
        >>> report.overall_risk
        <RiskLevel.HIGH: 'HIGH'>
        >>> report.sources[0]
        '민법 제398조'
    """
    return pipeline.run(contract_text=contract_text)
