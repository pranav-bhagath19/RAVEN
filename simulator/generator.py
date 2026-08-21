"""
RAVEN Synthetic Data Generator

Generates reproducible multi-scenario financial event streams embedded with exact ground truth labels.
Uses seed-controlled randomness for 100% deterministic, offline execution.
"""

from datetime import datetime, timedelta, timezone
import random
from typing import Any
from domain.entities.financial_event import FinancialEvent
from domain.enums import PaymentStatus
from simulator.scenarios import GroundTruthMetadata, ScenarioResult


class SyntheticDataGenerator:
    """
    Deterministic Synthetic Data Generator emitting multi-scenario financial datasets.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self._rng = random.Random(seed)
        self.base_time = datetime(2026, 8, 21, 12, 0, 0, tzinfo=timezone.utc)

    def _make_event_dict(
        self,
        event_id: str,
        event_type: str,
        entity_id: str,
        merchant_id: str,
        amount_minor: int,
        currency: str,
        occurred_at: datetime,
        received_at: datetime | None = None,
        sequence_number: int = 1,
        gateway_event_id: str | None = None,
        customer_id: str | None = None,
        order_id: str | None = None,
        extra_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "event_id": gateway_event_id or f"evt_gw_{event_id}",
            "payment_id": entity_id,
            "order_id": order_id or f"order_{entity_id}",
            "merchant_id": merchant_id,
            "customer_id": customer_id or f"cust_{entity_id}",
            "amount": amount_minor,
            "currency": currency,
        }
        if extra_payload:
            payload.update(extra_payload)

        event_hash = FinancialEvent.compute_canonical_hash(payload)

        return {
            "id": event_id,
            "event_hash": event_hash,
            "event_type": event_type,
            "gateway_event_id": gateway_event_id or payload["event_id"],
            "entity_id": entity_id,
            "order_id": order_id or payload["order_id"],
            "merchant_id": merchant_id,
            "customer_id": customer_id or payload["customer_id"],
            "amount": {"amount_minor": amount_minor, "currency": currency},
            "payload": payload,
            "occurred_at": occurred_at.isoformat(),
            "received_at": (received_at or occurred_at).isoformat(),
            "sequence_number": sequence_number,
        }

    def generate_scenario_1_transient_gateway_timeout(self) -> ScenarioResult:
        payment_id = "pay_scen1_transient_01"
        merchant_id = "mer_scen1"
        amount = 150000  # ₹1,500.00
        occurred = self.base_time

        evt_fail = self._make_event_dict(
            event_id="evt_scen1_fail",
            event_type="payment.failed",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=occurred,
            sequence_number=1,
            extra_payload={
                "error_code": "GATEWAY_TIMED_OUT",
                "error_description": "Issuer bank gateway timed out after 90 seconds",
            },
        )

        return ScenarioResult(
            scenario_id="scenario_1_transient_gateway_timeout",
            scenario_name="Transient Gateway Timeout",
            description="Issuer bank gateway timed out temporarily; recoverable via Smart Retry after downtime resolves.",
            expected_final_state=PaymentStatus.FAILED,
            events=[evt_fail],
            ground_truth=GroundTruthMetadata(
                payment_id=payment_id,
                true_root_cause="GATEWAY_TIMED_OUT",
                is_recoverable=True,
                organic_recovery_will_occur=False,
                optimal_action="SMART_RETRY",
                expected_optimal_delay_seconds=900,
            ),
        )

    def generate_scenario_2_hard_card_decline(self) -> ScenarioResult:
        payment_id = "pay_scen2_hard_decline_01"
        merchant_id = "mer_scen2"
        amount = 499900  # ₹4,999.00
        occurred = self.base_time + timedelta(minutes=5)

        evt_fail = self._make_event_dict(
            event_id="evt_scen2_fail",
            event_type="payment.failed",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=occurred,
            sequence_number=1,
            extra_payload={
                "error_code": "BAD_REQUEST_PAYMENT_DECLINED_INSUFFICIENT_FUNDS",
                "error_description": "Card issuer declined payment due to insufficient funds",
            },
        )

        return ScenarioResult(
            scenario_id="scenario_2_hard_card_decline",
            scenario_name="Hard Card Decline (Insufficient Funds)",
            description="Issuer declined card payment for insufficient funds; retries will fail. Optimal action: Payment link dispatch.",
            expected_final_state=PaymentStatus.FAILED,
            events=[evt_fail],
            ground_truth=GroundTruthMetadata(
                payment_id=payment_id,
                true_root_cause="BAD_REQUEST_PAYMENT_DECLINED_INSUFFICIENT_FUNDS",
                is_recoverable=True,
                organic_recovery_will_occur=False,
                optimal_action="PAYMENT_LINK_DISPATCH",
                expected_optimal_delay_seconds=0,
            ),
        )

    def generate_scenario_3_late_capture_webhook(self) -> ScenarioResult:
        payment_id = "pay_scen3_late_cap_01"
        merchant_id = "mer_scen3"
        amount = 250000  # ₹2,500.00
        t0 = self.base_time + timedelta(minutes=10)

        evt_fail = self._make_event_dict(
            event_id="evt_scen3_fail",
            event_type="payment.failed",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=t0,
            received_at=t0,
            sequence_number=1,
            extra_payload={
                "error_code": "PAYMENT_TIMED_OUT_LATE_AUTHORIZATION",
                "error_description": "Gateway timed out, but late authorization occurred at bank",
            },
        )

        evt_late_cap = self._make_event_dict(
            event_id="evt_scen3_cap",
            event_type="payment.captured",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=t0 + timedelta(seconds=45),
            received_at=t0 + timedelta(seconds=120),  # Arrived delayed at T+120s
            sequence_number=2,
        )

        return ScenarioResult(
            scenario_id="scenario_3_late_capture_webhook",
            scenario_name="Late Authorization Webhook",
            description="Gateway initially reported timeout, but bank late-captured funds. Delayed webhook confirms capture.",
            expected_final_state=PaymentStatus.CAPTURED,
            events=[evt_fail, evt_late_cap],
            ground_truth=GroundTruthMetadata(
                payment_id=payment_id,
                true_root_cause="PAYMENT_TIMED_OUT_LATE_AUTHORIZATION",
                is_recoverable=True,
                organic_recovery_will_occur=True,
                optimal_action="NO_ACTION_REQUIRED",
                expected_optimal_delay_seconds=0,
            ),
        )

    def generate_scenario_4_abandoned_checkout(self) -> ScenarioResult:
        payment_id = "pay_scen4_abandoned_01"
        merchant_id = "mer_scen4"
        amount = 99900  # ₹999.00
        t0 = self.base_time + timedelta(minutes=15)

        evt_pending = self._make_event_dict(
            event_id="evt_scen4_pending",
            event_type="payment.ambiguous",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=t0,
            sequence_number=1,
            extra_payload={
                "status": "ambiguous",
                "error_code": "AUTHENTICATION_ABANDONED",
                "error_description": "Customer abandoned checkout at 3DS OTP screen",
            },
        )

        return ScenarioResult(
            scenario_id="scenario_4_abandoned_checkout",
            scenario_name="Abandoned Checkout Intent",
            description="User abandoned 3DS OTP checkout screen without success or explicit failure webhook.",
            expected_final_state=PaymentStatus.AMBIGUOUS,
            events=[evt_pending],
            ground_truth=GroundTruthMetadata(
                payment_id=payment_id,
                true_root_cause="AUTHENTICATION_ABANDONED",
                is_recoverable=True,
                organic_recovery_will_occur=False,
                optimal_action="FALLBACK_CHANNEL_NOTIFY",
                expected_optimal_delay_seconds=1800,
            ),
        )

    def generate_scenario_5_subscription_dunning(self) -> ScenarioResult:
        payment_id = "pay_scen5_dunning_01"
        merchant_id = "mer_scen5"
        amount = 149900  # ₹1,499.00
        t0 = self.base_time + timedelta(minutes=20)

        evt_fail = self._make_event_dict(
            event_id="evt_scen5_fail",
            event_type="payment.failed",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=t0,
            sequence_number=1,
            extra_payload={
                "subscription_id": "sub_01H_dunning",
                "error_code": "RECURRING_TOKEN_EXPIRED",
                "error_description": "Monthly recurring auto-debit token expired",
            },
        )

        return ScenarioResult(
            scenario_id="scenario_5_subscription_dunning",
            scenario_name="Subscription Dunning Failure",
            description="Monthly subscription auto-debit failed due to expired recurring card token.",
            expected_final_state=PaymentStatus.FAILED,
            events=[evt_fail],
            ground_truth=GroundTruthMetadata(
                payment_id=payment_id,
                true_root_cause="RECURRING_TOKEN_EXPIRED",
                is_recoverable=True,
                organic_recovery_will_occur=False,
                optimal_action="PAYMENT_LINK_DISPATCH",
                expected_optimal_delay_seconds=0,
            ),
        )

    def generate_scenario_6_ambiguous_pending_state(self) -> ScenarioResult:
        payment_id = "pay_scen6_ambiguous_01"
        merchant_id = "mer_scen6"
        amount = 350000  # ₹3,500.00
        t0 = self.base_time + timedelta(minutes=25)

        evt_ambiguous = self._make_event_dict(
            event_id="evt_scen6_ambig",
            event_type="payment.pending",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=t0,
            sequence_number=1,
            extra_payload={
                "status": "pending",
                "error_code": "GATEWAY_STATE_AMBIGUOUS",
                "error_description": "Bank gateway returned HTTP 500 during status query",
            },
        )

        return ScenarioResult(
            scenario_id="scenario_6_ambiguous_pending_state",
            scenario_name="Ambiguous Payment State",
            description="Gateway state query returned HTTP 500; status ambiguous. Requires state verification before side-effects.",
            expected_final_state=PaymentStatus.AMBIGUOUS,
            events=[evt_ambiguous],
            ground_truth=GroundTruthMetadata(
                payment_id=payment_id,
                true_root_cause="GATEWAY_STATE_AMBIGUOUS",
                is_recoverable=True,
                organic_recovery_will_occur=False,
                optimal_action="ESCALATE_TO_HUMAN",
                expected_optimal_delay_seconds=0,
            ),
        )

    def generate_scenario_7_duplicate_webhook_delivery(self) -> ScenarioResult:
        payment_id = "pay_scen7_dup_01"
        merchant_id = "mer_scen7"
        amount = 75000  # ₹750.00
        t0 = self.base_time + timedelta(minutes=30)
        gateway_id = "gw_evt_dup_999"

        # Three identical webhook deliveries with same payload & gateway_event_id
        evt_1 = self._make_event_dict(
            event_id="evt_scen7_dup1",
            event_type="payment.captured",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=t0,
            received_at=t0,
            sequence_number=1,
            gateway_event_id=gateway_id,
        )
        evt_2 = self._make_event_dict(
            event_id="evt_scen7_dup2",
            event_type="payment.captured",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=t0,
            received_at=t0 + timedelta(seconds=2),
            sequence_number=1,
            gateway_event_id=gateway_id,
        )
        evt_3 = self._make_event_dict(
            event_id="evt_scen7_dup3",
            event_type="payment.captured",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=t0,
            received_at=t0 + timedelta(seconds=5),
            sequence_number=1,
            gateway_event_id=gateway_id,
        )

        return ScenarioResult(
            scenario_id="scenario_7_duplicate_webhook_delivery",
            scenario_name="Duplicate Webhook Delivery",
            description="Gateway delivered identical payment.captured webhook 3 times. Deduplication engine ingests only 1 event.",
            expected_final_state=PaymentStatus.CAPTURED,
            events=[evt_1, evt_2, evt_3],
            ground_truth=GroundTruthMetadata(
                payment_id=payment_id,
                true_root_cause="DUPLICATE_WEBHOOK_DELIVERY",
                is_recoverable=True,
                organic_recovery_will_occur=True,
                optimal_action="NO_ACTION_REQUIRED",
                expected_optimal_delay_seconds=0,
            ),
        )

    def generate_scenario_8_out_of_order_webhook_delivery(self) -> ScenarioResult:
        payment_id = "pay_scen8_ooo_01"
        merchant_id = "mer_scen8"
        amount = 120000  # ₹1,200.00
        t0 = self.base_time + timedelta(minutes=35)

        # Captured event occurred at T+2s, but received at T+1s
        evt_captured_first = self._make_event_dict(
            event_id="evt_scen8_cap",
            event_type="payment.captured",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=t0 + timedelta(seconds=2),
            received_at=t0 + timedelta(seconds=1),
            sequence_number=2,
        )

        # Authorized event occurred at T+1s, but received delayed at T+5s
        evt_authorized_second = self._make_event_dict(
            event_id="evt_scen8_auth",
            event_type="payment.authorized",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=t0 + timedelta(seconds=1),
            received_at=t0 + timedelta(seconds=5),
            sequence_number=1,
        )

        return ScenarioResult(
            scenario_id="scenario_8_out_of_order_webhook_delivery",
            scenario_name="Out-of-Order Webhook Delivery",
            description="Webhook arrival order differs from occurrence order. StateReconstructor reorders and resolves state to CAPTURED.",
            expected_final_state=PaymentStatus.CAPTURED,
            events=[evt_captured_first, evt_authorized_second],
            ground_truth=GroundTruthMetadata(
                payment_id=payment_id,
                true_root_cause="OUT_OF_ORDER_DELIVERY",
                is_recoverable=True,
                organic_recovery_will_occur=True,
                optimal_action="NO_ACTION_REQUIRED",
                expected_optimal_delay_seconds=0,
            ),
        )

    def generate_scenario_9_organic_customer_recovery(self) -> ScenarioResult:
        payment_id = "pay_scen9_organic_01"
        merchant_id = "mer_scen9"
        amount = 89900  # ₹899.00
        t0 = self.base_time + timedelta(minutes=40)

        evt_fail = self._make_event_dict(
            event_id="evt_scen9_fail",
            event_type="payment.failed",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=t0,
            sequence_number=1,
            extra_payload={
                "error_code": "BAD_REQUEST_PAYMENT_DECLINED",
                "error_description": "Initial payment attempt declined",
            },
        )

        evt_organic_cap = self._make_event_dict(
            event_id="evt_scen9_cap",
            event_type="payment.captured",
            entity_id=payment_id,
            merchant_id=merchant_id,
            amount_minor=amount,
            currency="INR",
            occurred_at=t0 + timedelta(seconds=180),
            sequence_number=2,
            extra_payload={"recovery_channel": "ORGANIC_MANUAL_RETRY"},
        )

        return ScenarioResult(
            scenario_id="scenario_9_organic_customer_recovery",
            scenario_name="Organic Customer Recovery",
            description="Customer manually retried and completed payment independently. Attribution engine must not claim recovery.",
            expected_final_state=PaymentStatus.CAPTURED,
            events=[evt_fail, evt_organic_cap],
            ground_truth=GroundTruthMetadata(
                payment_id=payment_id,
                true_root_cause="ORGANIC_CUSTOMER_RETRY",
                is_recoverable=True,
                organic_recovery_will_occur=True,
                optimal_action="NO_ACTION_REQUIRED",
                expected_optimal_delay_seconds=0,
            ),
        )

    def generate_all_scenarios(self) -> list[ScenarioResult]:
        """
        Generates all 9 standard scenario results in deterministic order.
        """
        return [
            self.generate_scenario_1_transient_gateway_timeout(),
            self.generate_scenario_2_hard_card_decline(),
            self.generate_scenario_3_late_capture_webhook(),
            self.generate_scenario_4_abandoned_checkout(),
            self.generate_scenario_5_subscription_dunning(),
            self.generate_scenario_6_ambiguous_pending_state(),
            self.generate_scenario_7_duplicate_webhook_delivery(),
            self.generate_scenario_8_out_of_order_webhook_delivery(),
            self.generate_scenario_9_organic_customer_recovery(),
        ]

    def build_dataset_dict(self) -> dict[str, Any]:
        """
        Builds the complete dataset dictionary ready for JSON serialization.
        """
        scenarios = self.generate_all_scenarios()
        scenarios_data = [s.model_dump() for s in scenarios]

        ground_truth_map = {
            s.ground_truth.payment_id: s.ground_truth.model_dump()
            for s in scenarios
        }

        return {
            "dataset_metadata": {
                "version": "1.0",
                "seed": self.seed,
                "total_scenarios": len(scenarios),
                "generated_at": self.base_time.isoformat(),
            },
            "scenarios": scenarios_data,
            "ground_truth": ground_truth_map,
        }
