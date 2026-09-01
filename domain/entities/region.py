"""
RAVEN Region Domain Entity

Defines the Region entity for multi-region operational reliability and distributed policy synchronization.
"""

from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from domain.enums import RegionStatus


class Region(BaseModel):
    """
    Region domain entity representing a distinct deployment region.
    """

    region_id: str = Field(..., description="Unique region identifier, e.g. ap-south-1, us-east-1")
    name: str = Field(..., min_length=1, description="Human-readable region name")
    status: RegionStatus = Field(default=RegionStatus.ACTIVE, description="Region operational status")
    is_primary: bool = Field(default=False, description="Whether region is designated primary coordinator")
    last_synced_at: datetime | None = Field(default=None, description="Last successful synchronization timestamp in UTC")
    health_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Region health score (0.0 to 1.0)")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Region registration timestamp in UTC",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Region last update timestamp in UTC",
    )

    @field_validator("region_id")
    @classmethod
    def validate_region_id(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not v_clean or len(v_clean) < 3:
            raise ValueError("region_id must be a non-empty string of at least 3 characters")
        return v_clean
