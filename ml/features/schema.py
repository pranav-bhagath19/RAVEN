"""
RAVEN ML Feature Schema Module

Defines FeatureSchemaV1 with strict versioning, feature ordering,
input validation, missing value handling, and target leakage prevention.
"""

from typing import Any, ClassVar
from pydantic import BaseModel, Field


class FeatureSchemaV1(BaseModel):
    """
    Version 1 Feature Schema for RAVEN Propensity Scoring.
    Defines explicit numerical and categorical inputs available BEFORE action execution.
    Target outcome and verification variables are strictly forbidden to prevent leakage.
    """

    schema_version: str = Field("v1.0", description="Feature schema version identifier")

    # Numerical Features
    amount_minor: int = Field(..., ge=0, description="Transaction amount in minor units (paise)")
    attempts_count: int = Field(0, ge=0, description="Previous failure retry attempts count")

    # Categorical Features
    currency: str = Field("INR", description="Transaction currency ISO code")
    error_code: str = Field("UNKNOWN", description="Payment failure error code")
    root_cause: str = Field("UNKNOWN", description="Diagnosed root cause category")
    action_type: str = Field("UNKNOWN", description="Candidate action type being evaluated")
    merchant_status: str = Field("active", description="Merchant account status")
    customer_opt_out: bool = Field(False, description="Customer communication opt-out flag")
    is_systemic_downtime: bool = Field(False, description="Bank/gateway downtime flag")

    # Strict Feature Ordering for Deterministic Model Matrix Construction
    FEATURE_NAMES: ClassVar[list[str]] = [
        "amount_scaled",
        "attempts_count",
        "currency_code",
        "error_code_encoded",
        "root_cause_encoded",
        "action_type_encoded",
        "merchant_status_encoded",
        "customer_opt_out_flag",
        "is_systemic_downtime_flag",
    ]

    # Target & Ground-Truth Leakage Check List
    FORBIDDEN_LEAKAGE_FIELDS: ClassVar[set[str]] = {
        "is_recovered",
        "recovered_amount",
        "recovered_amount_minor",
        "recovered",
        "recovery_attributed",
        "is_organic",
        "verification_status",
        "verified_at",
        "execution_status",
        "executed_at",
    }

    @classmethod
    def validate_raw_input(cls, input_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Validates raw input dictionary against target leakage rules and schema requirements.
        Raises ValueError if any forbidden leakage field is present in input.
        """
        leakage_detected = cls.FORBIDDEN_LEAKAGE_FIELDS.intersection(input_dict.keys())
        if leakage_detected:
            raise ValueError(f"Target leakage detected! Input contains forbidden post-action fields: {sorted(leakage_detected)}")

        return {
            "amount_minor": int(input_dict.get("amount_minor", 0)),
            "attempts_count": int(input_dict.get("attempts_count", 0)),
            "currency": str(input_dict.get("currency", "INR")),
            "error_code": str(input_dict.get("error_code", "UNKNOWN")),
            "root_cause": str(input_dict.get("root_cause", "UNKNOWN")),
            "action_type": str(input_dict.get("action_type", "UNKNOWN")),
            "merchant_status": str(input_dict.get("merchant_status", "active")),
            "customer_opt_out": bool(input_dict.get("customer_opt_out", False)),
            "is_systemic_downtime": bool(input_dict.get("is_systemic_downtime", False)),
        }
