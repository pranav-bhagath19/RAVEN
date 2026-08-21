"""
RAVEN Operations Dashboard API Response Schemas

Defines strongly typed Pydantic models for control plane overview, payment inspection,
decision trace lineage, policy audit, telemetry, benchmark, and ML operational endpoints.
"""

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated list response container."""

    items: list[T] = Field(default_factory=list, description="List of items for current page")
    page: int = Field(1, ge=1, description="1-indexed current page number")
    page_size: int = Field(50, ge=1, le=100, description="Items per page (max 100)")
    total: int = Field(0, ge=0, description="Total matching items count")


class OverviewResponse(BaseModel):
    """Operational dashboard aggregate summary metrics."""

    total_payments: int = Field(0, ge=0, description="Total payments observed")
    failed_payments: int = Field(0, ge=0, description="Total failed payments")
    recovered_payments: int = Field(0, ge=0, description="Total successfully recovered payments")
    recovery_rate: float = Field(0.0, ge=0.0, le=1.0, description="Gross recovery rate (0.0 - 1.0)")
    total_revenue_at_risk_minor: int = Field(0, ge=0, description="Total revenue at risk in minor units")
    total_revenue_recovered_minor: int = Field(0, ge=0, description="Total gross recovered revenue in minor units")
    total_action_cost_minor: int = Field(0, ge=0, description="Total execution cost in minor units")
    net_revenue_recovered_minor: int = Field(0, description="Net recovered revenue in minor units")
    blocked_actions: int = Field(0, ge=0, description="Total actions blocked by PolicyEngine")
    escalations: int = Field(0, ge=0, description="Total actions escalated to human operations")
    approved_actions: int = Field(0, ge=0, description="Total actions approved by PolicyEngine")
    tool_executions: int = Field(0, ge=0, description="Total side-effect tool executions")
    duplicate_executions_prevented: int = Field(0, ge=0, description="Duplicate side effects prevented by idempotency engine")
    policy_violations: int = Field(0, ge=0, description="Total policy violations (Target: 0)")
    active_opportunities: int = Field(0, ge=0, description="Open recovery opportunities count")
    agent_fallback_count: int = Field(0, ge=0, description="Total deterministic agent fallbacks triggered")
    llm_invocation_count: int = Field(0, ge=0, description="Total LLM provider invocations")
    average_agent_latency_ms: float = Field(0.0, ge=0.0, description="Average agent latency in milliseconds")
    webhook_count: int = Field(0, ge=0, description="Total webhooks ingested")
    duplicate_webhook_count: int = Field(0, ge=0, description="Duplicate webhooks detected")


class PaymentSummary(BaseModel):
    """Payment summary for list views."""

    payment_id: str = Field(..., description="Payment ID")
    order_id: str | None = Field(default=None, description="Order ID")
    merchant_id: str = Field(..., description="Merchant ID")
    customer_id: str = Field(..., description="Customer ID")
    amount_minor: int = Field(..., ge=0, description="Amount in minor units")
    currency: str = Field("INR", description="Currency ISO code")
    status: str = Field(..., description="Payment status")
    created_at: datetime = Field(..., description="Creation timestamp in UTC")
    last_event_type: str | None = Field(default=None, description="Most recent event type")
    recovery_status: str = Field("OPEN", description="Recovery opportunity status")


class PaymentDetailResponse(BaseModel):
    """Detailed payment view including reconstructed state and trace reference."""

    payment_id: str = Field(..., description="Payment ID")
    order_id: str | None = Field(default=None, description="Order ID")
    merchant_id: str = Field(..., description="Merchant ID")
    customer_id: str = Field(..., description="Customer ID")
    amount_minor: int = Field(..., ge=0, description="Amount in minor units")
    currency: str = Field("INR", description="Currency ISO code")
    status: str = Field(..., description="Current payment status")
    attempts_count: int = Field(0, ge=0, description="Payment attempts count")
    error_code: str | None = Field(default=None, description="Primary failure error code if failed")
    error_description: str | None = Field(default=None, description="Failure description")
    events: list[dict[str, Any]] = Field(default_factory=list, description="Ingested financial events timeline")
    candidate_actions: list[dict[str, Any]] = Field(default_factory=list, description="Candidate action proposals")
    policy_decision: dict[str, Any] | None = Field(default=None, description="PolicyEngine decision summary")
    execution_result: dict[str, Any] | None = Field(default=None, description="Tool execution outcome")
    verification_result: dict[str, Any] | None = Field(default=None, description="Verification outcome")
    latest_trace_id: str | None = Field(default=None, description="Latest DecisionTrace ID reference")


class EventSummary(BaseModel):
    """Financial event item representation."""

    id: str = Field(..., description="Event ID")
    event_hash: str = Field(..., description="SHA256 canonical event hash")
    event_type: str = Field(..., description="Event type string")
    entity_id: str = Field(..., description="Primary entity ID (payment_id)")
    merchant_id: str = Field(..., description="Merchant ID")
    amount_minor: int | None = Field(default=None, description="Amount in minor units")
    currency: str = Field("INR", description="Currency ISO code")
    occurred_at: datetime = Field(..., description="Occurrence timestamp in UTC")
    received_at: datetime = Field(..., description="Ingestion timestamp in UTC")
    payload: dict[str, Any] = Field(default_factory=dict, description="Sanitized payload snapshot")


class DecisionSummary(BaseModel):
    """Decision summary item."""

    decision_id: str = Field(..., description="Decision Trace ID")
    payment_id: str = Field(..., description="Payment ID")
    merchant_id: str = Field(..., description="Merchant ID")
    status: str = Field(..., description="Decision Trace Status")
    root_cause: str | None = Field(default=None, description="Identified root cause")
    selected_action: str | None = Field(default=None, description="Selected action type")
    policy_decision: str = Field("INITIATED", description="Policy outcome")
    policy_token_id: str | None = Field(default=None, description="Issued PolicyApprovalToken ID")
    created_at: str = Field(..., description="Creation timestamp ISO 8601")


class TraceMilestone(BaseModel):
    """Chronological milestone entry in a DecisionTrace timeline."""

    milestone_name: str = Field(..., description="Milestone identifier tag")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    status: str = Field(..., description="Status string at milestone")
    details: dict[str, Any] = Field(default_factory=dict, description="Milestone metadata details")


class TraceDetailResponse(BaseModel):
    """Complete DecisionTrace operational lineage response."""

    decision_id: str = Field(..., description="Unique DecisionTrace ID")
    recovery_opportunity_id: str = Field(..., description="Recovery Opportunity ID")
    merchant_id: str = Field(..., description="Merchant ID")
    customer_id: str = Field(..., description="Customer ID")
    payment_id: str = Field(..., description="Payment ID")
    status: str = Field(..., description="Lifecycle trace status")
    input_state_snapshot: dict[str, Any] = Field(default_factory=dict, description="Reconstructed state snapshot")
    evidence_references: list[str] = Field(default_factory=list, description="Evidence event IDs")
    root_cause_result: dict[str, Any] | None = Field(default=None, description="Root Cause Analyst output")
    candidate_actions: list[dict[str, Any]] = Field(default_factory=list, description="Candidate action proposals")
    value_estimates: list[dict[str, Any]] = Field(default_factory=list, description="Expected Value calculations")
    policy_evaluations: list[dict[str, Any]] = Field(default_factory=list, description="PolicyEngine rule evaluations")
    selected_action: dict[str, Any] | None = Field(default=None, description="Selected candidate action")
    policy_token_id: str | None = Field(default=None, description="Issued PolicyApprovalToken ID")
    execution_result: dict[str, Any] | None = Field(default=None, description="ToolExecutor result payload")
    verification_result: dict[str, Any] | None = Field(default=None, description="Verification Agent outcome")
    chronological_timeline: list[TraceMilestone] = Field(default_factory=list, description="Ordered trace milestones")


class PolicyRuleSummary(BaseModel):
    """PolicyEngine rule documentation and statistics item."""

    policy_id: str = Field(..., description="Policy Rule ID (e.g. POL_001)")
    name: str = Field(..., description="Human-readable policy rule name")
    description: str = Field(..., description="Detailed rule description")
    decision_type: str = Field(..., description="Decision outcome if rule triggers: BLOCKED or ESCALATE_TO_HUMAN")
    version: str = Field("v1.0", description="Policy rule version")
    evaluations_count: int = Field(0, ge=0, description="Total evaluations performed")
    triggers_count: int = Field(0, ge=0, description="Total times rule was triggered")


class ToolExecutionSummary(BaseModel):
    """ToolExecutor audit log item."""

    execution_id: str = Field(..., description="Execution ID")
    tool_name: str = Field(..., description="Executed tool name")
    action_id: str = Field(..., description="Action ID")
    payment_id: str = Field(..., description="Payment ID")
    status: str = Field(..., description="Status: SIMULATED_SUCCESS, SUCCESS, FAILED")
    executed_at: datetime = Field(..., description="Execution timestamp in UTC")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Sanitized parameters payload")
    policy_token_id: str | None = Field(default=None, description="Associated PolicyApprovalToken ID")


class VerificationSummary(BaseModel):
    """Verification Agent outcome log item."""

    payment_id: str = Field(..., description="Payment ID")
    action_id: str = Field(..., description="Action ID")
    recovery_type: str = Field(..., description="Attribution category tag")
    is_recovered: bool = Field(..., description="Whether revenue was recovered")
    recovered_amount_minor: int = Field(0, ge=0, description="Recovered amount in minor units")
    verified_at: datetime = Field(..., description="Verification timestamp in UTC")
    trace_id: str | None = Field(default=None, description="Associated trace ID")


class TelemetrySummary(BaseModel):
    """Sanitized LLM Observability Telemetry item."""

    trace_id: str = Field(..., description="Trace ID")
    agent_name: str = Field(..., description="Agent name")
    provider: str = Field(..., description="LLM provider name")
    model: str = Field(..., description="Model name")
    prompt_version: str = Field(..., description="Prompt version tag")
    started_at: datetime = Field(..., description="Start timestamp UTC")
    completed_at: datetime = Field(..., description="Completion timestamp UTC")
    latency_ms: float = Field(..., ge=0.0, description="Latency in milliseconds")
    success: bool = Field(..., description="Whether invocation succeeded")
    failure_reason: str | None = Field(default=None, description="Sanitized failure reason")
    reasoning_mode: str = Field(..., description="'LLM' or 'DETERMINISTIC_FALLBACK'")
    input_summary: str = Field(..., description="Sanitized input summary")
    output_summary: str = Field(..., description="Sanitized output summary")


class BenchmarkSummary(BaseModel):
    """Comparative evaluation benchmark metrics summary."""

    benchmark_version: str = Field(..., description="Benchmark version string")
    seed: int = Field(42, description="Random seed")
    benchmark_hash: str = Field(..., description="Canonical SHA256 report hash")
    generated_at: str = Field(..., description="ISO timestamp")
    total_cases: int = Field(..., ge=0, description="Total synthetic cases evaluated")
    strategies: list[dict[str, Any]] = Field(default_factory=list, description="Per-strategy benchmark metrics")


class MLModelSummary(BaseModel):
    """Read-only operational summary item for ML models."""

    model_version: str = Field(..., description="Model version tag")
    model_type: str = Field(..., description="Model algorithm type")
    feature_schema_version: str = Field("v1.0", description="Feature schema version")
    dataset_version: str = Field("v1.0", description="Dataset version")
    artifact_hash: str = Field(..., description="SHA-256 artifact hash")
    is_fitted: bool = Field(True, description="Whether model is trained")
    status: str = Field("ACTIVE", description="Model status")


class MLModelDetailResponse(BaseModel):
    """Read-only operational detail for a specific ML model version."""

    model_version: str = Field(..., description="Model version tag")
    model_type: str = Field(..., description="Model algorithm type")
    feature_schema_version: str = Field("v1.0", description="Feature schema version")
    dataset_version: str = Field("v1.0", description="Dataset version")
    artifact_hash: str = Field(..., description="SHA-256 artifact hash")
    hyperparameters: dict[str, Any] = Field(default_factory=dict, description="Model hyperparameters")
    status: str = Field("ACTIVE", description="Model status")


class MLMetricsResponse(BaseModel):
    """Read-only operational propensity classification metrics response."""

    model_version: str = Field("v1.0", description="Model version tag")
    roc_auc: float = Field(..., ge=0.0, le=1.0, description="ROC-AUC score")
    pr_auc: float = Field(..., ge=0.0, le=1.0, description="PR-AUC score")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="Classification accuracy")
    precision: float = Field(..., ge=0.0, le=1.0, description="Precision")
    recall: float = Field(..., ge=0.0, le=1.0, description="Recall")
    f1: float = Field(..., ge=0.0, le=1.0, description="F1 Score")
    brier_score: float = Field(..., ge=0.0, le=1.0, description="Brier Score")
    calibration_error: float = Field(..., ge=0.0, le=1.0, description="Expected Calibration Error")
    confusion_matrix: list[list[int]] = Field(..., description="Confusion matrix [[TN, FP], [FN, TP]]")
    benchmark_hash: str = Field(..., description="Associated canonical benchmark hash")


class OperationsHealthResponse(BaseModel):
    """Subsystem status health and readiness payload."""

    status: str = Field("ok", description="Overall health status: ok or degraded")
    api_status: str = Field("healthy", description="FastAPI gateway status")
    domain_status: str = Field("healthy", description="Domain kernel status")
    event_ingestion_status: str = Field("healthy", description="Event ingestion status")
    policy_engine_status: str = Field("healthy", description="PolicyEngine status")
    tool_executor_status: str = Field("healthy", description="ToolExecutor status")
    agent_subsystem_status: str = Field("healthy", description="Autonomous agent trio status")
    razorpay_integration_status: str = Field("healthy", description="Razorpay adapter status")
    telemetry_status: str = Field("healthy", description="Observability telemetry status")
    checked_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Check timestamp in UTC",
    )


class ReprocessRequest(BaseModel):
    """Request payload for controlled management reprocess command."""

    reason: str = Field(default="Manual operator reprocess", description="Reason for triggering reprocess")


class ReprocessResponse(BaseModel):
    """Response returned upon controlled management reprocess execution."""

    payment_id: str = Field(..., description="Target Payment ID")
    status: str = Field(..., description="Reprocess decision status")
    trace_id: str = Field(..., description="Generated DecisionTrace ID")
    policy_decision: str = Field(..., description="PolicyEngine decision tag: APPROVED, BLOCKED, ESCALATE_TO_HUMAN")
    execution_result: dict[str, Any] | None = Field(default=None, description="Tool execution result if approved")
