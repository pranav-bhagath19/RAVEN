"""
RAVEN Policy Engine Models

Defines CandidateAction, PolicyResult, PolicyDecision, PolicyContext,
and PolicyVersion domain models for deterministic governance.
"""

from datetime import datetime, timezone
import uuid
from typing import Any
from pydantic import BaseModel, Field, field_validator
from domain.entities.customer import Customer
from domain.entities.merchant import Merchant
from domain.entities.payment import Payment
from domain.enums import RecoveryActionType
from domain.values.money import Money


POLICY_VERSION = "v1.0"


class CandidateAction(BaseModel):
    """
    CandidateAction proposed by an AI agent or analytical pipeline.
    Strictly action representation ONLY until verified and approved by PolicyEngine.
    """

    id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:12]}", description="Unique Action ID")
    opportunity_id: str = Field(..., description="Associated Recovery Opportunity ID")
    payment_id: str = Field(..., description="Associated Payment ID")
    merchant_id: str = Field(..., description="Associated Merchant ID")
    customer_id: str | None = Field(default=None, description="Associated Customer ID")
    action_type: RecoveryActionType = Field(..., description="Requested recovery intervention category")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters dictionary")
    expected_recovery_value: Money = Field(..., description="Expected Recovery Value Money object")
    agent_confidence: float = Field(..., ge=0.0, le=1.0, description="Agent confidence score (0.0 to 1.0)")
    idempotency_key: str = Field(..., description="Unique client-supplied idempotency key")
    requested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Candidate action creation timestamp in UTC",
    )

    @field_validator("parameters")
    @classmethod
    def validate_action_parameters(cls, v: dict[str, Any], info: Any) -> dict[str, Any]:
        """Validates parameter requirements per action type."""
        action_type = info.data.get("action_type")
        if action_type == RecoveryActionType.SMART_RETRY:
            if "delay_seconds" not in v:
                v["delay_seconds"] = 900
        elif action_type == RecoveryActionType.PAYMENT_LINK_DISPATCH:
            if "channel" not in v:
                v["channel"] = "WHATSAPP"
        elif action_type == RecoveryActionType.FALLBACK_CHANNEL_NOTIFY:
            if "channel" not in v:
                v["channel"] = "SMS"
        elif action_type == RecoveryActionType.ESCALATE_TO_HUMAN:
            if "reason" not in v:
                v["reason"] = "Policy escalation"
        return v


class PolicyResult(BaseModel):
    """
    Result of an individual policy rule evaluation.
    """

    policy_id: str = Field(..., description="Policy rule ID (e.g. POL_001)")
    policy_version: str = Field(default=POLICY_VERSION, description="Policy version string")
    passed: bool = Field(..., description="Whether candidate action satisfied rule")
    decision: str = Field(..., description="Outcome tag: APPROVED, BLOCKED, or ESCALATE_TO_HUMAN")
    reason: str = Field(..., description="Deterministic explanation of evaluation result")


class PolicyContext(BaseModel):
    """
    Context snapshot provided to PolicyEngine for evaluating a candidate action.
    """

    payment: Payment | None = Field(default=None, description="Reconstructed Payment domain entity")
    customer: Customer | None = Field(default=None, description="Customer entity with preferences")
    merchant: Merchant | None = Field(default=None, description="Merchant entity")
    attempts_count: int = Field(default=0, ge=0, description="Number of recovery/payment attempts initiated")
    bank_downtime_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Issuer bank downtime failure rate (0.0 to 1.0)")
    daily_messages_sent: int = Field(default=0, ge=0, description="Count of messages sent to customer today")
    high_value_threshold_minor: int = Field(default=1000000, ge=0, description="High-value threshold in minor units (default: ₹10,000.00)")
    max_recovery_attempts: int = Field(default=3, ge=1, description="Max allowed recovery attempts per payment (default: 3)")
    min_confidence_threshold: float = Field(default=0.75, ge=0.0, le=1.0, description="Minimum agent confidence score required")


class PolicyDecision(BaseModel):
    """
    Final decision rendered by Deterministic PolicyEngine.
    """

    decision_id: str = Field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:12]}", description="Unique Decision ID")
    action_id: str = Field(..., description="Candidate Action ID")
    opportunity_id: str = Field(..., description="Associated Opportunity ID")
    payment_id: str = Field(..., description="Associated Payment ID")
    decision: str = Field(..., description="Final decision: APPROVED, BLOCKED, or ESCALATE_TO_HUMAN")
    policy_version: str = Field(default=POLICY_VERSION, description="Authoritative policy version")
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Policy evaluation timestamp in UTC",
    )
    policy_evaluations: list[PolicyResult] = Field(default_factory=list, description="Individual rule evaluation results")
    blocked_by_policy_id: str | None = Field(default=None, description="ID of policy rule that blocked or escalated action")
    reason: str = Field(..., description="Human-readable decision summary")
    approval_token: Any | None = Field(default=None, description="PolicyApprovalToken if APPROVED, else None")
