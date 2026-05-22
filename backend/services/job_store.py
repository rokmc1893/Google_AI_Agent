from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.api.schemas import JobStatus, ScreeningResult

UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "data" / "uploads"


@dataclass
class JobRecord:
    job_id: str
    filename: str
    file_type: str
    raw_text: str
    parsed_at: datetime = field(default_factory=datetime.utcnow)
    status: JobStatus = "uploaded"
    screening_result: ScreeningResult | None = None
    error: str | None = None
    saved_path: str | None = None


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}

    def create(
        self,
        filename: str,
        file_type: str,
        raw_text: str,
        file_bytes: bytes | None = None,
    ) -> JobRecord:
        job_id = str(uuid.uuid4())
        saved_path: str | None = None

        if file_bytes is not None:
            job_dir = UPLOAD_ROOT / job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            dest = job_dir / filename
            dest.write_bytes(file_bytes)
            saved_path = str(dest)

        record = JobRecord(
            job_id=job_id,
            filename=filename,
            file_type=file_type,
            raw_text=raw_text,
            saved_path=saved_path,
            status="uploaded",
        )
        self._jobs[job_id] = record
        return record

    def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)

    def require(self, job_id: str) -> JobRecord:
        record = self.get(job_id)
        if record is None:
            raise KeyError(job_id)
        return record

    def set_processing(self, job_id: str) -> JobRecord:
        record = self.require(job_id)
        record.status = "processing"
        record.error = None
        return record

    def set_completed(self, job_id: str, result: ScreeningResult) -> JobRecord:
        record = self.require(job_id)
        record.screening_result = result
        record.status = "completed"
        record.error = None
        return record

    def set_failed(self, job_id: str, message: str) -> JobRecord:
        record = self.require(job_id)
        record.status = "failed"
        record.error = message
        return record


_store = JobStore()


def get_job_store() -> JobStore:
    return _store
