"""
RAVEN FinancialEvent Domain Entity

Defines normalized input financial event models with canonical SHA-256 event hashing.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import Any
from pydantic import BaseModel, Field
from domain.values.money import Money


class FinancialEvent(BaseModel):
    """
    FinancialEvent entity representing normalized input events ingested into RAVEN.
    """

    id: str = Field(..., description="Unique internal event ID, e.g. evt_01H...")
    event_hash: str = Field(..., description="SHA256 hex digest of raw normalized payload for deduplication")
    event_type: str = Field(..., description="Event type identifier (e.g. payment.captured, payment.failed)")
    gateway_event_id: str | None = Field(default=None, description="External gateway event ID if provided")
    entity_id: str = Field(..., description="Primary entity ID (e.g. payment_id or order_id)")
    order_id: str | None = Field(default=None, description="Associated Order ID")
    merchant_id: str = Field(..., description="Associated Merchant ID")
    customer_id: str | None = Field(default=None, description="Associated Customer ID")
    amount: Money | None = Field(default=None, description="Transaction amount Money value object")
    payload: dict[str, Any] = Field(default_factory=dict, description="Raw event payload snapshot")
    occurred_at: datetime = Field(..., description="Gateway event occurrence timestamp in UTC")
    received_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Ingestion timestamp in UTC",
    )
    sequence_number: int = Field(default=1, ge=1, description="Sequence tie-breaker number")

    @property
    def currency(self) -> str:
        """Returns event currency ISO code."""
        if self.amount:
            return self.amount.currency
        return str(self.payload.get("currency", "INR")).upper()

    @staticmethod
    def compute_canonical_hash(payload: dict[str, Any]) -> str:
        """
        Computes canonical SHA256 hex digest for a dictionary payload.
        Ensures key order independence via sort_keys=True.
        Independent of dictionary iteration order or timestamps generated during hashing.
        """
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_hash(payload: dict[str, Any]) -> str:
        """Alias for compute_canonical_hash."""
        return FinancialEvent.compute_canonical_hash(payload)
