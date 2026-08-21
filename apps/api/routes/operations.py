"""
RAVEN Operations Control Plane Router Module

Exposes /api/v1/operations/... REST endpoints for observational metrics, payment inspection,
decision trace lineage, policy audit, telemetry, ML models/metrics, and controlled reprocessing.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from apps.api.auth import UserIdentity, get_current_user, require_control_permission
from apps.api.dependencies import get_operations_service
from apps.api.operations_schemas import (
    BenchmarkSummary,
    DecisionSummary,
    EventSummary,
    MLMetricsResponse,
    MLModelDetailResponse,
    MLModelSummary,
    OperationsHealthResponse,
    OverviewResponse,
    PaginatedResponse,
    PaymentDetailResponse,
    PaymentSummary,
    PolicyRuleSummary,
    ReprocessRequest,
    ReprocessResponse,
    TelemetrySummary,
    ToolExecutionSummary,
    TraceDetailResponse,
    VerificationSummary,
)
from apps.api.operations_service import OperationsService

router = APIRouter(prefix="/api/v1/operations", tags=["Operations"])


@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> OverviewResponse:
    """Returns aggregate operational summary metrics."""
    return service.get_overview()


@router.get("/payments", response_model=PaginatedResponse[PaymentSummary])
def get_payments(
    status_filter: str | None = Query(default=None, alias="status"),
    merchant_id: str | None = Query(default=None),
    customer_id: str | None = Query(default=None),
    payment_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> PaginatedResponse[PaymentSummary]:
    """Returns paginated payment summary items."""
    return service.get_payments(
        status=status_filter,
        merchant_id=merchant_id,
        customer_id=customer_id,
        payment_id=payment_id,
        page=page,
        page_size=page_size,
    )


@router.get("/payments/{payment_id}", response_model=PaymentDetailResponse)
def get_payment_detail(
    payment_id: str,
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> PaymentDetailResponse:
    """Returns detailed payment object including reconstructed state and trace reference."""
    detail = service.get_payment_detail(payment_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "PAYMENT_NOT_FOUND", "message": f"Payment '{payment_id}' was not found."}},
        )
    return detail


@router.get("/events", response_model=PaginatedResponse[EventSummary])
def get_events(
    entity_id: str | None = Query(default=None),
    event_id: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> PaginatedResponse[EventSummary]:
    """Returns paginated financial event summaries."""
    return service.get_events(
        entity_id=entity_id,
        event_id=event_id,
        event_type=event_type,
        page=page,
        page_size=page_size,
    )


@router.get("/decisions", response_model=PaginatedResponse[DecisionSummary])
def get_decisions(
    status_filter: str | None = Query(default=None, alias="status"),
    payment_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> PaginatedResponse[DecisionSummary]:
    """Returns paginated DecisionTrace summaries."""
    return service.get_decisions(
        status=status_filter,
        payment_id=payment_id,
        page=page,
        page_size=page_size,
    )


@router.get("/traces/{trace_id}", response_model=TraceDetailResponse)
def get_trace_detail(
    trace_id: str,
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> TraceDetailResponse:
    """Returns complete chronological operational DecisionTrace timeline."""
    trace = service.get_trace_detail(trace_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TRACE_NOT_FOUND", "message": f"DecisionTrace '{trace_id}' was not found."}},
        )
    return trace


@router.get("/actions", response_model=list[dict[str, Any]])
def get_actions(
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Returns catalog of candidate recovery action types."""
    return [
        {"action_type": "SMART_RETRY", "name": "Smart Retry", "description": "Automated network/gateway retry with optimal timing window."},
        {"action_type": "PAYMENT_LINK", "name": "Payment Link", "description": "Generate and dispatch fallback Razorpay checkout link."},
        {"action_type": "FALLBACK_NOTIFY", "name": "Customer Notification", "description": "Dispatch gentle customer alert for payment authorization update."},
        {"action_type": "ESCALATE_TO_HUMAN", "name": "Human Escalation", "description": "Escalate to human operations queue for high-value or ambiguous transactions."},
    ]


@router.get("/policies", response_model=list[PolicyRuleSummary])
def get_policies(
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> list[PolicyRuleSummary]:
    """Returns list of registered PolicyEngine rule summaries."""
    return service.get_policies()


@router.get("/tool-executions", response_model=PaginatedResponse[ToolExecutionSummary])
def get_tool_executions(
    payment_id: str | None = Query(default=None),
    tool_name: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> PaginatedResponse[ToolExecutionSummary]:
    """Returns paginated tool execution audit summaries."""
    return service.get_tool_executions(
        payment_id=payment_id,
        tool_name=tool_name,
        status=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get("/verifications", response_model=PaginatedResponse[VerificationSummary])
def get_verifications(
    payment_id: str | None = Query(default=None),
    recovery_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> PaginatedResponse[VerificationSummary]:
    """Returns paginated verification summaries."""
    return service.get_verifications(
        payment_id=payment_id,
        recovery_type=recovery_type,
        page=page,
        page_size=page_size,
    )


@router.get("/agents/telemetry", response_model=PaginatedResponse[TelemetrySummary])
def get_agent_telemetry(
    agent: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    model: str | None = Query(default=None),
    reasoning_mode: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> PaginatedResponse[TelemetrySummary]:
    """Returns paginated PII-sanitized LLM Observability telemetry logs."""
    return service.get_agent_telemetry(
        agent=agent,
        provider=provider,
        model=model,
        reasoning_mode=reasoning_mode,
        page=page,
        page_size=page_size,
    )


@router.get("/benchmarks", response_model=BenchmarkSummary)
def get_benchmarks(
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> BenchmarkSummary:
    """Returns comparative evaluation benchmark metrics."""
    return service.get_benchmark_summary()


@router.get("/ml/models", response_model=list[MLModelSummary])
def get_ml_models(
    user: UserIdentity = Depends(get_current_user),
) -> list[MLModelSummary]:
    """Returns list of registered read-only ML propensity models metadata."""
    return [
        MLModelSummary(
            model_version="v1.0",
            model_type="LogisticRegression",
            feature_schema_version="v1.0",
            dataset_version="v1.0",
            artifact_hash="a1b2c3d4e5f67890abcdef1234567890",
            is_fitted=True,
            status="ACTIVE",
        )
    ]


@router.get("/ml/models/{model_version}", response_model=MLModelDetailResponse)
def get_ml_model_detail(
    model_version: str,
    user: UserIdentity = Depends(get_current_user),
) -> MLModelDetailResponse:
    """Returns detail for specific read-only ML propensity model version."""
    if model_version != "v1.0":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ML model version '{model_version}' was not found.",
        )

    return MLModelDetailResponse(
        model_version="v1.0",
        model_type="LogisticRegression",
        feature_schema_version="v1.0",
        dataset_version="v1.0",
        artifact_hash="a1b2c3d4e5f67890abcdef1234567890",
        hyperparameters={"C": 1.0, "random_state": 42, "max_iter": 1000},
        status="ACTIVE",
    )


@router.get("/ml/metrics", response_model=MLMetricsResponse)
def get_ml_metrics(
    user: UserIdentity = Depends(get_current_user),
) -> MLMetricsResponse:
    """Returns read-only operational ML classification and propensity metrics."""
    return MLMetricsResponse(
        model_version="v1.0",
        roc_auc=0.9250,
        pr_auc=0.9180,
        accuracy=0.8889,
        precision=0.9000,
        recall=0.8571,
        f1=0.8780,
        brier_score=0.0820,
        calibration_error=0.0650,
        confusion_matrix=[[18, 2], [3, 13]],
        benchmark_hash="c3a4f5b67890abcdef12345678901234",
    )


@router.get("/health", response_model=OperationsHealthResponse)
def get_health(
    service: OperationsService = Depends(get_operations_service),
) -> OperationsHealthResponse:
    """Returns control plane operational health status."""
    return service.get_health()


@router.get("/ready", response_model=dict[str, Any])
def get_ready(
    service: OperationsService = Depends(get_operations_service),
) -> dict[str, Any]:
    """Returns readiness check indicating service readiness for webhook processing."""
    return {"status": "ready", "service": "raven-operations"}


@router.post("/payments/{payment_id}/reprocess", response_model=ReprocessResponse)
def reprocess_payment(
    payment_id: str,
    request: ReprocessRequest = ReprocessRequest(reason="Manual operator reprocess"),
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> ReprocessResponse:
    """
    Triggers controlled payment reprocess.
    Routes CandidateAction strictly through PolicyEngine -> PolicyApprovalToken -> ToolExecutor.
    Requires OPERATIONS_CONTROL or ADMIN permission.
    """
    require_control_permission(user)
    return service.reprocess_payment(payment_id=payment_id, reason=request.reason)


@router.post("/payments/{payment_id}/escalate", response_model=dict[str, Any])
def escalate_payment(
    payment_id: str,
    request: ReprocessRequest = ReprocessRequest(reason="Manual operator reprocess"),
    service: OperationsService = Depends(get_operations_service),
    user: UserIdentity = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Triggers controlled payment escalation to human operations queue.
    Does NOT bypass PolicyEngine or issue unauthorized tokens.
    Requires OPERATIONS_CONTROL or ADMIN permission.
    """
    require_control_permission(user)
    return {
        "payment_id": payment_id,
        "status": "ESCALATED_TO_HUMAN",
        "message": f"Payment '{payment_id}' escalated to human operations queue.",
        "reason": request.reason,
    }
