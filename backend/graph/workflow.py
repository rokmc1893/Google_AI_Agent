from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

logger = logging.getLogger(__name__)

_LANGGRAPH_AVAILABLE = False
_IMPORT_ERROR: str | None = None

try:
    from langgraph.graph import END, START, StateGraph

    _LANGGRAPH_AVAILABLE = True
except ImportError as exc:
    _IMPORT_ERROR = str(exc)


if TYPE_CHECKING:
    from backend.agent_graph import AgentState, LegalScreeningPipeline


def langgraph_available() -> bool:
    return _LANGGRAPH_AVAILABLE


def langgraph_import_error() -> str | None:
    return _IMPORT_ERROR


def compile_screening_graph(pipeline: LegalScreeningPipeline) -> Any:
    """
    LegalScreeningPipeline 노드를 LangGraph StateGraph로 연결.

    Flow:
      START → parser → masker → law_context_pre → screener
        ├─ (issues) → law_context_post → rag_retriever → guardrail → generator → demasker → END
        └─ (no issues) → generator → demasker → END
    """
    if not _LANGGRAPH_AVAILABLE:
        raise RuntimeError(
            f"langgraph 패키지를 import할 수 없습니다: {_IMPORT_ERROR}"
        )

    from backend.agent_graph import AgentState

    graph = StateGraph(AgentState)

    graph.add_node("parser", pipeline.parse_contract_node)
    graph.add_node("masker", pipeline.mask_pii_node)
    graph.add_node("law_context_pre", pipeline.retrieve_law_context_node)
    graph.add_node("screener", pipeline.screen_issues_node)
    graph.add_node("law_context_post", pipeline.retrieve_law_context_node)
    graph.add_node("rag_retriever", pipeline.retrieve_laws_node)
    graph.add_node("guardrail", pipeline.verify_with_sources_node)
    graph.add_node("generator", pipeline.generate_report_and_email_node)
    graph.add_node("demasker", pipeline.demask_results_node)

    graph.add_edge(START, "parser")
    graph.add_edge("parser", "masker")
    graph.add_edge("masker", "law_context_pre")
    graph.add_edge("law_context_pre", "screener")

    graph.add_conditional_edges(
        "screener",
        pipeline.should_continue,
        {
            "retrieve": "law_context_post",
            "end": "generator",
        },
    )

    graph.add_edge("law_context_post", "rag_retriever")
    graph.add_edge("rag_retriever", "guardrail")
    graph.add_edge("guardrail", "generator")
    graph.add_edge("generator", "demasker")
    graph.add_edge("demasker", END)

    compiled = graph.compile()
    logger.info("[LangGraph] screening graph compiled (9 nodes)")
    return compiled
