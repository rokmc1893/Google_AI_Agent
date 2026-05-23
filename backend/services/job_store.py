from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from backend.api.schemas import JobStatus, JobStatusResponse, ScreeningResult

UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "data" / "uploads"


@dataclass
class JobRecord:
    job_id: str
    filename: str
    file_type: str
    raw_text: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    parsed_at: datetime = field(default_factory=datetime.utcnow)
    status: JobStatus = "uploaded"
    screening_result: ScreeningResult | None = None
    error: str | None = None
    saved_path: str | None = None
    progress: int = 0
    current_node: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}

    def _drop_job(self, job_id: str) -> None:
        record = self._jobs.pop(job_id, None)
        if record is None:
            return

        record.raw_text = ""
        record.screening_result = None
        record.error = None
        record.saved_path = None
        record.current_node = None

    def cleanup_expired_jobs(self, ttl_minutes: int = 30) -> int:
        """Remove expired in-memory jobs during API traffic.

        This keeps demo deployments from retaining uploaded contract text
        indefinitely without introducing a scheduler, Redis, or database.
        Completed jobs are intentionally removed too: clients should fetch
        results shortly after completion in the demo environment.
        """
        if ttl_minutes <= 0:
            return 0

        cutoff = datetime.utcnow() - timedelta(minutes=ttl_minutes)
        expired_ids = [
            job_id
            for job_id, record in self._jobs.items()
            if record.created_at < cutoff
        ]
        for job_id in expired_ids:
            self._drop_job(job_id)
        return len(expired_ids)

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
        record.progress = 10
        record.current_node = "screening"
        record.started_at = datetime.utcnow()
        record.finished_at = None
        return record

    def set_completed(self, job_id: str, result: ScreeningResult) -> JobRecord:
        record = self.require(job_id)
        record.screening_result = result
        record.status = "completed"
        record.error = None
        record.progress = 100
        record.current_node = "completed"
        record.finished_at = datetime.utcnow()
        return record

    def set_failed(self, job_id: str, message: str) -> JobRecord:
        record = self.require(job_id)
        record.status = "failed"
        record.error = message
        record.current_node = "failed"
        record.finished_at = datetime.utcnow()
        return record

    def set_progress(self, job_id: str, progress: int, current_node: str | None = None) -> JobRecord:
        record = self.require(job_id)
        record.progress = max(0, min(100, progress))
        if current_node is not None:
            record.current_node = current_node
        return record

    def to_status_dto(self, job_id: str) -> JobStatusResponse:
        record = self.require(job_id)
        return JobStatusResponse(
            job_id=record.job_id,
            status=record.status,
            progress=record.progress,
            current_node=record.current_node,
            error=record.error,
            started_at=record.started_at,
            finished_at=record.finished_at,
        )


_store = JobStore()


def get_job_store() -> JobStore:
    return _store
