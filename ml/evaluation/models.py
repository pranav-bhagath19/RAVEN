"""
RAVEN ML Evaluation Models

Defines strongly typed Pydantic models for evaluation cases, strategy decisions,
evaluation results, benchmark metrics, and benchmark reports.
"""

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from domain.entities.financial_event import FinancialEvent


class EvaluationCase(BaseModel):
    """
    Controlled evaluation case wrapping a synthetic scenario and its ground truth metadata.
    Ground truth fields must NOT be passed to strategies during execution!
    """

    case_id: str = Field(..., description="Unique Evaluation Case ID")
    scenario_id: str = Field(..., description="Scenario identifier (e.g. scenario_1)")
    payment_id: str = Field(..., description="Target Payment ID")
    amount_minor: int = Field(..., ge=0, description="Revenue at risk in minor units")
    currency: str = Field(default="INR", description="Currency ISO 4217 code")
    ground_truth_root_cause: str = Field(..., description="Ground truth root cause classification")
    ground_truth_recoverable: bool = Field(..., description="Ground truth recoverability flag")
    ground_truth_organic_recovery: bool = Field(..., description="Ground truth organic recovery flag")
    ground_truth_optimal_action: str = Field(..., description="Ground truth optimal action type")
    ground_truth_optimal_delay_seconds: int = Field(default=0, ge=0, description="Ground truth optimal delay seconds")
    events: list[FinancialEvent] = Field(default_factory=list, description="Input financial events stream")


class StrategyDecision(BaseModel):
    """
    Decision and execution metadata produced by an evaluation strategy on a case.
    """

    strategy_name: str = Field(..., description="Evaluation strategy identifier")
    action_type: str = Field(..., description="Selected recovery action type")
    action_parameters: dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    decision: str = Field(..., description="Policy or strategy decision: APPROVED, BLOCKED, ESCALATED, NO_ACTION")
    predicted_recovery_probability: float = Field(default=0.0, ge=0.0, le=1.0, description="Estimated recovery probability")
    expected_value_minor: int = Field(default=0, description="Calculated Expected Value in minor units")
    execution_attempted: bool = Field(default=False, description="Whether side-effect execution was attempted")
    execution_success: bool = Field(default=False, description="Whether side-effect tool execution succeeded")
    execution_cost_minor: int = Field(default=0, ge=0, description="Cost of side-effect execution in minor units")
    recovery_attributed: bool = Field(default=False, description="Whether revenue recovery was attributed")
    attribution_type: str = Field(default="NONE", description="Attribution category tag")
    latency_ms: float = Field(default=0.0, ge=0.0, description="Decision latency in milliseconds")
    root_cause_prediction: str | None = Field(default=None, description="Predicted root cause if available")
    policy_violation: bool = Field(default=False, description="Whether a policy violation occurred")


class EvaluationResult(BaseModel):
    """
    Comparison result matching strategy decision against case ground truth.
    """

    case_id: str = Field(..., description="Evaluation Case ID")
    scenario_id: str = Field(..., description="Scenario ID")
    strategy_name: str = Field(..., description="Strategy Name")
    decision: str = Field(..., description="Strategy decision tag")
    root_cause_prediction: str | None = Field(default=None, description="Predicted root cause category")
    root_cause_correct: bool | None = Field(default=None, description="Whether root cause prediction matched ground truth")
    selected_action: str = Field(..., description="Selected action type")
    optimal_action: str = Field(..., description="Ground truth optimal action type")
    action_correct: bool = Field(..., description="Whether selected action matched optimal action")
    recovered: bool = Field(..., description="Whether revenue was recovered")
    recovery_attributed: bool = Field(..., description="Whether recovery was attributed to strategy")
    recovered_amount_minor: int = Field(default=0, ge=0, description="Gross recovered amount in minor units")
    action_cost_minor: int = Field(default=0, ge=0, description="Execution cost in minor units")
    net_recovered_minor: int = Field(default=0, description="Net recovered amount (gross - cost) in minor units")
    policy_violation: bool = Field(default=False, description="Whether a policy violation occurred")
    decision_latency_ms: float = Field(default=0.0, ge=0.0, description="Decision latency in milliseconds")


class BenchmarkMetrics(BaseModel):
    """
    Aggregated benchmark performance metrics for a strategy across cases.
    """

    total_cases: int = Field(default=0, ge=0, description="Total evaluation cases processed")
    state_reconstruction_accuracy: float = Field(default=0.0, ge=0.0, le=1.0, description="State reconstruction accuracy (0.0 - 1.0)")
    root_cause_accuracy: float = Field(default=0.0, ge=0.0, le=1.0, description="Root cause accuracy (0.0 - 1.0)")
    action_selection_accuracy: float = Field(default=0.0, ge=0.0, le=1.0, description="Action selection accuracy (0.0 - 1.0)")
    recovery_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Gross recovery rate (0.0 - 1.0)")
    recovery_net_rate: float = Field(default=0.0, description="Net recovery rate percentage relative to risk")
    total_revenue_at_risk_minor: int = Field(default=0, ge=0, description="Total revenue at risk in minor units")
    total_revenue_recovered_minor: int = Field(default=0, ge=0, description="Total gross revenue recovered in minor units")
    total_action_cost_minor: int = Field(default=0, ge=0, description="Total execution costs in minor units")
    policy_violation_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Policy violation rate (0.0 - 1.0)")
    attribution_precision: float = Field(default=0.0, ge=0.0, le=1.0, description="Attribution precision (0.0 - 1.0)")
    attribution_recall: float = Field(default=0.0, ge=0.0, le=1.0, description="Attribution recall (0.0 - 1.0)")
    average_decision_latency_ms: float = Field(default=0.0, ge=0.0, description="Average decision latency in milliseconds")
    p95_decision_latency_ms: float = Field(default=0.0, ge=0.0, description="95th percentile decision latency in milliseconds")
    organic_recovery_misattribution_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Organic misattribution rate (0.0 - 1.0)")


class BenchmarkReport(BaseModel):
    """
    Complete benchmark report containing metadata, metrics, per-scenario metrics, and raw results.
    """

    benchmark_version: str = Field(default="v1.0", description="Benchmark engine version")
    dataset_version: str = Field(default="v1.0", description="Simulated dataset version")
    seed: int = Field(default=42, description="Random seed used for generation")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Report generation timestamp in UTC ISO 8601",
    )
    benchmark_hash: str = Field(default="", description="SHA256 digest over canonical report payload for reproducibility")
    strategies: list[str] = Field(default_factory=list, description="Evaluated strategy names")
    metrics: dict[str, BenchmarkMetrics] = Field(default_factory=dict, description="Metrics per strategy")
    per_scenario_metrics: dict[str, dict[str, BenchmarkMetrics]] = Field(
        default_factory=dict, description="Per-scenario metrics mapping (scenario_id -> strategy_name -> metrics)"
    )
    raw_results: list[EvaluationResult] = Field(default_factory=list, description="Raw evaluation results per case")
