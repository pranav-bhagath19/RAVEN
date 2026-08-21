"""
RAVEN Merchant Domain Entity

Represents a merchant business using RAVEN for automated revenue recovery.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator


class MerchantStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ONBOARDING = "ONBOARDING"


class Merchant(BaseModel):
    """
    Merchant entity defining policy configuration and merchant-specific bounds.
    """

    id: str = Field(..., description="Unique merchant identifier, e.g. mer_01H...")
    name: str = Field(..., min_length=1, description="Business name")
    currency: str = Field("INR", description="ISO 4217 currency code")
    status: MerchantStatus = Field(MerchantStatus.ACTIVE, description="Merchant account status")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC",
    )
    policy_config: dict[str, Any] = Field(
        default_factory=lambda: {
            "max_recovery_attempts": 3,
            "high_value_threshold_paise": 1000000,  # ₹10,000 in minor units
            "min_confidence_threshold": 0.75,
            "allowed_channels": ["WHATSAPP", "EMAIL", "SMS"],
        },
        description="Merchant-specific policy rules and caps",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v_upper = v.upper()
        if len(v_upper) != 3 or not v_upper.isalpha():
            raise ValueError("Currency must be a valid 3-letter ISO 4217 code (e.g. INR, USD)")
        return v_upper
