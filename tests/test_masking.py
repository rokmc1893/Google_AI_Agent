"""
test_masking.py  ── 모듈 B: 보안 마스킹 모듈 TDD
═══════════════════════════════════════════════════════════════════════════════

[RED 단계] 구현 코드보다 먼저 작성된 테스트 코드입니다.

테스트 시나리오:
  ✅ 성공 케이스
    - 기업명이 [COMPANY_A] 형식으로 치환되는지 검증
    - 인물명(NER)이 [PERSON_A] 형식으로 치환되는지 검증
    - 금액이 [PRICE_A] 형식으로 치환되는지 검증
    - 마스킹 치환 딕셔너리(mapping)가 정확히 반환되는지 검증
    - unmask() 함수로 원본 텍스트 완전 복원 검증
    - 동일 엔티티가 반복 등장할 때 동일 토큰 재사용 검증
    - 서로 다른 엔티티에 다른 인덱스 부여 검증

  ❌ 예외 케이스
    - 빈 문자열 입력 시 처리 검증
    - 엔티티가 없는 텍스트 입력 시 처리 검증
    - unmask() 에 없는 토큰이 포함된 경우 처리 검증
    - 중첩(overlap) 엔티티 처리 검증

실행 방법:
  pytest tests/test_masking.py -v
"""

import re
# pyrefly: ignore [missing-import]
import pytest

from modules.masking import (
    MaskingEngine,
    MaskingResult,
    UnmaskError,
    mask_text,
    unmask_text,
)


# ─────────────────────────────────────────────────────────────────────────────
# 테스트용 샘플 텍스트
# ─────────────────────────────────────────────────────────────────────────────
COMPANY_TEXT = (
    "(주)테크솔루션은 고객사인 삼성전자와 계약을 체결하였다. "
    "(주)테크솔루션의 대표이사는 김철수이며, 담당자는 이영희이다."
)

PRICE_TEXT = (
    "용역 대금은 금 5,000만원(부가가치세 포함)이며, "
    "선급금은 1,000만원, 잔금은 4,000만원이다."
)

COMPLEX_TEXT = (
    "(주)에이비씨(이하 '갑')과 홍길동(이하 '을')은 "
    "2억 5,000만원 규모의 소프트웨어 개발 계약을 체결한다. "
    "(주)에이비씨의 법인등록번호는 110111-1234567이며, "
    "홍길동의 주민등록번호는 800101-1234567이다."
)

NO_ENTITY_TEXT = (
    "본 계약은 쌍방의 합의에 의하여 체결되며, "
    "계약 내용의 변경은 서면으로 한다."
)


# ─────────────────────────────────────────────────────────────────────────────
# 성공 케이스 테스트
# ─────────────────────────────────────────────────────────────────────────────
class TestMaskingSuccessCases:
    """마스킹 성공 시나리오 검증."""

    def test_mask_returns_masking_result(self):
        """mask_text()는 MaskingResult 타입을 반환해야 한다."""
        result = mask_text(COMPANY_TEXT)
        assert isinstance(result, MaskingResult)

    def test_masking_result_has_masked_text(self):
        """MaskingResult에 masked_text 속성이 있어야 한다."""
        result = mask_text(COMPANY_TEXT)
        assert hasattr(result, "masked_text")
        assert isinstance(result.masked_text, str)

    def test_masking_result_has_mapping(self):
        """MaskingResult에 mapping 딕셔너리가 있어야 한다."""
        result = mask_text(COMPANY_TEXT)
        assert hasattr(result, "mapping")
        assert isinstance(result.mapping, dict)

    def test_company_name_masked(self):
        """기업명이 [COMPANY_X] 형식으로 치환되어야 한다."""
        result = mask_text(COMPANY_TEXT)
        assert "(주)테크솔루션" not in result.masked_text, "기업명이 마스킹되지 않았습니다."
        # COMPANY 토큰이 포함되어야 함
        assert re.search(r"\[COMPANY_[A-Z]+\]", result.masked_text), (
            "COMPANY 토큰이 없습니다."
        )

    def test_person_name_masked(self):
        """인물명이 [PERSON_X] 형식으로 치환되어야 한다."""
        result = mask_text(COMPANY_TEXT)
        assert "김철수" not in result.masked_text, "인물명이 마스킹되지 않았습니다."
        assert re.search(r"\[PERSON_[A-Z]+\]", result.masked_text), (
            "PERSON 토큰이 없습니다."
        )

    def test_price_masked(self):
        """금액이 [PRICE_X] 형식으로 치환되어야 한다."""
        result = mask_text(PRICE_TEXT)
        assert re.search(r"\[PRICE_[A-Z]+\]", result.masked_text), (
            "PRICE 토큰이 없습니다."
        )

    def test_mapping_key_format(self):
        """mapping의 키는 [TYPE_LETTER] 형식이어야 한다."""
        result = mask_text(COMPANY_TEXT)
        pattern = re.compile(r"^\[(COMPANY|PERSON|PRICE|CORP_ID|RESIDENT_ID)_[A-Z]+\]$")
        for key in result.mapping.keys():
            assert pattern.match(key), f"잘못된 mapping 키 형식: {key}"

    def test_mapping_value_is_original(self):
        """mapping의 값은 원본 텍스트의 일부여야 한다."""
        result = mask_text(COMPANY_TEXT)
        for token, original in result.mapping.items():
            assert original in COMPANY_TEXT, (
                f"매핑값 '{original}'이 원본 텍스트에 없습니다."
            )

    def test_unmask_restores_original_text(self):
        """unmask_text()로 완전한 원본 텍스트 복원이 가능해야 한다."""
        result = mask_text(COMPANY_TEXT)
        restored = unmask_text(result.masked_text, result.mapping)
        assert restored == COMPANY_TEXT, (
            f"복원 실패.\n원본: {COMPANY_TEXT}\n복원: {restored}"
        )

    def test_unmask_price_text(self):
        """금액 마스킹 텍스트를 완전히 복원할 수 있어야 한다."""
        result = mask_text(PRICE_TEXT)
        restored = unmask_text(result.masked_text, result.mapping)
        assert restored == PRICE_TEXT

    def test_same_entity_same_token(self):
        """동일한 엔티티가 반복 등장할 때 동일한 토큰이 사용되어야 한다."""
        text = "(주)테크솔루션은 훌륭한 회사다. (주)테크솔루션은 계속 성장할 것이다."
        result = mask_text(text)

        # 치환된 토큰이 하나여야 함 (중복 치환 없음)
        company_tokens = re.findall(r"\[COMPANY_[A-Z]+\]", result.masked_text)
        unique_tokens = set(company_tokens)
        assert len(unique_tokens) == 1, (
            f"동일 엔티티에 여러 토큰이 사용됨: {unique_tokens}"
        )
        assert company_tokens[0] == company_tokens[-1], (
            "동일 엔티티에 다른 토큰이 사용되었습니다."
        )

    def test_different_entities_different_tokens(self):
        """서로 다른 기업명에는 다른 인덱스 토큰이 부여되어야 한다."""
        text = "(주)테크솔루션과 삼성전자는 파트너 관계이다."
        result = mask_text(text)

        company_tokens = re.findall(r"\[COMPANY_[A-Z]+\]", result.masked_text)
        # 두 개의 다른 회사 → 두 개의 다른 토큰
        assert len(set(company_tokens)) == 2, (
            f"서로 다른 기업에 다른 토큰이 없음: {company_tokens}"
        )

    def test_masking_engine_class(self):
        """MaskingEngine 클래스를 직접 사용할 수 있어야 한다."""
        engine = MaskingEngine()
        result = engine.mask(COMPANY_TEXT)
        assert isinstance(result, MaskingResult)

    def test_masking_engine_reset_clears_state(self):
        """MaskingEngine.reset() 호출 후 내부 상태(매핑 테이블)가 초기화되어야 한다."""
        engine = MaskingEngine()
        engine.mask(COMPANY_TEXT)
        assert len(engine.current_mapping) > 0

        engine.reset()
        assert len(engine.current_mapping) == 0

    def test_complex_text_masking(self):
        """복합 텍스트(기업명+인물명+금액+ID)를 마스킹하고 복원해야 한다."""
        result = mask_text(COMPLEX_TEXT)
        restored = unmask_text(result.masked_text, result.mapping)
        assert restored == COMPLEX_TEXT

    def test_resident_id_masked(self):
        """주민등록번호가 마스킹되어야 한다."""
        text = "홍길동의 주민등록번호는 800101-1234567이다."
        result = mask_text(text)
        assert "800101-1234567" not in result.masked_text, (
            "주민등록번호가 마스킹되지 않았습니다."
        )

    def test_corporate_id_masked(self):
        """법인등록번호가 마스킹되어야 한다."""
        text = "법인등록번호는 110111-1234567이다."
        result = mask_text(text)
        assert "110111-1234567" not in result.masked_text, (
            "법인등록번호가 마스킹되지 않았습니다."
        )


# ─────────────────────────────────────────────────────────────────────────────
# 예외 케이스 테스트
# ─────────────────────────────────────────────────────────────────────────────
class TestMaskingEdgeCases:
    """마스킹 예외 및 엣지케이스 검증."""

    def test_empty_string_input(self):
        """빈 문자열 입력 시 빈 masked_text와 빈 mapping을 반환해야 한다."""
        result = mask_text("")
        assert result.masked_text == ""
        assert result.mapping == {}

    def test_no_entity_text(self):
        """엔티티가 없는 텍스트는 원본 그대로 반환하고 mapping이 비어야 한다."""
        result = mask_text(NO_ENTITY_TEXT)
        assert result.masked_text == NO_ENTITY_TEXT
        assert result.mapping == {}

    def test_unmask_with_unknown_token_raises_error(self):
        """mapping에 없는 토큰이 포함된 경우 UnmaskError를 발생시켜야 한다."""
        masked_text = "계약서에 [COMPANY_Z]이 있습니다."
        empty_mapping = {}
        with pytest.raises(UnmaskError):
            unmask_text(masked_text, empty_mapping, strict=True)

    def test_unmask_non_strict_does_not_raise(self):
        """strict=False일 때 알 수 없는 토큰은 그대로 남겨야 한다."""
        masked_text = "계약서에 [COMPANY_Z]이 있습니다."
        result = unmask_text(masked_text, {}, strict=False)
        assert "[COMPANY_Z]" in result

    def test_whitespace_only_input(self):
        """공백만 있는 입력은 그대로 반환해야 한다."""
        result = mask_text("   \n\t  ")
        assert result.mapping == {}

    def test_masking_is_idempotent_with_engine(self):
        """동일 텍스트를 같은 엔진으로 두 번 마스킹해도 결과가 동일해야 한다."""
        engine = MaskingEngine()
        result1 = engine.mask(COMPANY_TEXT)
        engine.reset()
        result2 = engine.mask(COMPANY_TEXT)
        # 토큰 인덱스는 같아야 함 (A, B, C 순서 동일)
        assert set(result1.mapping.keys()) == set(result2.mapping.keys())

    def test_mapping_has_no_duplicates(self):
        """mapping의 값(원본 엔티티)에 중복이 없어야 한다."""
        result = mask_text(COMPLEX_TEXT)
        values = list(result.mapping.values())
        assert len(values) == len(set(values)), (
            f"mapping 값에 중복이 있습니다: {values}"
        )
