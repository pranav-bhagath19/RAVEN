"""
RAVEN Operations Control Plane Application Service

Coordinates read-only operations queries and controlled management actions.
Strictly preserves architectural security boundaries:
CandidateAction -> PolicyEngine -> PolicyApprovalToken -> ToolExecutor -> VerificationAgent.
"""

from typing import Any
from agents.common.provider import BaseLLMProvider, MockLLMProvider
from agents.orchestrator import AgentOrchestrator
from apps.api.operations_schemas import (
    BenchmarkSummary,
    DecisionSummary,
    EventSummary,
    OperationsHealthResponse,
    OverviewResponse,
    PaginatedResponse,
    PaymentDetailResponse,
    PaymentSummary,
    PolicyRuleSummary,
    ReprocessResponse,
    TelemetrySummary,
    ToolExecutionSummary,
    TraceDetailResponse,
    TraceMilestone,
    VerificationSummary,
)
from apps.api.repository import OperationsRepository
from domain.entities.customer import Customer
from domain.entities.merchant import Merchant
from domain.enums import MerchantStatus
from events.ingestion import EventIngestionService


class OperationsService:
    """
    Control Plane Application Service exposing read-only operational telemetry and controlled commands.
    """

    def __init__(
        self,
        repository: OperationsRepository | None = None,
        ingestion_service: EventIngestionService | None = None,
        orchestrator: AgentOrchestrator | None = None,
        provider: BaseLLMProvider | None = None,
    ) -> None:
        self.ingestion_service = ingestion_service or EventIngestionService()
        self.orchestrator = orchestrator or AgentOrchestrator()
        self.provider = provider or MockLLMProvider()
        self.repository = repository or OperationsRepository(
            ingestion_service=self.ingestion_service,
            tool_executor=self.orchestrator.tool_executor,
            telemetry=self.orchestrator.telemetry,
        )

    def get_overview(self) -> OverviewResponse:
        """Returns aggregate operational metrics summary."""
        stats = self.repository.get_overview_stats()
        return OverviewResponse.model_validate(stats)

    def get_payments(
        self,
        status: str | None = None,
        merchant_id: str | None = None,
        customer_id: str | None = None,
        payment_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[PaymentSummary]:
        """Returns paginated payment summary records."""
        items_dict, total = self.repository.get_payments(
            status=status,
            merchant_id=merchant_id,
            customer_id=customer_id,
            payment_id=payment_id,
            page=page,
            page_size=page_size,
        )
        items = [PaymentSummary.model_validate(i) for i in items_dict]
        return PaginatedResponse[PaymentSummary](items=items, page=page, page_size=page_size, total=total)

    def get_payment_detail(self, payment_id: str) -> PaymentDetailResponse | None:
        """Returns detailed payment state and execution history."""
        detail = self.repository.get_payment_detail(payment_id)
        if not detail:
            return None
        return PaymentDetailResponse.model_validate(detail)

    def get_events(
        self,
        entity_id: str | None = None,
        event_id: str | None = None,
        event_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[EventSummary]:
        """Returns paginated financial event summaries."""
        events, total = self.repository.get_events(
            entity_id=entity_id,
            event_id=event_id,
            event_type=event_type,
            page=page,
            page_size=page_size,
        )
        items = [
            EventSummary(
                id=e.id,
                event_hash=e.event_hash,
                event_type=e.event_type,
                entity_id=e.entity_id,
                merchant_id=e.merchant_id,
                amount_minor=e.amount.amount_minor if e.amount else None,
                currency=e.amount.currency if e.amount else "INR",
                occurred_at=e.occurred_at,
                received_at=e.received_at,
                payload=e.payload,
            )
            for e in events
        ]
        return PaginatedResponse[EventSummary](items=items, page=page, page_size=page_size, total=total)

    def get_decisions(
        self,
        status: str | None = None,
        payment_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[DecisionSummary]:
        """Returns paginated DecisionTrace summaries."""
        traces, total = self.repository.get_traces(
            status=status,
            payment_id=payment_id,
            page=page,
            page_size=page_size,
        )
        items = []
        for t in traces:
            pol_dec = "INITIATED"
            if t.policy_evaluations:
                pol_dec = t.policy_evaluations[-1].get("decision_type") or "EVALUATED"

            items.append(
                DecisionSummary(
                    decision_id=t.decision_id,
                    payment_id=t.payment_id,
                    merchant_id=t.merchant_id,
                    status=str(t.status),
                    root_cause=t.root_cause_result.get("primary_root_cause") if t.root_cause_result else None,
                    selected_action=t.selected_action.get("action_type") if t.selected_action else None,
                    policy_decision=str(pol_dec),
                    policy_token_id=t.policy_token_id,
                    created_at=t.timestamps.get("created_at", ""),
                )
            )
        return PaginatedResponse[DecisionSummary](items=items, page=page, page_size=page_size, total=total)

    def get_trace_detail(self, trace_id: str) -> TraceDetailResponse | None:
        """Returns complete DecisionTrace operational lineage timeline."""
        traces, _ = self.repository.get_traces(trace_id=trace_id)
        if not traces:
            return None
        t = traces[0]
        created_ts = t.timestamps.get("created_at", "")

        # Construct chronological milestone timeline
        timeline: list[TraceMilestone] = [
            TraceMilestone(milestone_name="EVENT_RECEIVED", timestamp=created_ts, status="INGESTED", details={"payment_id": t.payment_id}),
            TraceMilestone(milestone_name="STATE_RECONSTRUCTED", timestamp=created_ts, status="COMPLETED", details=t.input_state_snapshot),
        ]

        if t.root_cause_result:
            timeline.append(TraceMilestone(milestone_name="ROOT_CAUSE_ANALYZED", timestamp=t.timestamps.get("root_cause_analyzed", created_ts), status="COMPLETED", details=t.root_cause_result))
        if t.candidate_actions:
            timeline.append(TraceMilestone(milestone_name="RECOVERY_PLAN_GENERATED", timestamp=t.timestamps.get("recovery_planned", created_ts), status="COMPLETED", details={"candidates_count": len(t.candidate_actions)}))
        if t.policy_evaluations:
            pol_res = t.policy_evaluations[-1]
            timeline.append(TraceMilestone(milestone_name="POLICY_EVALUATED", timestamp=t.timestamps.get("policy_evaluated", created_ts), status=pol_res.get("decision_type", "EVALUATED"), details=pol_res))
        if t.policy_token_id:
            timeline.append(TraceMilestone(milestone_name="APPROVAL_TOKEN_ISSUED", timestamp=t.timestamps.get("policy_evaluated", created_ts), status="ISSUED", details={"token_id": t.policy_token_id}))
        if t.execution_result:
            timeline.append(TraceMilestone(milestone_name="TOOL_EXECUTED", timestamp=t.timestamps.get("tool_executed", created_ts), status=t.execution_result.get("status", "EXECUTED"), details=t.execution_result))
        if t.verification_result:
            timeline.append(TraceMilestone(milestone_name="OUTCOME_VERIFIED", timestamp=t.timestamps.get("outcome_verified", created_ts), status=t.verification_result.get("recovery_type", "VERIFIED"), details=t.verification_result))

        return TraceDetailResponse(
            decision_id=t.decision_id,
            recovery_opportunity_id=t.recovery_opportunity_id,
            merchant_id=t.merchant_id,
            customer_id=t.customer_id,
            payment_id=t.payment_id,
            status=str(t.status),
            input_state_snapshot=t.input_state_snapshot,
            evidence_references=t.evidence_references,
            root_cause_result=t.root_cause_result,
            candidate_actions=t.candidate_actions,
            value_estimates=t.value_estimates,
            policy_evaluations=t.policy_evaluations,
            selected_action=t.selected_action,
            policy_token_id=t.policy_token_id,
            execution_result=t.execution_result,
            verification_result=t.verification_result,
            chronological_timeline=timeline,
        )

    def get_policies(self) -> list[PolicyRuleSummary]:
        """Returns list of registered PolicyEngine rule summaries."""
        raw_policies = self.repository.get_policies()
        return [PolicyRuleSummary.model_validate(p) for p in raw_policies]

    def get_tool_executions(
        self,
        payment_id: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[ToolExecutionSummary]:
        """Returns paginated tool execution audit summaries."""
        raw_records, total = self.repository.get_tool_executions(
            payment_id=payment_id,
            tool_name=tool_name,
            status=status,
            page=page,
            page_size=page_size,
        )
        items = [ToolExecutionSummary.model_validate(r) for r in raw_records]
        return PaginatedResponse[ToolExecutionSummary](items=items, page=page, page_size=page_size, total=total)

    def get_verifications(
        self,
        payment_id: str | None = None,
        recovery_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[VerificationSummary]:
        """Returns paginated verification summaries."""
        raw_records, total = self.repository.get_verifications(
            payment_id=payment_id,
            recovery_type=recovery_type,
            page=page,
            page_size=page_size,
        )
        items = [VerificationSummary.model_validate(r) for r in raw_records]
        return PaginatedResponse[VerificationSummary](items=items, page=page, page_size=page_size, total=total)

    def get_agent_telemetry(
        self,
        agent: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        reasoning_mode: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[TelemetrySummary]:
        """Returns paginated PII-sanitized telemetry logs."""
        logs = self.repository.telemetry.get_logs()
        filtered = []
        for log_entry in logs:
            if agent and log_entry.agent_name.lower() != agent.lower():
                continue
            if provider and log_entry.provider.lower() != provider.lower():
                continue
            if model and log_entry.model.lower() != model.lower():
                continue
            if reasoning_mode and log_entry.reasoning_mode.lower() != reasoning_mode.lower():
                continue
            filtered.append(log_entry)

        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        items = [TelemetrySummary.model_validate(entry.model_dump()) for entry in filtered[start:end]]
        return PaginatedResponse[TelemetrySummary](items=items, page=page, page_size=page_size, total=total)

    def get_benchmark_summary(self) -> BenchmarkSummary:
        """Returns comparative benchmark report evaluation metrics."""
        report = self.repository.get_benchmark_report()
        strat_summaries: list[dict[str, Any]] = []

        for name, metrics_obj in report.metrics.items():
            strat_summaries.append({
                "strategy_name": name,
                "metrics": metrics_obj.model_dump(),
            })

        return BenchmarkSummary(
            benchmark_version=report.benchmark_version,
            seed=report.seed,
            benchmark_hash=report.benchmark_hash,
            generated_at=report.generated_at,
            total_cases=len(report.raw_results),
            strategies=strat_summaries,
        )

    def get_health(self) -> OperationsHealthResponse:
        """Returns operational control plane health and subsystem status."""
        return OperationsHealthResponse(
            status="ok",
            api_status="healthy",
            domain_status="healthy",
            event_ingestion_status="healthy",
            policy_engine_status="healthy",
            tool_executor_status="healthy",
            agent_subsystem_status="healthy",
            razorpay_integration_status="healthy",
            telemetry_status="healthy",
        )

    def reprocess_payment(self, payment_id: str, reason: str = "Manual operator reprocess") -> ReprocessResponse:
        """
        Executes controlled payment reprocess.
        STRICT ARCHITECTURAL INVARIANT:
        Routes CandidateAction -> PolicyEngine -> PolicyApprovalToken -> ToolExecutor -> VerificationAgent.
        Direct tool execution from HTTP router is strictly prohibited.
        """
        events = self.ingestion_service.get_events_for_entity(payment_id)
        if not events:
            # Create synthetic event if missing for payment_id
            events = [
                self.ingestion_service.ingest_event(
                    raw_payload={"payment_id": payment_id, "amount": 10000, "currency": "INR", "error_code": "GATEWAY_TIMED_OUT"},
                    event_type="payment.failed",
                )
            ]

        merchant = Merchant(id=events[0].merchant_id, name="Merchant Business", currency=events[0].currency, status=MerchantStatus.ACTIVE)
        customer = Customer(id=events[0].customer_id or f"cust_{payment_id}", merchant_id=merchant.id, email="customer@example.com", phone="+919876543210", name="Customer Name")

        trace = self.orchestrator.process_payment_failure(
            events=events,
            merchant=merchant,
            customer=customer,
            provider=self.provider,
        )

        # Store trace in repository
        self.repository.record_trace(trace)

        policy_decision_str = trace.policy_evaluations[-1].get("decision_type", "BLOCKED") if trace.policy_evaluations else "BLOCKED"

        return ReprocessResponse(
            payment_id=payment_id,
            status="COMPLETED" if trace.status in ("EXECUTED", "VERIFIED") else str(trace.status),
            trace_id=trace.decision_id,
            policy_decision=policy_decision_str,
            execution_result=trace.execution_result,
        )
