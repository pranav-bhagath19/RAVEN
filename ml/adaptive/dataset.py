"""
RAVEN Adaptive Outcome Dataset Builder Module

Builds training and evaluation datasets from historical recovery outcomes.
Enforces strict target leakage prevention by rejecting post-action execution, verification,
or financial recovery fields.
"""

from typing import Any
from pydantic import BaseModel, Field

FORBIDDEN_LEAKAGE_FIELDS: set[str] = {
    "recovered_amount_minor",
    "recovered_amount",
    "is_recovered",
    "verification_status",
    "verified_at",
    "execution_status",
    "executed_at",
    "tool_result",
    "future_event_id",
    "post_action_status",
}


class AdaptiveOutcomeRecord(BaseModel):
    """Single historical outcome training record."""

    tenant_id: str
    payment_id: str
    decision_id: str
    action_type: str
    amount_minor: int = Field(..., ge=0)
    currency: str = "INR"
    attempts_count: int = Field(..., ge=0)
    error_code: str
    root_cause: str
    merchant_status: str = "ACTIVE"
    customer_opt_out_flag: bool = False
    systemic_downtime_flag: bool = False
    propensity_score: float = Field(..., ge=0.0, le=1.0)
    policy_version: int = Field(..., ge=1)
    timestamp: str
    outcome: int = Field(..., ge=0, le=1, description="0 = unsuccessful, 1 = successful")


class AdaptiveOutcomeDatasetBuilder:
    """
    Builds and validates historical recovery outcome datasets.
    """

    def validate_raw_record(self, record: dict[str, Any]) -> None:
        """Checks raw dictionary for forbidden target leakage fields."""
        leaked_keys = set(record.keys()).intersection(FORBIDDEN_LEAKAGE_FIELDS)
        if leaked_keys:
            raise ValueError(f"Target leakage violation: record contains post-action fields {leaked_keys}")

    def build_dataset(self, raw_records: list[dict[str, Any]]) -> list[AdaptiveOutcomeRecord]:
        """Validates and converts raw records into typed AdaptiveOutcomeRecord instances."""
        records: list[AdaptiveOutcomeRecord] = []
        for r in raw_records:
            self.validate_raw_record(r)
            records.append(AdaptiveOutcomeRecord(**r))
        return records
