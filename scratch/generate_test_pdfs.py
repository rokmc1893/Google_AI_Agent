import os
import sys
from pathlib import Path
import fitz  # PyMuPDF

# Use Malgun Gothic from Windows font folder to ensure Korean renders properly
FONT_PATH = "C:\\Windows\\Fonts\\malgun.ttf"
FONT_BOLD_PATH = "C:\\Windows\\Fonts\\malgunbd.ttf"

if not os.path.exists(FONT_PATH):
    # Fallback to other fonts if Malgun Gothic is missing
    FONT_PATH = "C:\\Windows\\Fonts\\batang.ttc"

def create_pdf(filename: str, title: str, paragraphs: list):
    doc = fitz.open()
    page = doc.new_page()
    
    # Register font
    font_name = "Malgun"
    page.insert_font(fontname=font_name, fontfile=FONT_PATH)
    
    y = 50
    # Title
    page.insert_text((50, y), title, fontname=font_name, fontsize=16)
    y += 40
    
    for para in paragraphs:
        # Check space limit, create new page if needed
        if y > 750:
            page = doc.new_page()
            page.insert_font(fontname=font_name, fontfile=FONT_PATH)
            y = 50
            
        # Draw paragraph
        rect = fitz.Rect(50, y, 550, y + 150)
        # Using insert_textbox allows auto wrapping of text lines
        available_height = page.insert_textbox(rect, para, fontname=font_name, fontsize=10)
        
        # Increment y by the height consumed or a fixed step
        y += max(available_height, 60) + 15
        
    doc.save(filename)
    print(f"Created PDF: {filename} ({os.path.abspath(filename)})")

# Paragraphs definition for 5 contracts

# 1. 좋은 계약서 (Fair/Safe)
fair_contract = [
    "본 계약은 주식회사 한국솔루션(이하 '갑')과 홍길동(이하 '을') 사이에 소프트웨어 용역에 관하여 다음과 같이 체결한다.",
    "제1조 (목적)\n제1항 본 계약은 갑이 을에게 의뢰한 시스템 개발 업무를 신의성실의 원칙에 따라 수행하는 데 필요한 기본적인 협력 사항을 규정함을 목적으로 한다.",
    "제2조 (계약 기간 및 갱신)\n제1항 본 계약의 유효기간은 계약 체결일로부터 1년으로 한다.\n제2항 계약 종료 30일 전까지 서면으로 합의한 경우에 한하여 1회 연장할 수 있다.",
    "제3조 (용역 대금 및 정산)\n제1항 총 용역대금은 3,000만원으로 하며, 부가가치세를 포함한다.\n제2항 갑은 을의 산출물 검수 완료 후 14일 이내에 을에게 대금을 현금으로 지급한다.\n제3항 갑의 검수가 지연될 경우, 을의 귀책이 없는 한 납품일로부터 14일이 경과한 때에 검수가 완료된 것으로 간주한다.",
    "제4조 (손해배상)\n제1항 계약 당사자 일방이 본 계약상의 의무를 위반하여 상대방에게 손해를 입힌 경우, 그로 인해 발생한 실제 직접적인 손해 범위 내에서 배상할 책임을 진다.\n제2항 천재지변 등 불가항력적인 사유로 인해 발생한 손해에 대해서는 쌍방 모두 면책된다.",
    "제5조 (지식재산권)\n제1항 본 계약을 통해 새롭게 개발된 결과물에 대한 지식재산권은 갑과 을이 공동으로 소유하는 것을 원칙으로 하며, 지분율 및 활용방안은 상호 합의 하에 조정한다.",
    "제6조 (비밀유지)\n제1항 양 당사자는 본 계약 수행 중 취득한 상대방의 비밀정보를 계약 기간 및 종료 후 1년간 비밀로 유지하여야 한다.",
    "2026년 5월 22일\n\n갑: 주식회사 한국솔루션  대표이사 이영희  (인)\n을: 홍길동  (인)"
]

# 2. 완전 나쁜 계약서 (Dangerous/Unfair)
unfair_contract = [
    "본 계약은 주식회사 갑질홀딩스(이하 '갑')과 김철수(이하 '을') 사이에 용역 개발 계약을 다음과 같이 체결한다.",
    "제1조 (목적)\n제1항 본 계약은 갑의 지시에 따라 을이 소프트웨어 개발 업무를 일방적으로 수행하여 최종 결과물을 납품하는 것을 목적으로 한다.",
    "제2조 (계약 기간 및 자동 갱신)\n제1항 계약 기간은 1년으로 한다.\n제2항 계약 종료 전까지 갑이 명시적으로 해지 통보를 하지 않는 한 동일 조건으로 계약이 자동 연장된다.\n제3항 을은 계약의 자동 연장 및 횟수에 대하여 일체의 이의를 제기할 수 없다.",
    "제3조 (대금 지급 및 면책)\n제1항 용역 총액은 5,000만원으로 한다.\n제2항 갑은 대금 지급 시기를 자신의 경영 상황에 따라 임의로 조정하거나 무기한 연기할 수 있으며, 을은 이에 이의를 제기하거나 지연이자를 청구할 수 없다.\n제3항 갑의 변심이나 사정으로 계약이 해지되는 경우, 갑은 일체의 대금을 지급할 의무가 없으며 기 지급된 금액은 전부 반환받는다.",
    "제4조 (손해배상 및 위약금 독소)\n제1항 을이 납품을 단 하루라도 지연하거나 경미한 오류를 발생시키는 경우, 을은 갑에게 계약 총액의 50%를 위약금으로 현금 지급하여야 한다.\n제2항 을의 위약금 지급 의무는 갑의 실제 손해 발생 여부와 무관하게 즉시 효력이 발생하며, 소송을 통한 감액을 청구할 수 없다.",
    "제5조 (지식재산권 일방 양도)\n제1항 을이 개발한 모든 프로그램, 소스코드, 아이디어 및 지식재산권은 개발 즉시 갑에게 무상으로 이전된다.\n제2항 을이 계약 체결 전에 독자적으로 보유하고 있던 특허 및 기술 역시 갑에게 영구 양도된 것으로 간주한다.",
    "제6조 (비밀유지 및 경업금지)\n제1항 을은 계약 종료 후 10년간 관련 정보를 누설해서는 안 되며, 위반 시 1억원의 위약벌을 부과한다.\n제2항 을은 계약 종료 후 5년간 동종업계 일체에 취업할 수 없으며 창업도 금지된다.",
    "제7조 (일방적 해지 및 변경)\n제1항 갑은 사전 통지나 사유 없이 언제든지 서면 통보만으로 본 계약을 즉시 해지하거나 계약 내용을 일방적으로 변경할 수 있다.",
    "2026년 5월 22일\n\n갑: 주식회사 갑질홀딩스  대표이사 최갑수  (인)\n을: 김철수  (인)"
]

# 3. 교묘하게 숨겨놓은 계약서 (Subtle Risk)
subtle_contract = [
    "본 계약은 주식회사 스마트코리아(이하 '갑')과 박민수(이하 '을') 사이에 연구 용역 계약을 체결한다.",
    "제1조 (목적)\n제1항 본 계약은 양 당사자가 합의한 연구 개발 과제를 상호 존중하며 공동으로 추진하는 데 목적이 있다.",
    "제2조 (계약 기간)\n제1항 계약 기간은 체결일로부터 6개월로 한다.",
    "제3조 (대금 지급 및 검수 - 교묘한 독소 조항)\n제1항 용역 대금은 2,000만원으로 한다.\n제2항 갑은 을의 최종 결과물 제출 후 검수를 실시한다.\n제3항 단, 갑이 검수 결과를 을에게 통보하지 않고 지연하는 행위는 검수 불합격으로 판정하는 묵시적 통지로 간주하며, 이 경우 을은 무상으로 재개발을 수행하여야 한다.",
    "제4조 (지식재산권)\n제1항 개발 과정에서 도출된 결과물은 공동으로 소유한다.\n제2항 단, 을이 개발 과정에서 제시한 아이디어와 특허 중, 본 결과물에 기여한 핵심 기술에 대한 특허 소유 지분 및 실시권은 갑에게 독점적이고 무상으로 귀속된다.",
    "제5조 (분쟁 관할 - 교묘한 독소 조항)\n제1항 본 계약과 관련한 분쟁은 갑의 본사 소재지 관할 법원만을 전속적 합의 관할 법원으로 지정하며, 을은 타 법원에 소송을 제기할 권리를 포기한다.",
    "2026년 5월 22일\n\n갑: 주식회사 스마트코리아  대표이사 박지선  (인)\n을: 박민수  (인)"
]

# 4. 랜덤 계약서 1 (Random NDA)
random_nda = [
    "비밀유지 계약서 (NDA)",
    "본 계약은 정보제공자 주식회사 테크밸리(이하 '갑')과 정보수령자 주식회사 이노베이션(이하 '을') 사이에 다음과 같이 비밀유지 계약을 체결한다.",
    "제1조 (목적)\n제1항 본 계약은 갑과 을 사이에 상호 교환되는 기술 및 사업 정보에 대하여 상대방의 비밀정보를 보호하는 데 목적이 있다.",
    "제2조 (비밀정보의 정의)\n제1항 본 계약의 비밀정보는 서면, 구두 또는 전자적 형태로 상대방에게 제공되는 모든 기밀 정보를 의미한다.\n제2항 단, 이미 공개된 정보나 독자적으로 개발한 정보는 비밀정보에서 제외된다.",
    "제3조 (사용 금지 및 비밀 유지)\n제1항 을은 비밀정보를 본 목적 외에 다른 용도로 사용할 수 없으며 임직원 중 권한을 부여받은 자 외에는 노출하여서는 안 된다.",
    "제4조 (계약 기간)\n제1항 비밀유지 의무는 본 계약 체결일로부터 3년간 유효한 것으로 하며, 그 이후에는 소멸한다.",
    "2026년 5월 22일\n\n갑: 주식회사 테크밸리  대표이사 정현우  (인)\n을: 주식회사 이노베이션  대표이사 강동원  (인)"
]

# 5. 랜덤 계약서 2 (Random Supply Contract)
random_supply = [
    "원자재 구매 공급 계약서",
    "본 계약은 구매자 주식회사 빌드업(이하 '갑')과 공급자 주식회사 스틸파트너스(이하 '을') 사이에 다음과 같이 원자재 물품 공급 계약을 체결한다.",
    "제1조 (목적)\n제1항 본 계약은 을이 갑에게 고품질의 강재 원자재를 안정적으로 공급하고, 갑이 대금을 정상 지급하는 기본적인 규정을 마련함에 있다.",
    "제2조 (공급 및 단가)\n제1항 을은 갑이 주문한 사양에 맞추어 매월 10일까지 물품을 지정 장소에 인도하여야 한다.\n제2항 단가는 상호 서면 합의한 공급 단가표를 기준으로 하며, 원자재 가격 변동 폭이 10%를 초과할 경우 상호 재협의를 거쳐 조정한다.",
    "제3조 (품질 보증)\n제1항 을은 납품 후 1년간 원자재 자체의 하자 결함에 대하여 무상으로 대체품을 공급할 품질 보증 책임을 진다.",
    "제4조 (지연 이자)\n제1항 갑이 물품 대금 지급을 지연할 경우, 연 5%의 지연배상금을 을에게 지급하여야 한다.",
    "2026년 5월 22일\n\n갑: 주식회사 빌드업  대표이사 김진수  (인)\n을: 주식회사 스틸파트너스  대표이사 최성진  (인)"
]

# Run PDF Generation
scratch_dir = Path("scratch")
scratch_dir.mkdir(exist_ok=True)

create_pdf("scratch/contract_fair.pdf", "소프트웨어 용역 표준 계약서 (안전)", fair_contract)
create_pdf("scratch/contract_unfair.pdf", "용역 개발 계약서 (독소/위험)", unfair_contract)
create_pdf("scratch/contract_subtle.pdf", "연구 용역 계약서 (교묘한 독소)", subtle_contract)
create_pdf("scratch/contract_random_nda.pdf", "비밀유지 계약서 (표준)", random_nda)
create_pdf("scratch/contract_random_supply.pdf", "원자재 구매 공급 계약서 (일반)", random_supply)

print("All 5 test PDFs generated successfully inside legal_review_agent/scratch/ directory.")
