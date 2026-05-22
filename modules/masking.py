"""
masking.py  ── 모듈 B: 보안 마스킹 모듈
═══════════════════════════════════════════════════════════════════════════════

[Green 단계] 테스트를 통과하는 최소 구현 → [Refactor] 스레드 안전성 확보

주요 기능:
  - 기업명, 인물명, 금액, 주민번호, 법인번호를 임시 식별자로 치환
  - 치환 딕셔너리(mapping) 반환으로 복원 보장
  - spaCy NER + 정규표현식 하이브리드 방식
  - 동일 엔티티 → 동일 토큰 재사용 (일관성 보장)
  - [Refactor] 스레드 안전성을 위해 threading.Lock 적용

토큰 형식:
  기업명   → [COMPANY_A], [COMPANY_B], ...
  인물명   → [PERSON_A], [PERSON_B], ...
  금액     → [PRICE_A], [PRICE_B], ...
  주민번호 → [RESIDENT_ID_A], [RESIDENT_ID_B], ...
  법인번호 → [CORP_ID_A], [CORP_ID_B], ...
"""

from __future__ import annotations

import re
import string
import threading
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# 커스텀 예외
# ─────────────────────────────────────────────────────────────────────────────
class UnmaskError(KeyError):
    """마스킹 복원 불가 오류 (알 수 없는 토큰)."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# 정규식 패턴 (Refactor: 컴파일 캐싱)
# ─────────────────────────────────────────────────────────────────────────────
# 주민등록번호: 6자리-7자리
_RESIDENT_ID_RE = re.compile(r"(?<!\d)\d{6}-\d{7}(?!\d)")
# 법인등록번호: 6자리-7자리 (주민번호와 동일 패턴이나 앞 2자리 구분 가능)
_CORP_ID_RE = re.compile(r"(?<!\d)\d{6}-\d{7}(?!\d)")  # 문맥으로 구분
# 금액: 한국 금액 표현 (예: 5,000만원, 2억 5,000만원, 1,000만원)
_PRICE_RE = re.compile(
    r"(?:\d{1,3}(?:,\d{3})*|\d+)\s*(?:억|만)?\s*원"
    r"|금\s*(?:\d{1,3}(?:,\d{3})*)\s*(?:억|만)?\s*원"
)
# 기업명: 이름 본체만 매칭 (non-greedy + 조사 lookahead, $ 단독 허용 금지)
_NAME_CORE = r"[가-힣A-Za-z0-9·&]{2,15}?"
_PARTICLE_BOUNDARY = r"(?=[은이가를와과의도는,\.\)\s\"']|$)"
_TRAILING_PARTICLES_RE = re.compile(r"[이가을를은는으며다]+$")
_COMPANY_RE = re.compile(
    r"(?:"
    rf"주식회사\s*{_NAME_CORE}{_PARTICLE_BOUNDARY}"
    rf"|{_NAME_CORE}주식회사{_PARTICLE_BOUNDARY}"
    rf"|\(주\)\s*{_NAME_CORE}{_PARTICLE_BOUNDARY}"
    rf"|{_NAME_CORE}\s*\(주\){_PARTICLE_BOUNDARY}"
    rf"|유한회사\s*{_NAME_CORE}{_PARTICLE_BOUNDARY}"
    rf"|[가-힣]{{2,10}}(?:전자|화학|그룹|은행|증권|보험|공사|건설|중공업|시스템|솔루션|테크){_PARTICLE_BOUNDARY}"
    rf"|{_NAME_CORE}\s*(?:Inc\.|LLC|Corp\.|Co\.,?\s*Ltd\.?){_PARTICLE_BOUNDARY}"
    r")"
)
# 한국 인물명 (spaCy 미설치 시): 성씨 + 이름(1~2글자), 조사 앞에서 종료
_PERSON_RE = re.compile(
    r"(?<![가-힣])"
    r"([김이박최정강조윤장임한오서신권황안송류전홍][가-힣]{1,2})"
    r"(?=[이가을를은는으며다]|(?!\w))"
)


# ─────────────────────────────────────────────────────────────────────────────
# 토큰 인덱스 → 알파벳 변환 헬퍼
# ─────────────────────────────────────────────────────────────────────────────
def _index_to_letters(idx: int) -> str:
    """
    0 → 'A', 1 → 'B', ..., 25 → 'Z', 26 → 'AA', ...

    [Refactor] 26개 초과 엔티티 처리를 위한 다중 문자 인덱스
    """
    letters = string.ascii_uppercase
    result = ""
    idx += 1  # 1-indexed
    while idx > 0:
        idx, remainder = divmod(idx - 1, 26)
        result = letters[remainder] + result
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 결과 데이터 클래스
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class MaskingResult:
    """마스킹 처리 결과."""
    masked_text: str
    mapping: dict[str, str]  # {토큰: 원본값}
    entity_count: int = 0

    def __post_init__(self):
        self.entity_count = len(self.mapping)


# ─────────────────────────────────────────────────────────────────────────────
# 핵심 마스킹 엔진 (Refactor: 스레드 안전성)
# ─────────────────────────────────────────────────────────────────────────────
class MaskingEngine:
    """
    텍스트 내 민감 정보를 식별하고 임시 토큰으로 치환하는 엔진.

    [Refactor]
    - threading.Lock으로 멀티스레드 환경에서 상태 무결성 보장
    - spaCy 로드 실패 시 정규식 전용 모드로 폴백
    - 동일 엔티티 재사용 보장 (_value_to_token 역방향 매핑)
    """

    def __init__(self, use_spacy: bool = True):
        """
        Args:
            use_spacy: spaCy NER 사용 여부.
                       False이면 정규식 전용 모드로 동작.
        """
        self._lock = threading.Lock()
        self._mapping: dict[str, str] = {}           # {토큰: 원본값}
        self._value_to_token: dict[str, str] = {}    # {원본값: 토큰} (역방향)
        self._counters: dict[str, int] = {}           # {타입: 카운터}
        self._nlp = None

        if use_spacy:
            self._nlp = self._load_spacy_model()

    # ── spaCy 로드 ───────────────────────────────────────────────────────────
    @staticmethod
    def _load_spacy_model():
        """
        spaCy 한국어 모델 로드. 실패 시 None 반환 (폴백 모드).
        """
        try:
            # pyrefly: ignore [missing-import]
            import spacy
            return spacy.load("ko_core_news_lg")
        except Exception:
            try:
                # pyrefly: ignore [missing-import]
                import spacy
                return spacy.load("ko_core_news_sm")
            except Exception:
                return None  # 정규식 전용 폴백

    # ── 공개 API ─────────────────────────────────────────────────────────────
    def mask(self, text: str) -> MaskingResult:
        """
        텍스트를 마스킹하고 MaskingResult를 반환합니다.

        스레드 안전: Lock을 사용하여 동시 접근을 방지합니다.
        """
        if not text or not text.strip():
            return MaskingResult(masked_text=text, mapping={})

        with self._lock:
            masked = self._apply_masking(text)
            return MaskingResult(
                masked_text=masked,
                mapping=dict(self._mapping),  # 방어적 복사
            )

    def reset(self) -> None:
        """내부 상태(매핑 테이블, 카운터)를 초기화합니다."""
        with self._lock:
            self._mapping.clear()
            self._value_to_token.clear()
            self._counters.clear()

    @property
    def current_mapping(self) -> dict[str, str]:
        """현재 매핑 테이블 (읽기 전용 복사본)."""
        with self._lock:
            return dict(self._mapping)

    # ── 내부 마스킹 로직 ─────────────────────────────────────────────────────
    def _apply_masking(self, text: str) -> str:
        """
        마스킹 처리 순서:
        1. 주민/법인번호 (패턴이 명확 → 먼저 처리)
        2. 금액 (숫자 + 단위)
        3. 기업명 (정규식)
        4. 인물명 및 기업명 (spaCy NER 또는 정규식 폴백)
        """
        # 순서 중요: 더 구체적인 패턴 먼저
        text = self._mask_ids(text)
        text = self._mask_by_pattern(text, _PRICE_RE, "PRICE")
        text = self._mask_by_pattern(text, _COMPANY_RE, "COMPANY")

        # 인물명 및 기업명 마스킹
        if self._nlp:
            text = self._mask_spacy_entities(text)
        else:
            text = self._mask_persons_regex(text)

        return text

    def _get_or_create_token(self, entity_type: str, original: str) -> str:
        """
        원본값에 대응하는 토큰을 반환합니다.
        같은 원본값은 항상 같은 토큰을 재사용합니다.
        """
        if original in self._value_to_token:
            return self._value_to_token[original]

        # 새 카운터 할당
        count = self._counters.get(entity_type, 0)
        letter = _index_to_letters(count)
        token = f"[{entity_type}_{letter}]"

        self._counters[entity_type] = count + 1
        self._mapping[token] = original
        self._value_to_token[original] = token
        return token

    def _mask_by_pattern(
        self, text: str, pattern: re.Pattern, entity_type: str
    ) -> str:
        """정규식 패턴으로 엔티티를 찾아 토큰으로 치환합니다."""
        def replace(match: re.Match) -> str:
            original = match.group(0)
            return self._get_or_create_token(entity_type, original)

        return pattern.sub(replace, text)

    def _mask_ids(self, text: str) -> str:
        """주민등록번호와 법인등록번호를 구분하여 마스킹합니다."""
        def replace(match: re.Match) -> str:
            original = match.group(0)
            start_idx = match.start()
            # preceding 30 characters
            preceding_context = match.string[max(0, start_idx - 30):start_idx]
            if "법인" in preceding_context:
                entity_type = "CORP_ID"
            else:
                entity_type = "RESIDENT_ID"
            return self._get_or_create_token(entity_type, original)

        return _RESIDENT_ID_RE.sub(replace, text)

    def _mask_spacy_entities(self, text: str) -> str:
        """spaCy NER로 인물명과 기업명을 찾아 마스킹합니다."""
        doc = self._nlp(text)
        # 오프셋 역방향으로 치환 (앞에서부터 치환하면 오프셋 깨짐)
        entities = []
        for ent in doc.ents:
            # Skip if the entity text contains brackets '[' or ']' or is already masked
            if "[" in ent.text or "]" in ent.text:
                continue

            if ent.label_ in ("PERSON", "PS", "PER"):
                entities.append((ent.start_char, ent.end_char, ent.text, "PERSON"))
            elif ent.label_ in ("ORG", "OG"):
                entities.append((ent.start_char, ent.end_char, ent.text, "COMPANY"))

        # 오프셋 역순 치환
        for start, end, original, entity_type in sorted(entities, key=lambda x: x[0], reverse=True):
            if "[" in original or "]" in original:
                continue
            if entity_type == "PERSON":
                trimmed = _TRAILING_PARTICLES_RE.sub("", original)
                if trimmed and trimmed != original:
                    original = trimmed
                    end = start + len(original)
            token = self._get_or_create_token(entity_type, original)
            text = text[:start] + token + text[end:]
        return text

    def _mask_persons_regex(self, text: str) -> str:
        """spaCy 사용 불가 시 정규식으로 한국 인물명 패턴을 마스킹합니다."""
        def replace(match: re.Match) -> str:
            original = match.group(1)
            return self._get_or_create_token("PERSON", original)

        return _PERSON_RE.sub(replace, text)


# ─────────────────────────────────────────────────────────────────────────────
# 편의 함수 (공개 API)
# ─────────────────────────────────────────────────────────────────────────────

# 모듈 수준 공유 엔진 (기본 사용)
_default_engine = MaskingEngine(use_spacy=True)


def mask_text(text: str, engine: Optional[MaskingEngine] = None) -> MaskingResult:
    """
    텍스트 내 민감 정보를 마스킹합니다.

    Args:
        text: 마스킹할 원본 텍스트
        engine: 사용할 MaskingEngine (None이면 새 엔진 생성)

    Returns:
        MaskingResult: 마스킹된 텍스트와 치환 딕셔너리

    Examples:
        >>> result = mask_text("(주)테크솔루션과 김철수의 계약서입니다.")
        >>> "[COMPANY_A]" in result.masked_text
        True
        >>> result.mapping["[COMPANY_A]"]
        '(주)테크솔루션'
    """
    if engine is None:
        # 매 호출마다 독립적인 엔진 사용 (상태 격리)
        engine = MaskingEngine(use_spacy=True)
    return engine.mask(text)


def unmask_text(
    masked_text: str,
    mapping: dict[str, str],
    strict: bool = True,
) -> str:
    """
    마스킹된 텍스트를 원본으로 복원합니다.

    Args:
        masked_text: 마스킹 처리된 텍스트
        mapping: 토큰→원본값 딕셔너리 (MaskingResult.mapping)
        strict: True이면 알 수 없는 토큰 발견 시 UnmaskError 발생

    Returns:
        str: 복원된 원문 텍스트

    Raises:
        UnmaskError: strict=True이고 mapping에 없는 토큰이 있을 때

    Examples:
        >>> result = mask_text("(주)테크솔루션의 계약입니다.")
        >>> unmask_text(result.masked_text, result.mapping)
        '(주)테크솔루션의 계약입니다.'
    """
    if not masked_text:
        return masked_text

    # 텍스트 내 모든 토큰 찾기
    token_pattern = re.compile(r"\[[A-Z_]+\]")
    found_tokens = token_pattern.findall(masked_text)

    if strict:
        unknown = [t for t in found_tokens if t not in mapping]
        if unknown:
            raise UnmaskError(
                f"mapping에 없는 토큰이 발견되었습니다: {unknown}"
            )

    result = masked_text
    # 긴 토큰부터 치환 (부분 매칭 방지)
    for token in sorted(mapping.keys(), key=len, reverse=True):
        result = result.replace(token, mapping[token])
    return result
