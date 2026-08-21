"""
Evaluation Security Boundary Tests

Verifies that PolicyEngine and ToolExecutor security controls remain non-bypassable and authoritative
throughout evaluation framework runs.
"""

from datetime import datetime, timezone
from domain.entities.financial_event import FinancialEvent
from domain.enums import FinancialEventType
from domain.values.money import Money
from ml.evaluation.models import EvaluationCase
from ml.evaluation.strategies import RavenStrategy


def test_raven_strategy_preserves_captured_payment_policy_protection():
    strategy = RavenStrategy()

    payload = {"amount_minor": 100000}
    captured_events = [
        FinancialEvent(
            id="evt_cap_eval",
            event_hash=FinancialEvent.compute_canonical_hash(payload),
            merchant_id="mer_eval",
            entity_id="pay_captured_eval",
            event_type=FinancialEventType.PAYMENT_CAPTURED.value,
            amount=Money(amount_minor=100000),
            payload=payload,
            occurred_at=datetime.now(timezone.utc),
        )
    ]

    case = EvaluationCase(
        case_id="case_captured_eval",
        scenario_id="scenario_3",
        payment_id="pay_captured_eval",
        amount_minor=100000,
        currency="INR",
        ground_truth_root_cause="LATE_CAPTURE",
        ground_truth_recoverable=False,
        ground_truth_organic_recovery=False,
        ground_truth_optimal_action="NONE",
        events=captured_events,
    )

    decision = strategy.evaluate(case)

    # POL_001 blocks captured payment recovery attempts
    assert decision.decision == "BLOCKED"
    assert decision.execution_success is False
    assert decision.policy_violation is False
