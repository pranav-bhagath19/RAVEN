"""
RAVEN Verification Agent Models

Defines VerificationResult model detailing post-intervention revenue attribution.
"""

from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field
from domain.values.money import Money


class VerificationResult(BaseModel):
    """
    VerificationResult detailing deterministic revenue attribution post-action execution.
    """

    action_id: str = Field(..., description="Executed Recovery Action ID")
    payment_id: str = Field(..., description="Target Payment ID")
    is_recovered: bool = Field(..., description="Whether revenue was genuinely recovered")
    recovered_amount: Money = Field(..., description="Amount of recovered revenue Money object")
    recovery_type: Literal[
        "RAVEN_ATTRIBUTED",
        "ORGANIC_CUSTOMER_RETRY",
        "NO_RECOVERY",
        "PRE_EXISTING_RECOVERY",
        "AMBIGUOUS_STATE",
    ] = Field(..., description="Revenue attribution category")
    attribution_confidence: float = Field(..., ge=0.0, le=1.0, description="Attribution confidence score")
    explanation: str = Field(..., description="Human-readable attribution summary")
    verified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Verification timestamp in UTC",
    )
