"""
RAVEN FinancialEvent Domain Entity

Defines immutable raw and normalized financial event models.
Provides SHA256 event hashing for deduplication.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from pydantic import BaseModel, Field


class FinancialEvent(BaseModel):
    """
    FinancialEvent entity representing normalized input events ingested into RAVEN.
    """

    id: str = Field(..., description="Unique internal event ID, e.g. evt_01H...")
    event_hash: str = Field(..., description="SHA256 hex digest of raw normalized payload for deduplication")
    event_type: str = Field(..., description="Event type identifier, e.g. payment.captured, payment.failed")
    gateway_event_id: str | None = Field(None, description="External gateway event ID if provided")
    entity_id: str = Field(..., description="Primary entity ID (e.g. payment_id or order_id)")
    order_id: str | None = Field(None, description="Associated Order ID")
    merchant_id: str = Field(..., description="Associated Merchant ID")
    customer_id: str | None = Field(None, description="Associated Customer ID")
    amount_minor_units: int | None = Field(None, ge=0, description="Transaction amount in minor units")
    currency: str = Field("INR", description="ISO 4217 currency code")
    payload: dict[str, Any] = Field(default_factory=dict, description="Raw event payload snapshot")
    occurred_at: datetime = Field(..., description="Gateway event occurrence timestamp in UTC")
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Ingestion timestamp in UTC",
    )
    sequence_number: int = Field(1, ge=1, description="Sequence tie-breaker number")

    @staticmethod
    def compute_hash(payload: dict[str, Any]) -> str:
        """
        Computes canonical SHA256 hex digest for a JSON body payload.
        Ensures consistent key ordering before hashing.
        """
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
