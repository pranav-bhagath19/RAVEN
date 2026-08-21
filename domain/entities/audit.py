"""
RAVEN AuditEvent Domain Entity

Defines append-only audit records with controlled write access.
"""

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from domain.enums import ActorType


class AuditEvent(BaseModel):
    """
    AuditEvent entity for append-only audit logging with controlled write access.
    """

    id: str = Field(..., description="Unique Audit Event ID, e.g. aud_01H...")
    trace_id: str = Field(..., description="Global correlation trace ID")
    entity_type: str = Field(..., description="Target entity type (e.g. PAYMENT, POLICY, ACTION)")
    entity_id: str = Field(..., description="Target entity ID")
    actor_type: ActorType = Field(..., description="Actor category initiating event")
    action: str = Field(..., description="Operation performed (e.g. INGESTION, POLICY_APPROVE)")
    payload_snapshot: dict[str, Any] = Field(default_factory=dict, description="Operation snapshot")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Event record creation timestamp UTC",
    )
