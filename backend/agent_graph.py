from typing import Dict, List, Any, TypedDict, Literal
from backend.masking_guard import MaskingGuard
from backend.hybrid_rag import HybridRAG

# 1. LangGraph State 정의
class AgentState(TypedDict):
    contract_raw: str                # 원본 계약서 텍스트
    contract_parsed: str             # 조, 항, 호 계층 구조로 구조화된 텍스트
    contract_masked: str             # 기밀 마스킹된 텍스트
    masking_map: Dict[str, str]      # 마스킹 복원용 매핑 정보
    issues: List[Dict[str, Any]]     # 1차 탐색된 독소 조항 및 위반 의심 조항 목록
    retrieved_docs: List[Dict[str, Any]]  # RAG에서 검색된 관련 법령 및 규정
    verified_issues: List[Dict[str, Any]] # 가드레일을 통과한 신뢰성 있는 이슈 목록
    final_report: str                # 복원 전 최종 분석 보고서
    email_draft: str                 # 복원 전 수정 요청 이메일 초안
    output_report: str               # 최종 복원된 위험 분석 결과 보고서
    output_email: str                # 최종 복원된 비즈니스 메일 초안
    current_node: str                # 현재 실행 중인 노드명

class LegalScreeningPipeline:
    """
    LangChain 및 LangGraph 사상을 구현한 멀티 에이전트 파이프라인 관리 클래스.
    보안성(Masking)과 신뢰성(RAG & Source Guardrail) 거버넌스가 적용된 전체 흐름을 통제합니다.
    """
    def __init__(self):
        self.masker = MaskingGuard()
        self.rag = HybridRAG()

    # Node 1: 계약서 파싱 및 전처리
    def parse_contract_node(self, state: AgentState) -> AgentState:
        print("[Node: Parser] 계약서 파싱 및 구조화 시작...")
        raw = state["contract_raw"]
        # 조, 항, 호 단위의 구조적 파싱 가상화 (여기서는 공백 정리 및 정형화)
        parsed = "\n".join([line.strip() for line in raw.split("\n") if line.strip()])
        state["contract_parsed"] = parsed
        state["current_node"] = "parser"
        return state

    # Node 2: 데이터 마스킹 (외부 API 전송 전 기밀 보호)
    def mask_pii_node(self, state: AgentState) -> AgentState:
        print("[Node: Masker] 외부 전송 전 계약서 기밀 정보 마스킹 중...")
        parsed = state["contract_parsed"]
        masked = self.masker.mask(parsed)
        state["contract_masked"] = masked
        state["masking_map"] = self.masker.de_mask_map.copy()
        state["current_node"] = "masker"
        return state

    # Node 3: 독소 조항 스크리닝 (LLM 에이전트)
    def screen_issues_node(self, state: AgentState) -> AgentState:
        print("[Node: Screener] 마스킹된 텍스트 기반 독소 조항 1차 스크리닝 중...")
        masked = state["contract_masked"]
        
        # LLM 프롬프트 엔지니어링을 통한 스크리닝 가상화
        # 실제 환경에서는 ChatOpenAI, ChatGemini 등 LLM API를 사용
        # 여기서는 계약서 패턴별 불공정 조항 탐색 규칙 시뮬레이션
        detected_issues = []
        
        # 가상 스크리닝 규칙 (하도급 및 용역 계약의 대표적 독소 조항)
        if "지식재산권" in masked or "특허권" in masked:
            if "일방" in masked or "귀속한다" in masked or "이전한다" in masked:
                detected_issues.append({
                    "id": "ISSUE_IP",
                    "title": "지식재산권 일방적 귀속 리스크",
                    "clause_text": "본 계약 하에 개발되는 모든 지식재산권은 [COMPANY_A]에게 전적으로 귀속된다.",
                    "risk_level": "HIGH",
                    "description": "수급사업자가 개발한 고유 기술이나 공동 개발 결과물에 대한 권리를 일방적으로 원사업자에게 독점 귀속시키는 조항입니다. 불공정 하도급거래 우려가 높습니다."
                })
        
        if "지체상금" in masked or "지연" in masked:
            # 과도한 지체상금율 검증 (예: 1000분의 3, 표준은 1000분의 0.5~1.5)
            detected_issues.append({
                "id": "ISSUE_DELAY",
                "title": "과도한 지체상금율 적용 리스크",
                "clause_text": "납품 지체 시 매 1일당 총 계약금액의 3/1000(0.3%)에 해당하는 지체상금을 지불한다.",
                "risk_level": "MEDIUM",
                "description": "통상적인 지체상금률(0.05%~0.15%) 대비 지나치게 높은 지체상금율(0.3%)이 설정되어 과도한 손해배상 부담을 질 수 있습니다."
            })
            
        if "손해배상" in masked and "한도" not in masked:
            detected_issues.append({
                "id": "ISSUE_LIABILITY",
                "title": "책임 한도 무제한 리스크",
                "clause_text": "을은 계약 불이행으로 인해 발생한 모든 손해를 배상할 책임을 진다.",
                "risk_level": "MEDIUM",
                "description": "손해배상 책임 한도가 설정되어 있지 않아, 경과실로 인한 사고 시에도 예상치 못한 막대한 배상 책임을 질 위험이 있습니다."
            })

        state["issues"] = detected_issues
        state["current_node"] = "screener"
        return state

    # Node 4: 하이브리드 RAG 법률/규정 조회
    def retrieve_laws_node(self, state: AgentState) -> AgentState:
        print("[Node: RAG_Retriever] 관련 법령 및 사내 규정 조회 중...")
        issues = state["issues"]
        all_retrieved = []
        
        for issue in issues:
            # 이슈 내용과 매칭되는 법 조항 검색
            query = f"{issue['title']} {issue['description']}"
            retrieved = self.rag.retrieve(query, top_k=1)
            all_retrieved.extend(retrieved)
            
        state["retrieved_docs"] = all_retrieved
        state["current_node"] = "rag_retriever"
        return state

    # Node 5: 소스 가드레일 검증 (할루시네이션 방지)
    def verify_with_sources_node(self, state: AgentState) -> AgentState:
        print("[Node: Guardrail] 소스 일치 여부 팩트체크 및 가드레일 적용 중...")
        issues = state["issues"]
        retrieved_docs = state["retrieved_docs"]
        
        verified = []
        # AI가 도출한 위험 요소와 RAG의 원천 데이터 매핑
        for issue in issues:
            matched_doc = None
            for doc in retrieved_docs:
                # 키워드 맥락 매칭을 통한 법적 근거 연결
                if any(kw in issue["title"] or kw in issue["description"] for kw in doc["keywords"]):
                    matched_doc = doc
                    break
            
            if matched_doc:
                # 법적 근거가 매핑된 신뢰할 수 있는 위험 요소로 승인
                issue["legal_basis"] = f"{matched_doc['category']} {matched_doc['clause']}"
                issue["legal_basis_text"] = matched_doc["content"]
                verified.append(issue)
            else:
                # 근거가 없는 경우, 할루시네이션으로 보고 보수적으로 처리하거나 사내 규정 범주로 우회
                issue["legal_basis"] = "사내 법무팀 검토 필요 (자체 지식기반)"
                issue["legal_basis_text"] = "관련 국가 법령이 직접 조항에 매핑되지 않았으므로 사내 규정에 따라 정밀 검토 요망."
                verified.append(issue)

        state["verified_issues"] = verified
        state["current_node"] = "guardrail"
        return state

    # Node 6: 결과 보고서 및 비즈니스 메일 초안 생성 (LLM 에이전트)
    def generate_report_and_email_node(self, state: AgentState) -> AgentState:
        print("[Node: Generator] 분석 보고서 및 메일 초안 작성 중...")
        issues = state["verified_issues"]
        
        # 보고서 텍스트 생성
        report_lines = [
            "### 1차 법무 스크리닝 결과 보고서",
            "본 보고서는 인공지능 법무 에이전트의 1차 분석 결과이며, 법적 효력을 갖지 않습니다.\n",
            "**[검토 요약]**",
            f"검색된 총 위험 요인은 {len(issues)}건입니다.\n",
            "---",
            "**[상세 위험 요인 분석]**"
        ]
        
        for idx, issue in enumerate(issues, 1):
            report_lines.append(
                f"{idx}. {issue['title']} (위험도: {issue['risk_level']})\n"
                f"  - 해당 조항: \"{issue['clause_text']}\"\n"
                f"  - 위험 요소: {issue['description']}\n"
                f"  - 법적 근거: {issue['legal_basis']}\n"
                f"  - 근거 세부 조항: {issue['legal_basis_text']}\n"
            )
            
        state["final_report"] = "\n".join(report_lines)

        # 메일 초안 작성
        email_lines = [
            "제목: [수정 요청] 계약서 조항 일부 수정 제안의 건\n",
            "안녕하십니까, 상대방 담당자님.",
            "보내주신 계약서를 검토하는 과정에서 공정한 파트너십 구축 및 양사 간의 원활한 업무 처리를 위하여 일부 조항에 대한 수정을 요청드리고자 합니다.\n",
            "**[주요 수정 요청 사항]**"
        ]
        
        for issue in issues:
            email_lines.append(
                f"- **{issue['title']} 관련:**\n"
                f"  - 현재: \"{issue['clause_text']}\"\n"
                f"  - 제안: 관계 법령({issue['legal_basis']})에 부합하도록 당사자 간 기여도에 따라 귀속되거나 한도를 상호 제한하는 방향으로 조정을 희망합니다."
            )
            
        email_lines.append("\n너른 양해와 검토 부탁드리며, 조율 가능한 일정 회신 주시면 감사하겠습니다.\n\n감사합니다.\n[COMPANY_B] 드림")
        state["email_draft"] = "\n".join(email_lines)
        
        state["current_node"] = "generator"
        return state

    # Node 7: 데이터 마스킹 복원 (De-masking)
    def demask_results_node(self, state: AgentState) -> AgentState:
        print("[Node: Demasker] 최종 산출물 내 마스킹 정보 복원 중...")
        # 마스커 인스턴스에 보관 중이던 de_mask_map 설정 복원
        self.masker.de_mask_map = state["masking_map"]
        
        state["output_report"] = self.masker.unmask(state["final_report"])
        state["output_email"] = self.masker.unmask(state["email_draft"])
        state["current_node"] = "demasker"
        return state

    # LangGraph Routing 조건식
    def should_continue(self, state: AgentState) -> Literal["retrieve", "end"]:
        # 이슈가 없으면 바로 생성 노드로 건너뛸 수 있는 분기 조건 정의
        if not state["issues"]:
            return "end"
        return "retrieve"

    def run(self, raw_contract: str) -> Dict[str, Any]:
        """
        LangGraph 파이프라인 시뮬레이터 실행기
        """
        # 초기 상태 정의
        state: AgentState = {
            "contract_raw": raw_contract,
            "contract_parsed": "",
            "contract_masked": "",
            "masking_map": {},
            "issues": [],
            "retrieved_docs": [],
            "verified_issues": [],
            "final_report": "",
            "email_draft": "",
            "output_report": "",
            "output_email": "",
            "current_node": "init"
        }

        # 동적 워크플로우 제어 (LangGraph 실행 구조 모사)
        state = self.parse_contract_node(state)
        state = self.mask_pii_node(state)
        state = self.screen_issues_node(state)
        
        # 조건부 엣지
        if self.should_continue(state) == "retrieve":
            state = self.retrieve_laws_node(state)
            state = self.verify_with_sources_node(state)
            
        state = self.generate_report_and_email_node(state)
        state = self.demask_results_node(state)
        
        print("LangGraph 파이프라인 처리 완료!")
        return state

# 테스트용
if __name__ == "__main__":
    test_contract = (
        "용역위탁 계약서\n"
        "발주처: 주식회사 에이비씨디 (이하 '갑')\n"
        "수급처: (주)한라소프트 (이하 '을')\n"
        "계약금: ₩45,000,000\n\n"
        "제5조 (지식재산권)\n"
        "본 계약과 관련하여 을이 제작하는 모든 산출물에 대한 지식재산권은 갑에게 일방적으로 귀속한다.\n\n"
        "제7조 (지체상금)\n"
        "을은 납기 준수 실패 시 일당 총 계약금액의 0.3%에 해당하는 지체상금을 갑에게 지급해야 한다."
    )
    
    pipeline = LegalScreeningPipeline()
    result = pipeline.run(test_contract)
    
    print("\n================== 최종 스크리닝 보고서 ==================")
    print(result["output_report"])
    print("\n================== 수정 요청 이메일 초안 ==================")
    print(result["output_email"])
