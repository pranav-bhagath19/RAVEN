"""
RAVEN Operations Regions Router Module

Exposes read-only operational telemetry and control endpoints for multi-region infrastructure:
GET  /api/v1/operations/regions
GET  /api/v1/operations/regions/{region_id}
GET  /api/v1/operations/regions/{region_id}/health
POST /api/v1/operations/regions/{region_id}/status
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from apps.api.auth import UserIdentity, require_permission
from domain.entities.region import Region
from domain.enums import RegionStatus
from policies.failover import RegionalFailoverManager

router = APIRouter(prefix="/api/v1/operations/regions", tags=["Multi-Region Reliability"])

# Shared in-memory failover manager instance for API operations
_shared_failover_manager = RegionalFailoverManager()
_shared_failover_manager.register_region(Region(region_id="ap-south-1", name="Asia Pacific (Mumbai)", is_primary=True, status=RegionStatus.ACTIVE))
_shared_failover_manager.register_region(Region(region_id="us-east-1", name="US East (N. Virginia)", is_primary=False, status=RegionStatus.ACTIVE))
_shared_failover_manager.register_region(Region(region_id="eu-west-1", name="Europe (Ireland)", is_primary=False, status=RegionStatus.ACTIVE))


class RegionStatusUpdateRequest(BaseModel):
    status: RegionStatus = Field(..., description="Target region operational status")
    health_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Health score (0.0 to 1.0)")


@router.get("", response_model=list[dict[str, Any]])
def list_regions(
    user: UserIdentity = Depends(require_permission("REGION_READ")),
) -> list[dict[str, Any]]:
    """Lists all registered deployment regions."""
    return [r.model_dump(mode="json") for r in _shared_failover_manager.regions.values()]


@router.get("/{region_id}", response_model=dict[str, Any])
def get_region_details(
    region_id: str,
    user: UserIdentity = Depends(require_permission("REGION_READ")),
) -> dict[str, Any]:
    """Retrieves specific region details."""
    reg = _shared_failover_manager.get_region(region_id)
    if not reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Region '{region_id}' not found."}},
        )
    return reg.model_dump(mode="json")


@router.get("/{region_id}/health", response_model=dict[str, Any])
def get_region_health(
    region_id: str,
    user: UserIdentity = Depends(require_permission("REGION_READ")),
) -> dict[str, Any]:
    """Retrieves specific region health score and operational status."""
    reg = _shared_failover_manager.get_region(region_id)
    if not reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Region '{region_id}' not found."}},
        )
    return {
        "region_id": reg.region_id,
        "status": reg.status,
        "health_score": reg.health_score,
        "is_primary": reg.is_primary,
        "is_healthy": (reg.status == RegionStatus.ACTIVE and reg.health_score > 0.0),
    }


@router.post("/{region_id}/status", response_model=dict[str, Any])
def update_region_status(
    region_id: str,
    payload: RegionStatusUpdateRequest,
    user: UserIdentity = Depends(require_permission("REPLICATION_CONTROL")),
) -> dict[str, Any]:
    """Updates operational status and health score for a region."""
    reg = _shared_failover_manager.get_region(region_id)
    if not reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Region '{region_id}' not found."}},
        )
    res = _shared_failover_manager.update_region_status(
        region_id=region_id,
        status=payload.status,
        health_score=payload.health_score,
    )
    return res.model_dump(mode="json")
