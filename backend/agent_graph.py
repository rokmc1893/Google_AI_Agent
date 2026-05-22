from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Literal, TypedDict

from backend.config import get_settings
from backend.hybrid_rag import HybridRAG
from backend.llm_client import get_llm_client
from backend.masking_guard import MaskingGuard
from backend.prompts import (
    REPORT_EMAIL_SYSTEM,
    REPORT_EMAIL_USER,
    SCREEN_ISSUES_GROUNDED_EXTRA,
    SCREEN_ISSUES_SYSTEM,
    SCREEN_ISSUES_USER,
)
from backend.rag.retriever import build_law_context

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    contract_raw: str
    contract_parsed: str
    contract_masked: str
    masking_map: Dict[str, str]
    issues: List[Dict[str, Any]]
    retrieved_docs: List[Dict[str, Any]]
    verified_issues: List[Dict[str, Any]]
    final_report: str
    email_draft: str
    output_report: str
    output_email: str
    current_node: str
    law_context: str
    related_laws: List[Dict[str, Any]]
    retrieved_chunks: List[Dict[str, Any]]


class LegalScreeningPipeline:
    """
    법무 계약서 스크리닝 파이프라인.
    Phase 7: LangGraph StateGraph 실행 (USE_LANGGRAPH=true, 패키지 설치 시)
    """

    def __init__(self) -> None:
        self.masker = MaskingGuard()
        self.rag = HybridRAG()
        self.settings = get_settings()
        self.llm = get_llm_client()
        self._compiled_graph = None
        if self.settings.langgraph_enabled:
            from backend.graph.workflow import compile_screening_graph

            self._compiled_graph = compile_screening_graph(self)
            print("[LangGraph] StateGraph 컴파일 완료 — invoke 모드")

    def parse_contract_node(self, state: AgentState) -> AgentState:
        print("[Node: Parser] 계약서 파싱 및 구조화 시작...")
        raw = state["contract_raw"]
        parsed = "\n".join([line.strip() for line in raw.split("\n") if line.strip()])
        state["contract_parsed"] = parsed
        state["current_node"] = "parser"
        return state

    def mask_pii_node(self, state: AgentState) -> AgentState:
        print("[Node: Masker] 외부 전송 전 계약서 기밀 정보 마스킹 중...")
        parsed = state["contract_parsed"]
        masked = self.masker.mask(parsed)
        state["contract_masked"] = masked
        state["masking_map"] = self.masker.de_mask_map.copy()
        state["current_node"] = "masker"
        return state

    def retrieve_law_context_node(self, state: AgentState) -> AgentState:
        print("[Node: LawContext] 법령 API + RAG 맥락 수집 중...")
        try:
            ctx = build_law_context(
                state["contract_masked"],
                state.get("issues") or None,
                filename="screening_contract",
            )
            state["law_context"] = ctx.get("law_context", "")
            state["related_laws"] = ctx.get("related_laws", [])
            state["retrieved_chunks"] = ctx.get("retrieved_chunks", [])
            for doc in ctx.get("retrieved_docs", []):
                existing_ids = {d.get("id") for d in state["retrieved_docs"]}
                if doc.get("id") not in existing_ids:
                    state["retrieved_docs"].append(doc)
            print(
                f"[Node: LawContext] OK laws={len(state['related_laws'])} "
                f"chunks={len(state['retrieved_chunks'])} context_len={len(state['law_context'])}"
            )
        except Exception as exc:
            logger.warning("[Node: LawContext] fallback empty: %s", exc)
            print(f"[Node: LawContext] fallback ({exc})")
            state["law_context"] = ""
            state["related_laws"] = []
            state["retrieved_chunks"] = []

        state["current_node"] = "law_context"
        return state

    def _screen_issues_rules(self, masked: str) -> List[Dict[str, Any]]:
        detected_issues: List[Dict[str, Any]] = []

        if "지식재산권" in masked or "특허권" in masked:
            if "일방" in masked or "귀속한다" in masked or "이전한다" in masked:
                detected_issues.append({
                    "id": "ISSUE_IP",
                    "title": "지식재산권 일방적 귀속 리스크",
                    "clause_text": "본 계약 하에 개발되는 모든 지식재산권은 [COMPANY_A]에게 전적으로 귀속된다.",
                    "risk_level": "HIGH",
                    "description": "수급사업자가 개발한 고유 기술이나 공동 개발 결과물에 대한 권리를 일방적으로 원사업자에게 독점 귀속시키는 조항입니다.",
                })

        if "지체상금" in masked or "지연" in masked:
            detected_issues.append({
                "id": "ISSUE_DELAY",
                "title": "과도한 지체상금율 적용 리스크",
                "clause_text": "납품 지체 시 매 1일당 총 계약금액의 3/1000(0.3%)에 해당하는 지체상금을 지불한다.",
                "risk_level": "MEDIUM",
                "description": "통상적인 지체상금률 대비 지나치게 높은 지체상금율이 설정되어 과도한 손해배상 부담을 질 수 있습니다.",
            })

        if "손해배상" in masked and "한도" not in masked:
            detected_issues.append({
                "id": "ISSUE_LIABILITY",
                "title": "책임 한도 무제한 리스크",
                "clause_text": "을은 계약 불이행으로 인해 발생한 모든 손해를 배상할 책임을 진다.",
                "risk_level": "MEDIUM",
                "description": "손해배상 책임 한도가 설정되어 있지 않아 막대한 배상 책임을 질 위험이 있습니다.",
            })

        return detected_issues

    def _screen_issues_llm(self, masked: str, law_context: str) -> List[Dict[str, Any]]:
        user = SCREEN_ISSUES_USER.format(
            contract_masked=masked,
            law_context=law_context or "(법령 맥락 없음)",
        )
        system = SCREEN_ISSUES_SYSTEM
        if law_context.strip():
            system += SCREEN_ISSUES_GROUNDED_EXTRA
        data = self.llm.generate_json(system, user)
        issues = data.get("issues", [])
        if not isinstance(issues, list):
            raise ValueError("LLM 응답에 issues 배열이 없습니다.")
        normalized: List[Dict[str, Any]] = []
        for i, item in enumerate(issues):
            if not isinstance(item, dict):
                continue
            level = str(item.get("risk_level", "MEDIUM")).upper()
            if level not in ("HIGH", "MEDIUM", "LOW"):
                level = "MEDIUM"
            entry = {
                "id": str(item.get("id") or f"ISSUE_LLM_{i + 1:03d}"),
                "title": str(item.get("title", "미명명 리스크")),
                "clause_text": str(item.get("clause_text", "")),
                "risk_level": level,
                "description": str(item.get("description", "")),
            }
            if item.get("legal_reference"):
                entry["legal_reference"] = str(item["legal_reference"])
            normalized.append(entry)
        return normalized

    def screen_issues_node(self, state: AgentState) -> AgentState:
        print("[Node: Screener] 마스킹된 텍스트 기반 독소 조항 1차 스크리닝 중...")
        masked = state["contract_masked"]
        law_context = state.get("law_context", "")

        if self.llm.enabled:
            try:
                mode = "Gemini+RAG" if law_context.strip() else "Gemini"
                print(f"[Node: Screener] {mode} LLM 스크리닝")
                state["issues"] = self._screen_issues_llm(masked, law_context)
            except Exception as exc:
                logger.warning("LLM 스크리닝 실패, 규칙 fallback: %s", exc)
                print(f"[Node: Screener] LLM 실패 → 규칙 fallback ({exc})")
                state["issues"] = self._screen_issues_rules(masked)
        else:
            print("[Node: Screener] 규칙 기반 스크리닝 (LLM 비활성)")
            state["issues"] = self._screen_issues_rules(masked)

        state["current_node"] = "screener"
        return state

    def retrieve_laws_node(self, state: AgentState) -> AgentState:
        print("[Node: RAG_Retriever] 관련 법령 및 사내 규정 조회 중...")
        issues = state["issues"]
        all_retrieved = list(state.get("retrieved_docs", []))

        for issue in issues:
            query = f"{issue['title']} {issue['description']}"
            retrieved = self.rag.retrieve(query, top_k=1)
            all_retrieved.extend(retrieved)

        state["retrieved_docs"] = all_retrieved
        state["current_node"] = "rag_retriever"
        return state

    def verify_with_sources_node(self, state: AgentState) -> AgentState:
        print("[Node: Guardrail] 소스 일치 여부 팩트체크 및 가드레일 적용 중...")
        issues = state["issues"]
        retrieved_docs = state["retrieved_docs"]

        verified = []
        for issue in issues:
            matched_doc = None
            for doc in retrieved_docs:
                keywords = doc.get("keywords") or []
                if keywords and any(
                    kw in issue["title"] or kw in issue["description"] for kw in keywords
                ):
                    matched_doc = doc
                    break
                if doc.get("clause") and doc["clause"] in issue.get("description", ""):
                    matched_doc = doc
                    break

            if matched_doc:
                issue["legal_basis"] = f"{matched_doc.get('category', 'RAG')} {matched_doc.get('clause', '')}"
                issue["legal_basis_text"] = matched_doc.get("content", "")
            elif issue.get("legal_reference"):
                issue["legal_basis"] = "RAG/법령 맥락"
                issue["legal_basis_text"] = issue["legal_reference"]
            else:
                issue["legal_basis"] = "사내 법무팀 검토 필요 (자체 지식기반)"
                issue["legal_basis_text"] = "관련 국가 법령이 직접 조항에 매핑되지 않았으므로 사내 규정에 따라 정밀 검토 요망."
            verified.append(issue)

        state["verified_issues"] = verified
        state["current_node"] = "guardrail"
        return state

    def _report_law_sections(self, state: AgentState) -> str:
        lines = []
        if state.get("related_laws"):
            lines.append("## 관련 법령 (API/로컬DB)")
            for law in state["related_laws"][:5]:
                lines.append(f"- **{law.get('title')}**: {str(law.get('summary', ''))[:200]}")
        if state.get("retrieved_chunks"):
            lines.append("## RAG 검색 근거")
            for ch in state["retrieved_chunks"][:5]:
                lines.append(f"- (score={ch.get('score', 0):.2f}) {ch.get('content', '')[:200]}")
        lines.append(
            "## 신뢰도 안내\n"
            "- 본 문서는 AI 1차 스크리닝 결과입니다.\n"
            "- RAG·법령 API 근거는 참고용이며 최종 판단은 법무팀 검토가 필요합니다."
        )
        return "\n".join(lines)

    def _generate_report_rules(self, state: AgentState) -> tuple[str, str]:
        issues = state["verified_issues"]
        report_lines = [
            "### 1차 법무 스크리닝 결과 보고서",
            "본 보고서는 인공지능 법무 에이전트의 1차 분석 결과이며, 법적 효력을 갖지 않습니다.\n",
            "**[검토 요약]**",
            f"검색된 총 위험 요인은 {len(issues)}건입니다.\n",
            "---",
            self._report_law_sections(state),
            "---",
            "**[상세 위험 요인 분석]**",
        ]

        for idx, issue in enumerate(issues, 1):
            report_lines.append(
                f"{idx}. {issue['title']} (위험도: {issue['risk_level']})\n"
                f"  - 해당 조항: \"{issue['clause_text']}\"\n"
                f"  - 위험 요소: {issue['description']}\n"
                f"  - 법적 근거: {issue.get('legal_basis', 'N/A')}\n"
                f"  - 근거 세부 조항: {issue.get('legal_basis_text', 'N/A')}\n"
            )

        email_lines = [
            "제목: [수정 요청] 계약서 조항 일부 수정 제안의 건\n",
            "안녕하십니까, 상대방 담당자님.",
            "보내주신 계약서를 검토하는 과정에서 공정한 파트너십 구축을 위해 일부 조항 수정을 요청드립니다.\n",
            "**[주요 수정 요청 사항]**",
        ]

        for issue in issues:
            email_lines.append(
                f"- **{issue['title']} 관련:**\n"
                f"  - 현재: \"{issue['clause_text']}\"\n"
                f"  - 제안: 관계 법령({issue.get('legal_basis', 'N/A')})에 부합하도록 조정을 희망합니다."
            )

        email_lines.append(
            "\n너른 양해와 검토 부탁드리며, 조율 가능한 일정 회신 주시면 감사하겠습니다.\n\n감사합니다.\n[COMPANY_B] 드림"
        )
        return "\n".join(report_lines), "\n".join(email_lines)

    def _generate_report_llm(self, state: AgentState) -> tuple[str, str]:
        issues = state["verified_issues"]
        user = REPORT_EMAIL_USER.format(
            issues_json=json.dumps(issues, ensure_ascii=False, indent=2),
            law_context=state.get("law_context", ""),
            related_laws_json=json.dumps(
                state.get("related_laws", []), ensure_ascii=False, indent=2
            ),
        )
        data = self.llm.generate_json(REPORT_EMAIL_SYSTEM, user)
        report = str(data.get("final_report", "")).strip()
        email = str(data.get("email_draft", "")).strip()
        if not report or not email:
            raise ValueError("LLM 보고서/이메일 필드 누락")
        extra = self._report_law_sections(state)
        if "## 관련 법령" not in report and extra:
            report = report + "\n\n---\n\n" + extra
        return report, email

    def generate_report_and_email_node(self, state: AgentState) -> AgentState:
        print("[Node: Generator] 분석 보고서 및 메일 초안 작성 중...")
        issues = state["verified_issues"]

        if not issues:
            state["final_report"] = "### 1차 법무 스크리닝 결과\n특이 리스크 조항이 탐지되지 않았습니다."
            state["email_draft"] = "제목: [검토 완료] 계약서 1차 스크리닝 결과 회신\n\n특이 수정 요청 사항 없이 검토를 마쳤습니다."
        elif self.llm.enabled:
            try:
                print("[Node: Generator] Gemini LLM 보고서·메일 생성 (RAG grounded)")
                report, email = self._generate_report_llm(state)
                state["final_report"] = report
                state["email_draft"] = email
            except Exception as exc:
                logger.warning("LLM 보고서 생성 실패, 규칙 fallback: %s", exc)
                print(f"[Node: Generator] LLM 실패 → 규칙 fallback ({exc})")
                report, email = self._generate_report_rules(state)
                state["final_report"] = report
                state["email_draft"] = email
        else:
            report, email = self._generate_report_rules(state)
            state["final_report"] = report
            state["email_draft"] = email

        state["current_node"] = "generator"
        return state

    def demask_results_node(self, state: AgentState) -> AgentState:
        print("[Node: Demasker] 최종 산출물 내 마스킹 정보 복원 중...")
        self.masker.de_mask_map = state["masking_map"]
        state["output_report"] = self.masker.unmask(state["final_report"])
        state["output_email"] = self.masker.unmask(state["email_draft"])
        state["current_node"] = "demasker"
        return state

    def should_continue(self, state: AgentState) -> Literal["retrieve", "end"]:
        if not state["issues"]:
            return "end"
        return "retrieve"

    def _initial_state(self, raw_contract: str) -> AgentState:
        return {
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
            "current_node": "init",
            "law_context": "",
            "related_laws": [],
            "retrieved_chunks": [],
        }

    def _run_manual(self, state: AgentState) -> AgentState:
        """Phase 1~6 수동 오케스트레이션 (LangGraph fallback)."""
        state = self.parse_contract_node(state)
        state = self.mask_pii_node(state)
        state = self.retrieve_law_context_node(state)
        state = self.screen_issues_node(state)

        if self.should_continue(state) == "retrieve":
            state = self.retrieve_law_context_node(state)
            state = self.retrieve_laws_node(state)
            state = self.verify_with_sources_node(state)

        state = self.generate_report_and_email_node(state)
        state = self.demask_results_node(state)
        return state

    def run(self, raw_contract: str) -> Dict[str, Any]:
        state = self._initial_state(raw_contract)

        if self._compiled_graph is not None:
            print("[LangGraph] graph.invoke() 실행...")
            result = self._compiled_graph.invoke(state)
            print("LangGraph 파이프라인 처리 완료! (StateGraph)")
            return result

        print("[LangGraph] 수동 파이프라인 fallback (USE_LANGGRAPH=false 또는 미설치)")
        result = self._run_manual(state)
        print("LangGraph 파이프라인 처리 완료! (manual)")
        return result


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
    print(result["output_report"][:800])
    print("\n================== 수정 요청 이메일 초안 ==================")
    print(result["output_email"][:400])
