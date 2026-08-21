"""
RAVEN Agent Orchestrator Module

Top-level orchestration pipeline coordinating the Autonomous Agent Trio, PolicyEngine, ToolExecutor,
VerificationAgent, and DecisionTrace lineage logging.

Pipeline flow:
1. State Reconstruction -> 2. Risk Identification -> 3. Root Cause Analysis ->
4. Recovery Planning -> 5. Deterministic EV Calculation -> 6. Policy Engine Evaluation ->
7. Approval Token Check -> 8. Tool Executor Dispatch -> 9. Post-Action Verification ->
10. Lineage Trace Snapshot
"""

from datetime import datetime, timezone
import uuid
from typing import Any
from agents.common.prompts import RECOVERY_PLANNER_PROMPT_VERSION, ROOT_CAUSE_PROMPT_VERSION
from agents.common.provider import BaseLLMProvider
from agents.observability import LLMObservabilityTelemetry
from agents.recovery_planner.planner import RecoveryPlanner
from agents.root_cause.analyst import RootCauseAnalyst
from agents.verifier.verifier import VerificationAgent
from domain.entities.customer import Customer
from domain.entities.decision_trace import DecisionTrace, DecisionTraceStatus
from domain.entities.merchant import Merchant
from domain.entities.payment import Payment, PaymentStatus
from domain.entities.recovery import OpportunityStatus, RecoveryOpportunity
from domain.state.reconstructor import StateReconstructor
from domain.values.money import Money
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext, PolicyDecision
from tools.executor import ToolExecutor


class AgentOrchestrator:
    """
    RAVEN Autonomous Recovery Pipeline Orchestrator.
    """

    def __init__(
        self,
        policy_engine: PolicyEngine | None = None,
        tool_executor: ToolExecutor | None = None,
        telemetry: LLMObservabilityTelemetry | None = None,
        recovery_planner: RecoveryPlanner | None = None,
    ) -> None:
        self.reconstructor = StateReconstructor()
        self.analyst = RootCauseAnalyst()
        self.planner = recovery_planner or RecoveryPlanner()
        self.verifier = VerificationAgent()
        self.policy_engine = policy_engine or PolicyEngine()
        self.tool_executor = tool_executor or ToolExecutor()
        self.telemetry = telemetry or LLMObservabilityTelemetry()

    def process_payment_failure(
        self,
        events: list[Any],
        merchant: Merchant,
        customer: Customer,
        opportunity_id: str | None = None,
        policy_context_overrides: dict[str, Any] | None = None,
        provider: BaseLLMProvider | None = None,
        error_code: str | None = None,
        gateway_message: str | None = None,
    ) -> DecisionTrace:
        """
        Executes complete autonomous recovery workflow end-to-end.
        """
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        opp_id = opportunity_id or f"opp_{uuid.uuid4().hex[:12]}"

        # Resolve primary payment_id and last error_code from events
        payment_id = "pay_unknown"
        resolved_error_code = error_code
        if events:
            first_event = events[0]
            if hasattr(first_event, "entity_id") and first_event.entity_id:
                payment_id = first_event.entity_id
            elif hasattr(first_event, "payment_id") and first_event.payment_id:
                payment_id = first_event.payment_id
            elif isinstance(first_event, dict):
                payment_id = first_event.get("entity_id") or first_event.get("payment_id") or "pay_unknown"

            if not resolved_error_code:
                last_event = events[-1]
                if hasattr(last_event, "payload") and isinstance(last_event.payload, dict):
                    resolved_error_code = last_event.payload.get("error_code")
                elif isinstance(last_event, dict) and "payload" in last_event:
                    resolved_error_code = last_event["payload"].get("error_code")

        # 1. State Reconstruction
        payment_before = self.reconstructor.reconstruct_payment_state(payment_id, events)
        amount = payment_before.amount if payment_before else Money.zero(currency=merchant.currency)

        # Initialize DecisionTrace
        trace = DecisionTrace(
            decision_id=trace_id,
            recovery_opportunity_id=opp_id,
            merchant_id=merchant.id,
            customer_id=customer.id,
            payment_id=payment_id,
            input_state_snapshot={
                "payment_status": payment_before.status if payment_before else "UNKNOWN",
                "amount_minor": amount.amount_minor,
                "currency": amount.currency,
            },
            evidence_references=[getattr(ev, "id", getattr(ev, "event_id", str(i))) for i, ev in enumerate(events)],
            status=DecisionTraceStatus.INITIATED,
        )

        # 2. Revenue Risk Identification
        RecoveryOpportunity(
            id=opp_id,
            merchant_id=merchant.id,
            payment_id=payment_id,
            amount_at_risk=amount,
            risk_category="PAYMENT_FAILURE_RECOVERY",
            status=OpportunityStatus.OPEN,
        )
        trace.mark_milestone("revenue_risk_identified")

        # 3. Root Cause Analysis
        start_rca = datetime.now(timezone.utc)
        rca_result = self.analyst.analyze(
            payment=payment_before,
            event_timeline=[ev.to_dict() if hasattr(ev, "to_dict") else {} for ev in events],
            customer=customer,
            merchant=merchant,
            provider=provider,
            error_code=resolved_error_code,
            gateway_message=gateway_message,
        )
        end_rca = datetime.now(timezone.utc)
        latency_rca = (end_rca - start_rca).total_seconds() * 1000.0

        trace.root_cause_result = rca_result.model_dump()
        trace.mark_milestone("root_cause_analyzed")

        # Telemetry for RCA
        self.telemetry.record_invocation(
            trace_id=trace_id,
            agent_name="RootCauseAnalyst",
            model=provider.default_model if provider else "deterministic_fallback",
            provider=provider.provider_name if provider else "heuristic",
            prompt_version=ROOT_CAUSE_PROMPT_VERSION,
            started_at=start_rca,
            completed_at=end_rca,
            latency_ms=latency_rca,
            success=True,
            reasoning_mode=rca_result.reasoning_mode,
            input_summary=f"Payment {payment_id} status={payment_before.status if payment_before else 'UNKNOWN'}",
            output_summary=f"RootCause={rca_result.root_cause} recoverability={rca_result.recoverability}",
        )

        # 4. Recovery Planning & 5. Deterministic Expected Value
        start_plan = datetime.now(timezone.utc)
        plan, value_summaries = self.planner.plan_recovery(
            rca=rca_result,
            payment=payment_before,
            customer=customer,
            merchant=merchant,
            provider=provider,
        )
        end_plan = datetime.now(timezone.utc)
        latency_plan = (end_plan - start_plan).total_seconds() * 1000.0

        trace.candidate_actions = [p.model_dump() for p in plan.proposals]
        trace.value_estimates = value_summaries
        trace.mark_milestone("recovery_plan_generated")

        # Telemetry for Recovery Planner
        self.telemetry.record_invocation(
            trace_id=trace_id,
            agent_name="RecoveryPlanner",
            model=provider.default_model if provider else "deterministic_fallback",
            provider=provider.provider_name if provider else "heuristic",
            prompt_version=RECOVERY_PLANNER_PROMPT_VERSION,
            started_at=start_plan,
            completed_at=end_plan,
            latency_ms=latency_plan,
            success=True,
            reasoning_mode=plan.reasoning_mode,
            input_summary=f"RCA={rca_result.root_cause}",
            output_summary=f"ProposalsCount={len(plan.proposals)} Top={plan.proposals[0].action_type if plan.proposals else 'NONE'}",
        )

        if not plan.proposals:
            trace.status = DecisionTraceStatus.ANALYZED
            return trace

        # Top ranked proposal
        top_proposal = plan.proposals[0]

        # Convert proposal into CandidateAction model
        candidate_action = CandidateAction(
            opportunity_id=opp_id,
            payment_id=payment_id,
            merchant_id=merchant.id,
            customer_id=customer.id,
            action_type=top_proposal.action_type,
            parameters=top_proposal.parameters,
            expected_recovery_value=amount,
            agent_confidence=top_proposal.agent_confidence,
            idempotency_key=f"idempotent_{trace_id}",
        )
        trace.selected_action = candidate_action.model_dump()

        # 6. Policy Engine Evaluation
        overrides = policy_context_overrides or {}
        policy_ctx = PolicyContext(
            payment=payment_before,
            customer=customer,
            merchant=merchant,
            **overrides,
        )

        decision: PolicyDecision = self.policy_engine.evaluate(candidate_action, policy_ctx)
        trace.policy_evaluations = [pe.model_dump() for pe in decision.policy_evaluations]
        trace.mark_milestone("policy_evaluated")

        # Handle Policy Decision Outcomes
        if decision.decision == "BLOCKED":
            trace.status = DecisionTraceStatus.POLICY_BLOCKED
            return trace

        if decision.decision == "ESCALATE_TO_HUMAN":
            trace.status = DecisionTraceStatus.ESCALATED
            return trace

        # Decision is APPROVED
        trace.status = DecisionTraceStatus.POLICY_APPROVED
        approval_token = decision.approval_token
        if approval_token:
            trace.policy_token_id = approval_token.token_id

        # 7 & 8. Tool Executor Dispatch
        try:
            exec_result = self.tool_executor.execute_action(
                action=candidate_action,
                decision=decision,
                approval_token=approval_token,
            )
            trace.execution_result = exec_result.model_dump()
            trace.status = DecisionTraceStatus.EXECUTED
            trace.mark_milestone("tool_executed")

            # Simulate post-action payment state for verification
            if exec_result.status in ("SIMULATED_SUCCESS", "SUCCESS"):
                post_payment = Payment(
                    id=payment_before.id if payment_before else "pay_recovered",
                    order_id=payment_before.order_id if payment_before else "ord_1",
                    merchant_id=merchant.id,
                    customer_id=customer.id,
                    amount=amount,
                    status=PaymentStatus.CAPTURED if candidate_action.action_type != "ESCALATE_TO_HUMAN" else payment_before.status,
                )
            else:
                post_payment = payment_before
        except Exception as e:
            trace.status = DecisionTraceStatus.FAILED
            trace.execution_result = {"error": str(e), "status": "FAILED"}
            return trace

        # 9. Verification Agent
        ver_result = self.verifier.verify(
            payment_before=payment_before,
            payment_after=post_payment,
            execution_result=exec_result,
            action_id=candidate_action.id,
        )
        trace.verification_result = ver_result.model_dump()
        trace.status = DecisionTraceStatus.VERIFIED
        trace.mark_milestone("outcome_verified")

        return trace
