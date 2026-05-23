from fastapi import APIRouter

from backend.api.schemas import MetricsResponse
from backend.config import get_settings
from backend.services.job_store import get_job_store
from backend.services.metrics import get_metrics_store

router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics() -> MetricsResponse:
    _ = get_job_store().cleanup_expired_jobs(get_settings().job_ttl_minutes)
    data = get_metrics_store().snapshot()
    return MetricsResponse(**data)
