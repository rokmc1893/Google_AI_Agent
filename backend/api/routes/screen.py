import time

from fastapi import APIRouter, HTTPException

from backend.api.schemas import (
    EmailDraftRequest,
    EmailDraftResponse,
    ErrorResponse,
    ScreenRequest,
    ScreenResponse,
    ScreeningResult,
)
from backend.services.job_store import get_job_store
from backend.services.metrics import get_metrics_store
from backend.services.pipeline_service import run_screening

router = APIRouter()


@router.post("/screen", response_model=ScreenResponse)
def screen_contract(body: ScreenRequest) -> ScreenResponse:
    store = get_job_store()
    try:
        record = store.require(body.job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.") from None

    if record.status == "completed" and record.screening_result:
        return ScreenResponse(job_id=body.job_id, status="completed")

    store.set_processing(body.job_id)
    started = time.perf_counter()
    metrics = get_metrics_store()
    try:
        result = run_screening(body.job_id, record.raw_text)
        duration_ms = (time.perf_counter() - started) * 1000
        metrics.record_screen(duration_ms)
        store.set_completed(body.job_id, result)
        return ScreenResponse(job_id=body.job_id, status="completed")
    except Exception as exc:
        duration_ms = (time.perf_counter() - started) * 1000
        metrics.record_screen(duration_ms, error=True)
        store.set_failed(body.job_id, str(exc))
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(code="SCREEN_FAILED", message=str(exc)).model_dump(),
        ) from exc


@router.get("/result/{job_id}", response_model=ScreeningResult)
def get_result(job_id: str) -> ScreeningResult:
    store = get_job_store()
    record = store.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    if record.screening_result is None:
        raise HTTPException(
            status_code=404,
            detail="스크리닝 결과가 없습니다. POST /api/screen을 먼저 호출하세요.",
        )
    return record.screening_result


@router.post("/email-draft", response_model=EmailDraftResponse)
def get_email_draft(body: EmailDraftRequest) -> EmailDraftResponse:
    store = get_job_store()
    record = store.get(body.job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    if record.screening_result is None:
        raise HTTPException(status_code=404, detail="스크리닝 결과가 없습니다.")
    return EmailDraftResponse(
        job_id=body.job_id,
        email_draft=record.screening_result.output_email,
    )
