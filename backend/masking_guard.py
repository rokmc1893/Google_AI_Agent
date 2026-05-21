import re
from typing import Dict, Tuple

class MaskingGuard:
    """
    기밀 유출 방지를 위해 계약서 내 민감 정보(기업명, 금액, 개인정보 등)를 
    외부 LLM 호출 전 마스킹하고, 결과 수신 후 다시 복원(De-masking)하는 로컬 보안 가드레일 클래스입니다.
    """
    def __init__(self):
        # 마스킹 맵: {마스킹토큰: 원본텍스트}
        self.de_mask_map: Dict[str, str] = {}
        # 마스킹 카운터
        self.counters = {
            "COMPANY": 1,
            "INDIVIDUAL": 1,
            "MONEY": 1,
            "DATE": 1,
            "RRN": 1 # 주민등록번호/등록번호
        }

    def reset(self):
        self.de_mask_map.clear()
        for k in self.counters:
            self.counters[k] = 1

    def mask(self, text: str) -> str:
        """
        텍스트 내 민감 정보를 마스킹하고 마스킹된 텍스트를 반환합니다.
        """
        self.reset()
        masked_text = text

        # 1. 주민등록번호 / 법인등록번호 / 사업자번호 마스킹 (예: 123456-1234567)
        rrn_pattern = r'\b\d{6}-\d{7}\b|\b\d{3}-\d{2}-\d{5}\b'
        matches = re.findall(rrn_pattern, masked_text)
        for match in set(matches):
            token = f"[ID_NO_{self.counters['RRN']}]"
            self.de_mask_map[token] = match
            masked_text = masked_text.replace(match, token)
            self.counters['RRN'] += 1

        # 2. 금액 마스킹 (예: 10,000,000원, 5천만원, USD 50,000)
        money_pattern = r'\b(?:USD|KRW|₩)?\s?\d{1,3}(?:,\d{3})*(?:\s?원|\s?만\s?원|\s?억\s?원)?\b|\b\d+\s?천?\s?만?\s?억\s?원\b'
        matches = re.findall(money_pattern, masked_text)
        # 긴 매치부터 처리하여 부분 매치 버그 방지
        for match in sorted(set(matches), key=len, reverse=True):
            if match.strip() and not match.isdigit(): # 단순 숫자 방지
                token = f"[VALUE_{self.counters['MONEY']}]"
                self.de_mask_map[token] = match
                masked_text = masked_text.replace(match, token)
                self.counters['MONEY'] += 1

        # 3. 특정 고유명사 (기업명 등) 마스킹
        # 한글/영문 주식회사 패턴 (예: 주식회사 홍길동, (주)아무개, ABC Co., Ltd.)
        company_patterns = [
            r'\(주\)\s?[가-힣A-Za-z0-9]+',
            r'주식회사\s?[가-힣A-Za-z0-9]+',
            r'[가-힣A-Za-z0-9]+\s?\(주\)',
            r'[가-힣A-Za-z0-9]+\s?주식회사',
            r'\b[A-Z][A-Za-z0-9\s]+(?:Co\.,?\s?Ltd\.|Inc\.|Corp\.)'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, masked_text)
            for match in set(matches):
                # 중복 마스킹 방지
                if match in self.de_mask_map.values():
                    continue
                token = f"[COMPANY_{chr(64 + self.counters['COMPANY'])}]" # A, B, C...
                self.de_mask_map[token] = match
                masked_text = masked_text.replace(match, token)
                self.counters['COMPANY'] += 1
                if self.counters['COMPANY'] > 26: # 알파벳 한계 대비
                    self.counters['COMPANY'] = 1

        # 4. 날짜 패턴 마스킹 (예: 2026년 5월 21일, 2026.05.21)
        date_pattern = r'\b\d{4}년\s?\d{1,2}월\s?\d{1,2}일\b|\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b'
        matches = re.findall(date_pattern, masked_text)
        for match in set(matches):
            token = f"[DATE_{self.counters['DATE']}]"
            self.de_mask_map[token] = match
            masked_text = masked_text.replace(match, token)
            self.counters['DATE'] += 1

        return masked_text

    def unmask(self, text: str) -> str:
        """
        마스킹된 텍스트를 원본 정보로 복원합니다.
        """
        unmasked_text = text
        # 키 크기 역순으로 정렬하여 마스킹 해제 (긴 토큰이 먼저 해제되도록 함)
        for token, original in sorted(self.de_mask_map.items(), key=lambda x: len(x[0]), reverse=True):
            unmasked_text = unmasked_text.replace(token, original)
        return unmasked_text

# 간단한 테스트
if __name__ == "__main__":
    guard = MaskingGuard()
    sample_contract = (
        "갑: 주식회사 에이비씨 (사업자번호: 120-12-34567)\n"
        "을: (주)데프코리아 (주민등록번호: 850101-1234567)\n"
        "제3조 (계약금) 계약 금액은 총 KRW 50,000,000원으로 정하며, "
        "2026년 06월 01일까지 을의 계좌로 입금한다."
    )
    print("=== 원본 계약서 ===")
    print(sample_contract)
    
    masked = guard.mask(sample_contract)
    print("\n=== 마스킹된 계약서 ===")
    print(masked)
    
    unmasked = guard.unmask(masked)
    print("\n=== 복원된 계약서 ===")
    print(unmasked)
