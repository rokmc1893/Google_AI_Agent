"""
conftest.py
───────────────────────────────────────────────────────────────────────────────
pytest 전역 픽스처 및 공통 설정.
모든 테스트 모듈에서 자동으로 참조되며, 실제 외부 서비스(OpenAI, DB 등)는
mock으로 대체하여 테스트 환경 독립성을 보장합니다.
"""

import json
import os
import textwrap
from io import BytesIO
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# ──────────────────────────────────────────────────────────────────────────────
# 경로 상수
# ──────────────────────────────────────────────────────────────────────────────
FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"


# ──────────────────────────────────────────────────────────────────────────────
# 계약서 샘플 텍스트 픽스처
# ──────────────────────────────────────────────────────────────────────────────
SAMPLE_CONTRACT_TEXT = textwrap.dedent(
    """
    제1조 (목적)
      본 계약은 (주)테크솔루션(이하 "갑")과 김철수(이하 "을") 사이의
      소프트웨어 개발 용역에 관한 사항을 정함을 목적으로 한다.

      제1항 계약 기간은 2024년 1월 1일부터 2024년 12월 31일까지로 한다.
        제1호 단, 갑의 서면 동의가 있을 경우 연장 가능하다.

    제2조 (대금 및 지급)
      제1항 용역 대금은 금 5,000만원(부가가치세 포함)으로 한다.
        제1호 갑은 계약 체결 후 7일 이내에 계약금 1,000만원을 지급한다.
        제2호 잔금은 용역 완료 후 30일 이내에 지급한다.

    제3조 (손해배상 및 위약금)
      제1항 을이 계약을 위반하는 경우, 갑에 대하여 계약 총액의 20%에 해당하는
      위약금을 지급하여야 한다.
      제2항 갑의 귀책사유로 계약이 해지되는 경우, 을은 기 지급받은 대금을
      모두 반환하여야 한다.

    제4조 (비밀유지)
      제1항 계약 당사자는 본 계약 내용 및 이행 과정에서 알게 된 상대방의
      영업비밀을 제3자에게 누설하여서는 아니 된다.
    """
).strip()


SAMPLE_MASKED_TEXT = (
    "제1조 (목적)\n"
    "본 계약은 [COMPANY_A]과 [PERSON_A](이하 \"을\") 사이의 소프트웨어 개발 용역에 관한 "
    "사항을 정함을 목적으로 한다.\n"
    "제2조 (대금) 용역 대금은 [PRICE_A](부가가치세 포함)으로 한다."
)


# ──────────────────────────────────────────────────────────────────────────────
# 법령 DB 샘플 픽스처
# ──────────────────────────────────────────────────────────────────────────────
SAMPLE_LEGAL_DB: list[dict] = [
    {
        "id": "civil_law_398",
        "source": "민법 제398조",
        "source_type": "statute",
        "text": "당사자는 채무불이행에 관한 손해배상액을 예정할 수 있다. "
                "손해배상의 예정액이 부당히 과다한 경우에는 법원은 적당히 감액할 수 있다.",
        "tags": ["위약금", "손해배상", "손해배상예정"],
    },
    {
        "id": "labor_law_46",
        "source": "근로기준법 제46조",
        "source_type": "statute",
        "text": "사용자는 휴업하는 경우에 휴업기간 동안 그 근로자에게 평균임금의 100분의 70 이상의 "
                "수당을 지급하여야 한다.",
        "tags": ["휴업수당", "임금", "근로"],
    },
    {
        "id": "internal_policy_contract_01",
        "source": "사내규정 계약관리규정 제7조",
        "source_type": "internal_policy",
        "text": "계약 총액의 10%를 초과하는 위약금 조항은 법무팀의 사전 검토를 받아야 한다.",
        "tags": ["위약금", "계약", "법무검토"],
    },
    {
        "id": "precedent_2023da12345",
        "source": "대법원 2023다12345 판결",
        "source_type": "precedent",
        "text": "비밀유지 의무의 범위가 포괄적으로 규정되어 있어 계약 당사자의 직업 선택의 "
                "자유를 과도하게 제한하는 경우 해당 조항은 무효이다.",
        "tags": ["비밀유지", "직업선택의자유", "무효"],
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# pytest 픽스처
# ──────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """테스트 픽스처 디렉토리 경로."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def sample_contract_text() -> str:
    """샘플 계약서 전문(plain text)."""
    return SAMPLE_CONTRACT_TEXT


@pytest.fixture(scope="session")
def sample_legal_db() -> list[dict]:
    """인메모리 법령/사내규정 DB."""
    return SAMPLE_LEGAL_DB


@pytest.fixture(scope="session")
def sample_legal_db_json(fixtures_dir: Path) -> Path:
    """법령 DB JSON 파일 경로 (없으면 생성)."""
    path = fixtures_dir / "sample_legal_db.json"
    if not path.exists():
        path.write_text(
            json.dumps(SAMPLE_LEGAL_DB, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return path


@pytest.fixture()
def mock_llm():
    """OpenAI LLM 호출을 mock으로 대체."""
    with patch("langchain_openai.ChatOpenAI") as mock_cls:
        instance = MagicMock()
        instance.invoke.return_value = MagicMock(
            content="위험도: 높음\n근거: 민법 제398조에 따라 위약금이 과다합니다."
        )
        mock_cls.return_value = instance
        yield instance


@pytest.fixture()
def mock_embeddings():
    """임베딩 모델 호출을 mock으로 대체."""
    import numpy as np

    with patch("langchain_openai.OpenAIEmbeddings") as mock_cls:
        instance = MagicMock()
        # 항상 동일한 차원의 벡터 반환 (1536-dim, OpenAI ada-002 기준)
        instance.embed_query.return_value = np.random.rand(1536).tolist()
        instance.embed_documents.side_effect = lambda texts: [
            np.random.rand(1536).tolist() for _ in texts
        ]
        mock_cls.return_value = instance
        yield instance
