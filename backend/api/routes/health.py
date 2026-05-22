from datetime import datetime

from fastapi import APIRouter

from backend.api.schemas import HealthResponse
from backend.config import get_settings
from backend.rag.status import get_rag_status

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    rag_on, chroma_status, _ = get_rag_status()
    return HealthResponse(
        status="ok",
        version="0.1.0",
        timestamp=datetime.utcnow(),
        llm_enabled=settings.llm_enabled,
        rag_enabled=rag_on,
        chroma_status=chroma_status,
        embedding_model=settings.embedding_model,
        langgraph_enabled=settings.langgraph_enabled,
    )
