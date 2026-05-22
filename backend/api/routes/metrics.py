from fastapi import APIRouter

from backend.api.schemas import MetricsResponse
from backend.services.metrics import get_metrics_store

router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics() -> MetricsResponse:
    data = get_metrics_store().snapshot()
    return MetricsResponse(**data)
