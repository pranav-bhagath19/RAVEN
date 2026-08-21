"""
Unit and Integration Tests for Simulated Side-Effect Tools & Phase 2 Scenarios Integration
"""

from domain.entities.payment import Payment, PaymentStatus
from domain.enums import RecoveryActionType
from domain.values.money import Money
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext
from simulator.generator import SyntheticDataGenerator
from tools.executor import ToolExecutor
from tools.simulated import (
    EscalateToHumanTool,
    FallbackChannelNotifyTool,
    PaymentLinkDispatchTool,
    SmartRetryTool,
)


def test_simulated_smart_retry_tool():
    tool = SmartRetryTool()
    result = tool.execute(action_id="act_1", payment_id="pay_1", parameters={"delay_seconds": 600})

    assert result.status == "SIMULATED_SUCCESS"
    assert result.tool_name == "smart_retry"
    assert result.payload["delay_seconds"] == 600


def test_simulated_payment_link_tool():
    tool = PaymentLinkDispatchTool()
    result = tool.execute(action_id="act_2", payment_id="pay_2", parameters={"channel": "WHATSAPP"})

    assert result.status == "SIMULATED_SUCCESS"
    assert result.tool_name == "payment_link_dispatch"
    assert "payment_link_url" in result.payload


def test_simulated_fallback_notify_tool():
    tool = FallbackChannelNotifyTool()
    result = tool.execute(action_id="act_3", payment_id="pay_3", parameters={"channel": "SMS"})

    assert result.status == "SIMULATED_SUCCESS"
    assert result.tool_name == "fallback_channel_notify"
    assert result.payload["channel"] == "SMS"


def test_simulated_escalate_human_tool():
    tool = EscalateToHumanTool()
    result = tool.execute(action_id="act_4", payment_id="pay_4", parameters={"reason": "High-value transaction"})

    assert result.status == "SIMULATED_SUCCESS"
    assert result.tool_name == "escalate_to_human"
    assert "ticket_id" in result.payload


def test_scenario_1_integration_policy_approval_and_execution():
    """
    Integrates Phase 2 Scenario 1 (Transient Gateway Timeout):
    Generates CandidateAction -> PolicyEngine evaluates and approves -> ToolExecutor executes SmartRetryTool.
    """
    generator = SyntheticDataGenerator(seed=42)
    scen1 = generator.generate_scenario_1_transient_gateway_timeout()

    gt = scen1.ground_truth
    action = CandidateAction(
        opportunity_id=f"opp_{gt.payment_id}",
        payment_id=gt.payment_id,
        merchant_id="mer_scen1",
        action_type=RecoveryActionType.SMART_RETRY,
        parameters={"delay_seconds": gt.expected_optimal_delay_seconds},
        expected_recovery_value=Money(amount_minor=150000),
        agent_confidence=0.92,
        idempotency_key=f"idempotent_scen1_{gt.payment_id}",
    )
    payment = Payment(
        id=gt.payment_id,
        order_id=f"order_{gt.payment_id}",
        merchant_id="mer_scen1",
        customer_id="cust_scen1",
        amount=Money(amount_minor=150000),
        status=PaymentStatus.FAILED,
    )
    context = PolicyContext(payment=payment)

    engine = PolicyEngine()
    executor = ToolExecutor()

    # 1. Policy Evaluation
    decision = engine.evaluate(action, context)
    assert decision.decision == "APPROVED"
    assert decision.approval_token is not None

    # 2. Tool Execution
    exec_result = executor.execute_action(action, decision, decision.approval_token)
    assert exec_result.status == "SIMULATED_SUCCESS"
    assert exec_result.tool_name == "smart_retry"
    assert exec_result.payload["delay_seconds"] == 900


def test_scenario_2_integration_hard_decline_policy_approval():
    """
    Integrates Phase 2 Scenario 2 (Hard Card Decline):
    Generates CandidateAction (PAYMENT_LINK_DISPATCH) -> PolicyEngine approves -> ToolExecutor dispatches link.
    """
    generator = SyntheticDataGenerator(seed=42)
    scen2 = generator.generate_scenario_2_hard_card_decline()

    gt = scen2.ground_truth
    action = CandidateAction(
        opportunity_id=f"opp_{gt.payment_id}",
        payment_id=gt.payment_id,
        merchant_id="mer_scen2",
        action_type=RecoveryActionType.PAYMENT_LINK_DISPATCH,
        parameters={"channel": "WHATSAPP"},
        expected_recovery_value=Money(amount_minor=499900),
        agent_confidence=0.88,
        idempotency_key=f"idempotent_scen2_{gt.payment_id}",
    )
    payment = Payment(
        id=gt.payment_id,
        order_id=f"order_{gt.payment_id}",
        merchant_id="mer_scen2",
        customer_id="cust_scen2",
        amount=Money(amount_minor=499900),
        status=PaymentStatus.FAILED,
    )
    context = PolicyContext(payment=payment)

    engine = PolicyEngine()
    executor = ToolExecutor()

    decision = engine.evaluate(action, context)
    assert decision.decision == "APPROVED"

    exec_result = executor.execute_action(action, decision, decision.approval_token)
    assert exec_result.status == "SIMULATED_SUCCESS"
    assert exec_result.tool_name == "payment_link_dispatch"
    assert "https://rzp.io/i/" in exec_result.payload["payment_link_url"]
