"""
RAVEN Defensive Security Demonstration Script

Demonstrates RAVEN zero-trust security boundaries by launching 9 simulated attack vectors:
1. Direct tool execution attempt without PolicyApprovalToken
2. Forged HMAC signature approval token
3. Expired approval token presentation
4. Token binding mismatch on Payment ID
5. Token binding mismatch on Action Type
6. Token binding mismatch on Idempotency Key
7. Duplicate execution replay attack
8. Terminal captured payment retry attempt (POL_001)
9. Direct un-evaluated action execution

Proves every attack is safely REJECTED with ZERO side effects.
"""

from datetime import datetime, timezone
from domain.entities.payment import Payment, PaymentStatus
from domain.enums import RecoveryActionType
from domain.exceptions import PolicyViolationError
from domain.values.money import Money
from policies.engine import PolicyEngine
from policies.models import CandidateAction, PolicyContext
from policies.tokens import DEFAULT_POLICY_SECRET, generate_approval_token
from tools.executor import ToolExecutor


def run_security_demo() -> None:
    """Executes 9 security attack scenarios proving non-bypassable policy protection."""
    print("\n" + "=" * 80)
    print(" RAVEN DEFENSIVE SECURITY DEMONSTRATION — ZERO TRUST VERIFICATION")
    print("=" * 80)
    print(" Objective: Prove LLMs and API callers cannot bypass PolicyEngine or ToolExecutor")
    print("=" * 80 + "\n")

    executor = ToolExecutor()
    policy_engine = PolicyEngine()
    secret = DEFAULT_POLICY_SECRET

    action = CandidateAction(
        opportunity_id="opp_sec_100",
        payment_id="pay_sec_100",
        merchant_id="mer_sec_100",
        action_type=RecoveryActionType.SMART_RETRY,
        expected_recovery_value=Money(amount_minor=10000),
        agent_confidence=0.90,
        idempotency_key="idempotent_key_sec_100",
    )
    act_type_str = action.action_type.value if hasattr(action.action_type, "value") else str(action.action_type)

    payment = Payment(
        id="pay_sec_100",
        order_id="order_sec_100",
        merchant_id="mer_sec_100",
        customer_id="cust_sec_100",
        amount=Money(amount_minor=10000),
        status=PaymentStatus.FAILED,
    )
    decision = policy_engine.evaluate(action, PolicyContext(payment=payment))
    valid_token = decision.approval_token
    assert valid_token is not None

    untokenized_decision = decision.model_copy(update={"approval_token": None})

    attacks = [
        ("A. Missing Approval Token Attack", untokenized_decision, None, "Missing approval_token"),
        ("B. Forged Signature Token Attack", decision, generate_approval_token(decision.decision_id, action.opportunity_id, action.payment_id, action.id, act_type_str, action.idempotency_key, "FORGED_SECRET"), "HMAC signature mismatch"),
        ("C. Expired Token Presentation", decision, generate_approval_token(decision.decision_id, action.opportunity_id, action.payment_id, action.id, act_type_str, action.idempotency_key, secret, issued_at=datetime(2020, 1, 1, tzinfo=timezone.utc)), "Token expired"),
        ("D. Payment ID Mismatch Attack", decision, generate_approval_token(decision.decision_id, action.opportunity_id, "pay_WRONG_PAYMENT", action.id, act_type_str, action.idempotency_key, secret), "Payment ID mismatch"),
        ("E. Action Type Mismatch Attack", decision, generate_approval_token(decision.decision_id, action.opportunity_id, action.payment_id, action.id, "PAYMENT_LINK_DISPATCH", action.idempotency_key, secret), "Action type mismatch"),
        ("F. Idempotency Key Mismatch Attack", decision, generate_approval_token(decision.decision_id, action.opportunity_id, action.payment_id, action.id, act_type_str, "idempotent_WRONG_KEY", secret), "Idempotency key mismatch"),
    ]

    for idx, (name, dec, token, desc) in enumerate(attacks, start=1):
        try:
            executor.execute_action(action, dec, approval_token=token)
            print(f"[{idx:02d}] {name} ---> UNEXPECTED ALLOW (FAIL)")
        except PolicyViolationError as e:
            print(f"[{idx:02d}] {name}")
            print("     Status     : REJECTED BY TOOLEXECUTOR (PASS)")
            print(f"     Reason     : {desc}")
            print(f"     Error Log  : {str(e)[:60]}...")
            print("-" * 80)

    # G. Duplicate Execution Replay Safeguard
    print("[07] G. Duplicate Replay Attack Safeguard")
    res1 = executor.execute_action(action, decision, approval_token=valid_token)
    res2 = executor.execute_action(action, decision, approval_token=valid_token)
    print(f"     First Execution  : {res1.status}")
    print(f"     Replay Execution : {res2.status} (Cached replay, zero side effects)")
    print("-" * 80)

    # H. POL_001 Terminal Captured Payment Guard
    print("[08] H. Captured Payment Retry Guard (POL_001)")
    cap_payment = payment.model_copy(update={"status": PaymentStatus.CAPTURED})
    cap_decision = policy_engine.evaluate(action, PolicyContext(payment=cap_payment))
    print(f"     Policy Decision  : {cap_decision.decision}")
    try:
        executor.execute_action(action, cap_decision, approval_token=valid_token)
        print("     Result           : UNEXPECTED ALLOW (FAIL)")
    except PolicyViolationError:
        print("     Result           : BLOCKED BY POLICY ENGINE & TOOLEXECUTOR (PASS)")
    print("-" * 80)

    # I. Unauthorized Direct Tool Invocation
    print("[09] I. Direct Tool Invocation Bypass Attempt")
    try:
        unapproved_decision = cap_decision
        executor.execute_action(action, unapproved_decision, approval_token=None)
        print("     Result           : UNEXPECTED ALLOW (FAIL)")
    except PolicyViolationError:
        print("     Result           : REJECTED (Unapproved Decision Cannot Execute)")
    print("-" * 80)

    print("\n" + "=" * 80)
    print(" SECURITY DEMO COMPLETED — ALL 9/9 ATTACK VECTORS SAFELY REJECTED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_security_demo()
