"""
RAVEN Customer Domain Entity

Represents a merchant's end customer purchasing goods/services.
Includes PII sanitization helpers for compliance logging.
"""

from datetime import datetime, timezone
import re
from pydantic import BaseModel, Field, field_validator


class CustomerCommunicationPreferences(BaseModel):
    opt_out: bool = Field(False, description="Whether customer opted out of recovery messages")
    preferred_channel: str = Field("WHATSAPP", description="Preferred contact channel")
    daily_message_limit: int = Field(2, ge=0, description="Max recovery messages allowed per day")


class Customer(BaseModel):
    """
    Customer entity representing paying end-users.
    """

    id: str = Field(..., description="Unique customer ID, e.g. cust_01H...")
    merchant_id: str = Field(..., description="Associated Merchant ID")
    email: str = Field(..., description="Customer email address")
    phone: str = Field(..., description="Customer phone number (E.164 normalized)")
    name: str = Field(..., min_length=1, description="Customer name")
    communication_preferences: CustomerCommunicationPreferences = Field(
        default_factory=lambda: CustomerCommunicationPreferences(
            opt_out=False, preferred_channel="WHATSAPP", daily_message_limit=2
        ),
        description="Communication consent and preference settings",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp in UTC",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        clean = v.strip().lower()
        if "@" not in clean or "." not in clean.split("@")[-1]:
            raise ValueError(f"Invalid email address format: {v}")
        return clean

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits_only = re.sub(r"\D", "", v)
        if len(digits_only) < 7 or len(digits_only) > 15:
            raise ValueError(f"Invalid phone number format: {v}")
        return f"+{digits_only}" if not v.startswith("+") else v

    def masked_email(self) -> str:
        """Returns PII-redacted email for logging (e.g. j***e@domain.com)."""
        if "@" not in self.email:
            return "***"
        local, domain = self.email.split("@", 1)
        if len(local) <= 2:
            masked_local = local[0] + "*"
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"

    def masked_phone(self) -> str:
        """Returns PII-redacted phone number for logging (e.g. +91******1234)."""
        if len(self.phone) < 6:
            return "***"
        return self.phone[:3] + "*" * (len(self.phone) - 7) + self.phone[-4:]
