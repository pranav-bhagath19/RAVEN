"""
Unit Tests for Baseline Strategies (Always Retry and Rule-Based)
"""

from datetime import datetime, timezone
from domain.entities.financial_event import FinancialEvent
from domain.values.money import Money
from ml.evaluation.baselines import AlwaysRetryStrategy, RuleBasedStrategy
from ml.evaluation.models import EvaluationCase


def create_mock_case(scenario_id: str, error_code: str, recoverable: bool, optimal_action: str) -> EvaluationCase:
    payload = {"amount_minor": 100000, "error_code": error_code}
    event = FinancialEvent(
        id=f"evt_{scenario_id}",
        event_hash=FinancialEvent.compute_canonical_hash(payload),
        merchant_id="mer_eval",
        entity_id=f"pay_{scenario_id}",
        event_type="payment.failed",
        amount=Money(amount_minor=100000),
        payload=payload,
        occurred_at=datetime.now(timezone.utc),
    )

    return EvaluationCase(
        case_id=f"case_{scenario_id}",
        scenario_id=scenario_id,
        payment_id=f"pay_{scenario_id}",
        amount_minor=100000,
        currency="INR",
        ground_truth_root_cause="GATEWAY_TIMED_OUT" if "TIMEOUT" in error_code or "TIMED_OUT" in error_code else "HARD_DECLINE",
        ground_truth_recoverable=recoverable,
        ground_truth_organic_recovery=False,
        ground_truth_optimal_action=optimal_action,
        events=[event],
    )


def test_always_retry_strategy_behavior():
    strategy = AlwaysRetryStrategy()

    # Case 1: Transient timeout
    case_timeout = create_mock_case("scenario_1", "GATEWAY_TIMED_OUT", True, "SMART_RETRY")
    dec_timeout = strategy.evaluate(case_timeout)

    assert dec_timeout.strategy_name == "Always Retry"
    assert dec_timeout.action_type == "SMART_RETRY"
    assert dec_timeout.execution_success is True
    assert dec_timeout.root_cause_prediction is None

    # Case 2: Hard decline
    case_decline = create_mock_case("scenario_2", "CARD_EXPIRED", False, "NONE")
    dec_decline = strategy.evaluate(case_decline)

    assert dec_decline.action_type == "SMART_RETRY"
    assert dec_decline.execution_success is False


def test_rule_based_strategy_behavior():
    strategy = RuleBasedStrategy()

    # Case 1: Timeout error code -> SMART_RETRY
    case_timeout = create_mock_case("scenario_1", "GATEWAY_TIMED_OUT", True, "SMART_RETRY")
    dec_timeout = strategy.evaluate(case_timeout)

    assert dec_timeout.strategy_name == "Rule-Based"
    assert dec_timeout.action_type == "SMART_RETRY"
    assert dec_timeout.root_cause_prediction == "GATEWAY_TIMED_OUT"
    assert dec_timeout.execution_cost_minor == 0

    # Case 2: Hard decline -> NO_ACTION
    case_decline = create_mock_case("scenario_2", "CARD_EXPIRED", False, "NONE")
    dec_decline = strategy.evaluate(case_decline)

    assert dec_decline.action_type == "NONE"
    assert dec_decline.execution_attempted is False
