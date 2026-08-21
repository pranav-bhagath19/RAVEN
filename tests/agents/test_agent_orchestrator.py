"""
Integration Tests for Agent Orchestrator Pipeline
"""

from datetime import datetime, timezone
from agents.common.provider import MockLLMProvider
from agents.orchestrator import AgentOrchestrator
from agents.recovery_planner.models import CandidateActionProposal, RecoveryPlan
from agents.root_cause.models import RootCauseAnalysis
from domain.entities.customer import Customer
from domain.entities.decision_trace import DecisionTraceStatus
from domain.entities.financial_event import FinancialEvent
from domain.entities.merchant import Merchant
from domain.enums import FinancialEventType, RecoveryActionType
from domain.values.money import Money


def create_sample_context():
    merchant = Merchant(id="mer_orch_1", name="Test Merchant", currency="INR")
    customer = Customer(
        id="cust_orch_1",
        merchant_id="mer_orch_1",
        email="cust@test.com",
        phone="+919876543210",
        name="Test Customer",
    )
    payload = {"amount_minor": 150000, "error_code": "GATEWAY_TIMED_OUT"}
    events = [
        FinancialEvent(
            id="evt_orch_1",
            event_hash=FinancialEvent.compute_canonical_hash(payload),
            merchant_id="mer_orch_1",
            entity_id="pay_orch_1",
            event_type=FinancialEventType.PAYMENT_FAILED.value if hasattr(FinancialEventType.PAYMENT_FAILED, "value") else str(FinancialEventType.PAYMENT_FAILED),
            amount=Money(amount_minor=150000),
            occurred_at=datetime.now(timezone.utc),
            payload=payload,
        )
    ]
    return merchant, customer, events


def test_orchestrator_successful_pipeline():
    orchestrator = AgentOrchestrator()
    merchant, customer, events = create_sample_context()

    def mock_generator(prompt, response_model):
        if response_model == RootCauseAnalysis:
            return RootCauseAnalysis(
                payment_id="pay_orch_1",
                root_cause="GATEWAY_TIMED_OUT",
                explanation="Gateway timeout during payment processing.",
                evidence=["evt_orch_1"],
                recoverability="HIGH",
                confidence=0.92,
                recommended_direction="Smart retry",
            )
        elif response_model == RecoveryPlan:
            return RecoveryPlan(
                payment_id="pay_orch_1",
                proposals=[
                    CandidateActionProposal(
                        action_type=RecoveryActionType.SMART_RETRY,
                        reasoning="Retry after 15 minutes",
                        predicted_success_probability=0.85,
                        agent_confidence=0.90,
                        recommended_delay_seconds=900,
                    )
                ],
            )
        raise ValueError("Unknown model")

    provider = MockLLMProvider(mock_response_generator=mock_generator)

    trace = orchestrator.process_payment_failure(
        events=events,
        merchant=merchant,
        customer=customer,
        provider=provider,
    )

    assert trace.status == DecisionTraceStatus.VERIFIED
    assert trace.policy_token_id is not None
    assert trace.execution_result["status"] == "SIMULATED_SUCCESS"
    assert trace.verification_result["is_recovered"] is True


def test_orchestrator_policy_blocked():
    orchestrator = AgentOrchestrator()
    merchant, customer, _ = create_sample_context()

    payload = {"amount_minor": 150000}
    events_captured = [
        FinancialEvent(
            id="evt_orch_cap",
            event_hash=FinancialEvent.compute_canonical_hash(payload),
            merchant_id="mer_orch_1",
            entity_id="pay_orch_cap",
            event_type=FinancialEventType.PAYMENT_CAPTURED.value if hasattr(FinancialEventType.PAYMENT_CAPTURED, "value") else str(FinancialEventType.PAYMENT_CAPTURED),
            amount=Money(amount_minor=150000),
            occurred_at=datetime.now(timezone.utc),
            payload=payload,
        )
    ]

    trace = orchestrator.process_payment_failure(
        events=events_captured,
        merchant=merchant,
        customer=customer,
        provider=None,  # Fallback
    )

    # POL_001 blocks captured payment recovery
    assert trace.status == DecisionTraceStatus.POLICY_BLOCKED
    assert trace.policy_token_id is None
    assert trace.execution_result is None


def test_orchestrator_human_escalation():
    orchestrator = AgentOrchestrator()
    merchant, customer, _ = create_sample_context()

    # High value transaction (> ₹10,000 / 1,000,000 minor units) triggers POL_004 escalation
    payload = {"amount_minor": 1500000, "error_code": "GATEWAY_TIMED_OUT"}
    high_val_events = [
        FinancialEvent(
            id="evt_highval",
            event_hash=FinancialEvent.compute_canonical_hash(payload),
            merchant_id="mer_orch_1",
            entity_id="pay_highval",
            event_type=FinancialEventType.PAYMENT_FAILED.value if hasattr(FinancialEventType.PAYMENT_FAILED, "value") else str(FinancialEventType.PAYMENT_FAILED),
            amount=Money(amount_minor=1500000),
            occurred_at=datetime.now(timezone.utc),
            payload=payload,
        )
    ]

    trace = orchestrator.process_payment_failure(
        events=high_val_events,
        merchant=merchant,
        customer=customer,
        provider=None,
    )

    assert trace.status == DecisionTraceStatus.ESCALATED
    assert trace.policy_token_id is None


def test_orchestrator_llm_fallback():
    orchestrator = AgentOrchestrator()
    merchant, customer, events = create_sample_context()

    # Provider is None -> executes fallback pipeline cleanly
    trace = orchestrator.process_payment_failure(
        events=events,
        merchant=merchant,
        customer=customer,
        provider=None,
        error_code="GATEWAY_TIMED_OUT",
    )

    assert trace.status == DecisionTraceStatus.VERIFIED
    assert trace.root_cause_result["reasoning_mode"] == "DETERMINISTIC_FALLBACK"
