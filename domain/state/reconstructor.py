"""
RAVEN Deterministic State Reconstructor

Reconstructs true entity state from a list of normalized FinancialEvent records.
Applies deterministic state transition rules, terminal state guards,
out-of-order event reordering, and conflict resolution logic.
"""

from datetime import datetime, timezone
from domain.entities.financial_event import FinancialEvent
from domain.entities.payment import Payment, PaymentAttempt
from domain.enums import PaymentAttemptStatus, PaymentMethodType, PaymentStatus
from domain.exceptions import InvalidStateTransitionError
from domain.values.money import Money


class StateReconstructor:
    """
    Deterministic Reconstructor evaluating event sequences to derive true Payment state.
    """

    @staticmethod
    def reconstruct_payment_state(
        payment_id: str,
        events: list[FinancialEvent],
        initial_payment: Payment | None = None,
    ) -> Payment:
        """
        Reconstructs true Payment state by playing sorted FinancialEvent records.
        """
        payment_events = [
            e for e in events if e.entity_id == payment_id or e.payload.get("payment_id") == payment_id
        ]

        sorted_events = sorted(
            payment_events,
            key=lambda e: (e.occurred_at, e.sequence_number)
        )

        if initial_payment:
            payment = initial_payment.model_copy(deep=True)
        else:
            first_evt = sorted_events[0] if sorted_events else None
            initial_money = (
                first_evt.amount
                if first_evt and first_evt.amount
                else Money.zero(first_evt.currency if first_evt else "INR")
            )

            payment = Payment(
                id=payment_id,
                order_id=first_evt.order_id if first_evt and first_evt.order_id else f"order_{payment_id}",
                merchant_id=first_evt.merchant_id if first_evt else "mer_default",
                customer_id=first_evt.customer_id if first_evt and first_evt.customer_id else "cust_default",
                amount=initial_money,
                status=PaymentStatus.CREATED,
                created_at=first_evt.occurred_at if first_evt else datetime.now(timezone.utc),
            )

        attempt_counter = 1

        for evt in sorted_events:
            event_type = evt.event_type.lower()
            payload = evt.payload

            # Terminal state protection rule:
            # If current state is CAPTURED, ignore out-of-order FAILED events
            if payment.status == PaymentStatus.CAPTURED and "failed" in event_type:
                continue

            target_status: PaymentStatus | None = None

            if "captured" in event_type or "order.paid" in event_type:
                target_status = PaymentStatus.CAPTURED
            elif "authorized" in event_type:
                target_status = PaymentStatus.AUTHORIZED
            elif "failed" in event_type:
                target_status = PaymentStatus.FAILED
            elif "refunded" in event_type:
                target_status = PaymentStatus.REFUNDED
            elif "pending" in event_type or "ambiguous" in event_type:
                target_status = PaymentStatus.AMBIGUOUS

            if target_status and payment.status != target_status:
                try:
                    payment.transition_to(target_status, timestamp=evt.occurred_at)
                except InvalidStateTransitionError:
                    # Ignore illegal transition attempts on event replay
                    pass

            if "failed" in event_type:
                error_code = payload.get("error_code") or payload.get("error", {}).get("code") or "BAD_REQUEST_ERROR"
                error_desc = payload.get("error_description") or payload.get("error", {}).get("description") or "Payment failed"

                attempt = PaymentAttempt(
                    id=f"att_{evt.id}",
                    payment_id=payment_id,
                    attempt_sequence=attempt_counter,
                    payment_method_type=PaymentMethodType.CARD,
                    status=PaymentAttemptStatus.FAILED,
                    error_code=error_code,
                    error_description=error_desc,
                    gateway_reference=evt.gateway_event_id,
                    initiated_at=evt.occurred_at,
                    completed_at=evt.occurred_at,
                )
                payment.attempts.append(attempt)
                attempt_counter += 1

        return payment
