"""
legal_review_agent.modules
법무 검토 자동화 에이전트 핵심 모듈 패키지.
"""
from modules.parser import ContractParser, ParsedContract, parse_contract_file
from modules.masking import MaskingEngine, MaskingResult, mask_text, unmask_text
from modules.rag_retriever import (
    HybridRetriever,
    LegalDocument,
    RetrievalResult,
    SourceGuardrail,
    build_retriever_from_json,
    retrieve_relevant_clauses,
)
from modules.agent_pipeline import (
    AgentState,
    LegalReviewPipeline,
    RiskLevel,
    RiskReport,
    ScreeningResult,
    run_legal_review,
)
from modules.law_api_ingester import (
    APIError,
    LawAPIClient,
    LawDataIngester,
)

__all__ = [
    # 파서
    "ContractParser", "ParsedContract", "parse_contract_file",
    # 마스킹
    "MaskingEngine", "MaskingResult", "mask_text", "unmask_text",
    # RAG
    "HybridRetriever", "LegalDocument", "RetrievalResult",
    "SourceGuardrail", "build_retriever_from_json", "retrieve_relevant_clauses",
    # 파이프라인
    "AgentState", "LegalReviewPipeline", "RiskLevel", "RiskReport",
    "ScreeningResult", "run_legal_review",
    # 법령 API 수집기
    "APIError", "LawAPIClient", "LawDataIngester",
]
