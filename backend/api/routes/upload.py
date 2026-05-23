from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from backend.api.schemas import UploadResponse
from backend.config import get_settings
from backend.services.job_store import get_job_store
from backend.services.metrics import get_metrics_store
from backend.services.parser import PREVIEW_LEN, parse_upload

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_contract(file: Annotated[UploadFile, File(...)]) -> UploadResponse:
    settings = get_settings()
    parsed = await parse_upload(file, settings.max_upload_bytes)

    # 저장용: parse_upload 내부에서 이미 read됨 → job_store는 텍스트만 저장해도 Phase1 충분
    store = get_job_store()
    _ = store.cleanup_expired_jobs(settings.job_ttl_minutes)
    record = store.create(
        filename=parsed.filename,
        file_type=parsed.file_type,
        raw_text=parsed.text,
        file_bytes=None,
    )

    preview = parsed.text[:PREVIEW_LEN]
    if len(parsed.text) > PREVIEW_LEN:
        preview += "…"

    get_metrics_store().record_upload()

    return UploadResponse(
        job_id=record.job_id,
        filename=record.filename,
        file_type=record.file_type,
        text_preview=preview,
        char_count=len(parsed.text),
    )
