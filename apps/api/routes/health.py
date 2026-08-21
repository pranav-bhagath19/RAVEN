"""
Health Router Module

Exposes GET /health and GET /api/v1/health endpoints returning service status.
"""

from fastapi import APIRouter
from apps.api.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
@router.get("/api/v1/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Returns deterministic service health status."""
    return HealthResponse(status="ok", service="raven")
