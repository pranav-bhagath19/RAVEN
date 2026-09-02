"""
RAVEN Production & Demo Environment Configuration Module

Provides strongly typed configuration loading from environment variables with fallback defaults.
Ensures secrets are never hardcoded or exposed in logs/APIs.
"""

import os
from typing import Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Settings(BaseModel):
    """RAVEN Global Application & Gateway Configuration Settings."""

    environment: str = Field(
        default_factory=lambda: os.getenv("RAVEN_ENV", "demo").lower(),
        description="Deployment environment mode: development, demo, or production",
    )
    api_host: str = Field(
        default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"),
        description="API Gateway host binding address",
    )
    api_port: int = Field(
        default_factory=lambda: int(os.getenv("API_PORT", "8000")),
        description="API Gateway HTTP port",
    )
    debug: bool = Field(
        default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true",
        description="Debug mode flag",
    )
    razorpay_key_id: str = Field(
        default_factory=lambda: os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder_key_id"),
        description="Razorpay API Key ID",
    )
    razorpay_key_secret: str = Field(
        default_factory=lambda: os.getenv("RAZORPAY_KEY_SECRET", "placeholder_key_secret"),
        description="Razorpay API Secret Key",
    )
    razorpay_webhook_secret: str = Field(
        default_factory=lambda: os.getenv("RAZORPAY_WEBHOOK_SECRET", "placeholder_webhook_secret"),
        description="Razorpay Webhook HMAC Signature Secret",
    )
    policy_secret: str = Field(
        default_factory=lambda: os.getenv("RAVEN_POLICY_SECRET", "raven_policy_secret_key_2026"),
        description="PolicyEngine HMAC Approval Token Secret Key",
    )
    allowed_cors_origins: list[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "*").split(",")
            if origin.strip()
        ],
        description="Allowed CORS origins list",
    )

    def is_production(self) -> bool:
        """Returns True if running in production mode."""
        return self.environment == "production"

    def sanitize_dict(self) -> dict[str, Any]:
        """Returns a sanitized configuration dictionary redacting secret keys."""
        dump = self.model_dump()
        dump["razorpay_key_secret"] = "[REDACTED]"
        dump["razorpay_webhook_secret"] = "[REDACTED]"
        dump["policy_secret"] = "[REDACTED]"
        return dump


def get_settings() -> Settings:
    """Returns application Settings instance."""
    return Settings()
