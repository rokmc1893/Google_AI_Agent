from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

JobStatus = Literal["uploaded", "processing", "completed", "failed"]
RiskLevel = Literal["HIGH", "MEDIUM", "LOW"]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    llm_enabled: bool = False
    rag_enabled: bool = False
    chroma_status: str = "disabled"
    embedding_model: str = ""
    langgraph_enabled: bool = False


class MetricsResponse(BaseModel):
    uptime_seconds: float = 0
    upload_count: int = 0
    screen_count: int = 0
    screen_errors: int = 0
    last_screen_ms: float | None = None
    avg_screen_ms: float | None = None
    screen_sla_seconds: int = 180
    sla_met_last: bool | None = None


class ErrorResponse(BaseModel):
    code: str
    message: str


class UploadResponse(BaseModel):
    job_id: str
    filename: str
    file_type: str
    text_preview: str
    char_count: int


class ScreenRequest(BaseModel):
    job_id: str


class ScreenResponse(BaseModel):
    job_id: str
    status: JobStatus


class RetrievedDoc(BaseModel):
    id: str = ""
    category: str = ""
    clause: str = ""
    content: str = ""


class RiskIssue(BaseModel):
    id: str
    title: str
    clause_text: str = ""
    risk_level: RiskLevel = "MEDIUM"
    description: str = ""
    legal_basis: str | None = None
    legal_basis_text: str | None = None
    citations: list[str] = Field(default_factory=list)


class ScreeningResult(BaseModel):
    job_id: str
    status: JobStatus
    issues: list[RiskIssue] = Field(default_factory=list)
    verified_issues: list[RiskIssue] = Field(default_factory=list)
    retrieved_docs: list[RetrievedDoc] = Field(default_factory=list)
    output_report: str = ""
    output_email: str = ""
    contract_masked: str | None = None
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    safety_score: int | None = None


class EmailDraftRequest(BaseModel):
    job_id: str


class EmailDraftResponse(BaseModel):
    job_id: str
    email_draft: str
