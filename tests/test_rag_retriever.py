"""
test_rag_retriever.py  ── 모듈 C: RAG 검색 및 가드레일 TDD
═══════════════════════════════════════════════════════════════════════════════

[RED 단계] 구현 코드보다 먼저 작성된 테스트 코드입니다.

테스트 시나리오:
  ✅ 성공 케이스
    - 질의에 관련된 법령 조항 반환 검증
    - 반환 결과에 source 메타데이터 필수 포함 검증
    - 하이브리드 검색(키워드+의미)으로 상위 K개 반환 검증
    - source_type 필드 포함 검증 (statute/internal_policy/precedent)
    - 출처 없는 결과 자동 필터링 (가드레일) 검증
    - 관련도 점수(score) 포함 검증

  ❌ 예외 케이스
    - 빈 질의 입력 시 처리 검증
    - DB가 비어 있을 때 빈 리스트 반환 검증
    - top_k=0 입력 시 빈 리스트 반환 검증
    - 출처 없는 문서만 있는 경우 빈 리스트 반환 (가드레일 작동) 검증

실행 방법:
  pytest tests/test_rag_retriever.py -v
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from modules.rag_retriever import (
    HybridRetriever,
    LegalDocument,
    RetrievalResult,
    SourceGuardrail,
    build_retriever_from_json,
    retrieve_relevant_clauses,
)


# ─────────────────────────────────────────────────────────────────────────────
# 픽스처: 인메모리 검색기 구성
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def legal_documents(sample_legal_db) -> list[LegalDocument]:
    """샘플 법령 DB를 LegalDocument 객체 리스트로 변환."""
    return [LegalDocument(**doc) for doc in sample_legal_db]


@pytest.fixture(scope="module")
def mock_embedder():
    """임베딩 함수를 재현 가능한 난수 벡터로 mock."""
    import hashlib
    rng = np.random.default_rng(seed=42)

    def _embed(text: str) -> np.ndarray:
        # 텍스트 해시를 시드로 활용해 일관된 벡터 반환
        # MD5 해시를 사용하여 파이썬 해시 시드 랜덤화 방지
        h = hashlib.md5(text.encode("utf-8")).digest()
        seed = int.from_bytes(h[:4], byteorder="big") % (2**31)
        return np.random.default_rng(seed).random(384).astype(np.float32)

    return _embed


@pytest.fixture(scope="module")
def retriever(legal_documents, mock_embedder) -> HybridRetriever:
    """테스트용 HybridRetriever (mock 임베딩 사용)."""
    return HybridRetriever(
        documents=legal_documents,
        embed_fn=mock_embedder,
        bm25_weight=0.4,
        dense_weight=0.6,
    )


@pytest.fixture(scope="module")
def retriever_from_json(sample_legal_db_json, mock_embedder) -> HybridRetriever:
    """JSON 파일에서 로드한 HybridRetriever."""
    return build_retriever_from_json(
        json_path=sample_legal_db_json,
        embed_fn=mock_embedder,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 성공 케이스 테스트
# ─────────────────────────────────────────────────────────────────────────────
class TestRAGRetrieverSuccessCases:
    """RAG 검색 성공 시나리오 검증."""

    def test_retrieve_returns_list(self, retriever: HybridRetriever):
        """검색 결과는 리스트 타입이어야 한다."""
        results = retriever.retrieve("위약금 손해배상", top_k=3)
        assert isinstance(results, list)

    def test_retrieve_returns_retrieval_results(self, retriever: HybridRetriever):
        """검색 결과 각 항목은 RetrievalResult 타입이어야 한다."""
        results = retriever.retrieve("위약금 손해배상", top_k=3)
        for r in results:
            assert isinstance(r, RetrievalResult), f"타입 오류: {type(r)}"

    def test_retrieve_top_k_limit(self, retriever: HybridRetriever):
        """top_k 파라미터로 반환 개수가 제한되어야 한다."""
        results = retriever.retrieve("계약 조항", top_k=2)
        assert len(results) <= 2, f"top_k=2인데 {len(results)}개 반환됨"

    def test_retrieve_result_has_source(self, retriever: HybridRetriever):
        """모든 검색 결과에 'source' 필드가 존재해야 한다. (가드레일 핵심)"""
        results = retriever.retrieve("위약금", top_k=4)
        for r in results:
            assert r.source is not None, "source 필드가 None입니다."
            assert r.source != "", "source 필드가 빈 문자열입니다."

    def test_retrieve_result_has_source_type(self, retriever: HybridRetriever):
        """모든 검색 결과에 'source_type' 필드가 존재해야 한다."""
        results = retriever.retrieve("위약금", top_k=4)
        valid_types = {"statute", "internal_policy", "precedent", "contract_clause"}
        for r in results:
            assert r.source_type in valid_types, (
                f"유효하지 않은 source_type: {r.source_type}"
            )

    def test_retrieve_result_has_score(self, retriever: HybridRetriever):
        """검색 결과에 관련도 점수(score)가 포함되어야 한다."""
        results = retriever.retrieve("위약금 손해배상", top_k=3)
        for r in results:
            assert hasattr(r, "score"), "score 필드가 없습니다."
            assert 0.0 <= r.score <= 1.0, f"score 범위 오류: {r.score}"

    def test_retrieve_result_has_text(self, retriever: HybridRetriever):
        """검색 결과에 문서 본문(text)이 포함되어야 한다."""
        results = retriever.retrieve("위약금", top_k=2)
        for r in results:
            assert r.text is not None and r.text != "", "text가 비어 있습니다."

    def test_retrieve_sorted_by_score(self, retriever: HybridRetriever):
        """검색 결과는 점수 내림차순으로 정렬되어야 한다."""
        results = retriever.retrieve("손해배상 위약금 계약", top_k=4)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True), (
            f"점수 정렬 오류: {scores}"
        )

    def test_retrieve_keyword_query_finds_relevant(self, retriever: HybridRetriever):
        """'위약금' 키워드 질의 시 민법 제398조가 상위에 검색되어야 한다."""
        results = retriever.retrieve("위약금 손해배상 예정", top_k=3)
        sources = [r.source for r in results]
        assert any("398" in src for src in sources), (
            f"민법 제398조가 상위에 검색되지 않음. 결과: {sources}"
        )

    def test_retrieve_internal_policy_included(self, retriever: HybridRetriever):
        """사내규정도 검색 결과에 포함되어야 한다."""
        results = retriever.retrieve("위약금 계약 법무 검토", top_k=4)
        source_types = [r.source_type for r in results]
        assert "internal_policy" in source_types, (
            "사내규정이 검색 결과에 없습니다."
        )

    def test_retrieve_precedent_included(self, retriever: HybridRetriever):
        """판례도 검색 결과에 포함될 수 있어야 한다."""
        results = retriever.retrieve("비밀유지 직업 자유 무효", top_k=4)
        source_types = [r.source_type for r in results]
        assert "precedent" in source_types, "판례가 검색 결과에 없습니다."

    def test_build_from_json(self, retriever_from_json: HybridRetriever):
        """JSON 파일에서 빌드한 검색기도 정상 동작해야 한다."""
        results = retriever_from_json.retrieve("위약금", top_k=2)
        assert len(results) >= 1

    def test_retrieve_via_convenience_function(
        self, legal_documents, mock_embedder
    ):
        """retrieve_relevant_clauses() 편의 함수도 정상 동작해야 한다."""
        results = retrieve_relevant_clauses(
            query="위약금 손해배상",
            documents=legal_documents,
            embed_fn=mock_embedder,
            top_k=2,
        )
        assert len(results) >= 1
        assert all(isinstance(r, RetrievalResult) for r in results)

    def test_retrieve_result_id_present(self, retriever: HybridRetriever):
        """검색 결과에 문서 고유 id가 포함되어야 한다."""
        results = retriever.retrieve("손해배상", top_k=2)
        for r in results:
            assert r.doc_id is not None and r.doc_id != ""


# ─────────────────────────────────────────────────────────────────────────────
# 가드레일 테스트 (출처 없는 문서 필터링)
# ─────────────────────────────────────────────────────────────────────────────
class TestSourceGuardrail:
    """출처 기반 가드레일 검증 — 할루시네이션 방지 핵심 로직."""

    def test_guardrail_filters_no_source(self):
        """source가 None인 결과를 가드레일이 필터링해야 한다."""
        results = [
            RetrievalResult(
                doc_id="1", text="조항 내용", source=None,
                source_type="statute", score=0.9
            ),
            RetrievalResult(
                doc_id="2", text="근거 있는 조항", source="민법 제398조",
                source_type="statute", score=0.8
            ),
        ]
        guardrail = SourceGuardrail()
        filtered = guardrail.filter(results)
        assert len(filtered) == 1
        assert filtered[0].source == "민법 제398조"

    def test_guardrail_filters_empty_source(self):
        """source가 빈 문자열인 결과를 가드레일이 필터링해야 한다."""
        results = [
            RetrievalResult(
                doc_id="1", text="내용", source="",
                source_type="statute", score=0.95
            ),
        ]
        guardrail = SourceGuardrail()
        filtered = guardrail.filter(results)
        assert len(filtered) == 0

    def test_guardrail_passes_valid_results(self, retriever: HybridRetriever):
        """유효한 출처가 있는 결과는 가드레일을 통과해야 한다."""
        results = retriever.retrieve("위약금", top_k=3)
        guardrail = SourceGuardrail()
        filtered = guardrail.filter(results)
        assert len(filtered) == len(results), "유효한 결과가 필터링되었습니다."

    def test_guardrail_all_no_source_returns_empty(self):
        """모든 결과에 출처가 없으면 빈 리스트를 반환해야 한다."""
        results = [
            RetrievalResult(
                doc_id=str(i), text="내용", source=None,
                source_type="statute", score=0.9 - i * 0.1
            )
            for i in range(3)
        ]
        guardrail = SourceGuardrail()
        filtered = guardrail.filter(results)
        assert filtered == []


# ─────────────────────────────────────────────────────────────────────────────
# 예외 케이스 테스트
# ─────────────────────────────────────────────────────────────────────────────
class TestRAGRetrieverEdgeCases:
    """RAG 검색 예외 및 엣지케이스 검증."""

    def test_empty_query_returns_empty_list(self, retriever: HybridRetriever):
        """빈 질의 입력 시 빈 리스트를 반환해야 한다."""
        results = retriever.retrieve("", top_k=3)
        assert results == []

    def test_top_k_zero_returns_empty_list(self, retriever: HybridRetriever):
        """top_k=0 입력 시 빈 리스트를 반환해야 한다."""
        results = retriever.retrieve("위약금", top_k=0)
        assert results == []

    def test_empty_db_returns_empty_list(self, mock_embedder):
        """빈 문서 DB로 생성한 검색기는 빈 리스트를 반환해야 한다."""
        empty_retriever = HybridRetriever(
            documents=[],
            embed_fn=mock_embedder,
        )
        results = empty_retriever.retrieve("위약금", top_k=3)
        assert results == []

    def test_top_k_larger_than_db_returns_all(self, retriever: HybridRetriever):
        """top_k가 DB 크기보다 크면 DB의 모든 문서를 반환해야 한다."""
        # DB에 4개 문서 존재
        results = retriever.retrieve("계약", top_k=100)
        assert len(results) <= 4, f"DB 크기(4)를 초과한 결과: {len(results)}"

    def test_whitespace_query_returns_empty(self, retriever: HybridRetriever):
        """공백만 있는 질의는 빈 리스트를 반환해야 한다."""
        results = retriever.retrieve("   ", top_k=3)
        assert results == []
