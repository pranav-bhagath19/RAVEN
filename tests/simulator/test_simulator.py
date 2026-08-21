"""
Behavioral and Unit Tests for RAVEN Synthetic Data Simulator

Validates seed determinism, 9 scenario definitions, ground truth metadata integrity,
event schema compatibility, state reconstruction accuracy, deduplication engine matching,
arrival-order independence, and export determinism.
"""

from datetime import datetime
from pathlib import Path
from domain.entities.financial_event import FinancialEvent
from domain.enums import PaymentStatus
from domain.state.reconstructor import StateReconstructor
from domain.values.money import Money
from events.ingestion import EventDeduplicationEngine, EventIngestionService
from simulator.exporter import export_dataset
from simulator.generator import SyntheticDataGenerator


def test_1_seed_determinism():
    gen1 = SyntheticDataGenerator(seed=42)
    gen2 = SyntheticDataGenerator(seed=42)

    ds1 = gen1.build_dataset_dict()
    ds2 = gen2.build_dataset_dict()

    assert ds1 == ds2


def test_2_different_seed():
    gen1 = SyntheticDataGenerator(seed=42)
    gen2 = SyntheticDataGenerator(seed=99)

    assert gen1.seed == 42
    assert gen2.seed == 99


def test_3_nine_scenarios_exist():
    gen = SyntheticDataGenerator(seed=42)
    scenarios = gen.generate_all_scenarios()

    assert len(scenarios) == 9

    expected_scenario_ids = [
        "scenario_1_transient_gateway_timeout",
        "scenario_2_hard_card_decline",
        "scenario_3_late_capture_webhook",
        "scenario_4_abandoned_checkout",
        "scenario_5_subscription_dunning",
        "scenario_6_ambiguous_pending_state",
        "scenario_7_duplicate_webhook_delivery",
        "scenario_8_out_of_order_webhook_delivery",
        "scenario_9_organic_customer_recovery",
    ]

    actual_scenario_ids = [s.scenario_id for s in scenarios]
    assert actual_scenario_ids == expected_scenario_ids


def test_4_event_schema_and_domain_invariants():
    gen = SyntheticDataGenerator(seed=42)
    scenarios = gen.generate_all_scenarios()

    for scen in scenarios:
        for evt_dict in scen.events:
            event = FinancialEvent(
                id=evt_dict["id"],
                event_hash=evt_dict["event_hash"],
                event_type=evt_dict["event_type"],
                gateway_event_id=evt_dict["gateway_event_id"],
                entity_id=evt_dict["entity_id"],
                order_id=evt_dict["order_id"],
                merchant_id=evt_dict["merchant_id"],
                customer_id=evt_dict["customer_id"],
                amount=Money(
                    amount_minor=evt_dict["amount"]["amount_minor"],
                    currency=evt_dict["amount"]["currency"],
                ),
                payload=evt_dict["payload"],
                occurred_at=datetime.fromisoformat(evt_dict["occurred_at"]),
                received_at=datetime.fromisoformat(evt_dict["received_at"]),
                sequence_number=evt_dict["sequence_number"],
            )

            computed_hash = FinancialEvent.compute_canonical_hash(evt_dict["payload"])
            assert event.event_hash == computed_hash
            assert event.amount.currency == "INR"


def test_5_ingestion_compatibility():
    gen = SyntheticDataGenerator(seed=42)
    scen1 = gen.generate_scenario_1_transient_gateway_timeout()

    ingestion_service = EventIngestionService()
    evt_dict = scen1.events[0]

    financial_evt = ingestion_service.ingest_event(
        raw_payload=evt_dict["payload"],
        event_type=evt_dict["event_type"],
        gateway_event_id=evt_dict["gateway_event_id"],
        occurred_at=datetime.fromisoformat(evt_dict["occurred_at"]),
        sequence_number=evt_dict["sequence_number"],
    )

    assert len(ingestion_service.ingested_events) == 1
    assert financial_evt.entity_id == "pay_scen1_transient_01"


def test_6_state_reconstruction_for_all_scenarios():
    gen = SyntheticDataGenerator(seed=42)
    scenarios = gen.generate_all_scenarios()

    for scen in scenarios:
        events = []
        for evt_dict in scen.events:
            events.append(
                FinancialEvent(
                    id=evt_dict["id"],
                    event_hash=evt_dict["event_hash"],
                    event_type=evt_dict["event_type"],
                    gateway_event_id=evt_dict["gateway_event_id"],
                    entity_id=evt_dict["entity_id"],
                    order_id=evt_dict["order_id"],
                    merchant_id=evt_dict["merchant_id"],
                    customer_id=evt_dict["customer_id"],
                    amount=Money(
                        amount_minor=evt_dict["amount"]["amount_minor"],
                        currency=evt_dict["amount"]["currency"],
                    ),
                    payload=evt_dict["payload"],
                    occurred_at=datetime.fromisoformat(evt_dict["occurred_at"]),
                    received_at=datetime.fromisoformat(evt_dict["received_at"]),
                    sequence_number=evt_dict["sequence_number"],
                )
            )

        payment_id = scen.ground_truth.payment_id
        reconstructed = StateReconstructor.reconstruct_payment_state(payment_id, events)

        assert reconstructed.status == scen.expected_final_state


def test_7_duplicate_webhook_detection():
    gen = SyntheticDataGenerator(seed=42)
    scen7 = gen.generate_scenario_7_duplicate_webhook_delivery()

    dedup = EventDeduplicationEngine()
    first_evt = scen7.events[0]
    second_evt = scen7.events[1]

    # First event is not a duplicate
    assert not dedup.is_duplicate(first_evt["event_hash"], first_evt["gateway_event_id"])
    dedup.register(first_evt["event_hash"], first_evt["gateway_event_id"])

    # Second identical event is detected as duplicate
    assert dedup.is_duplicate(second_evt["event_hash"], second_evt["gateway_event_id"])


def test_8_arrival_order_independence():
    gen = SyntheticDataGenerator(seed=42)
    scen8 = gen.generate_scenario_8_out_of_order_webhook_delivery()

    # Create FinancialEvent objects
    events = [
        FinancialEvent(
            id=e["id"],
            event_hash=e["event_hash"],
            event_type=e["event_type"],
            gateway_event_id=e["gateway_event_id"],
            entity_id=e["entity_id"],
            merchant_id=e["merchant_id"],
            amount=Money(amount_minor=e["amount"]["amount_minor"], currency=e["amount"]["currency"]),
            payload=e["payload"],
            occurred_at=datetime.fromisoformat(e["occurred_at"]),
            received_at=datetime.fromisoformat(e["received_at"]),
            sequence_number=e["sequence_number"],
        )
        for e in scen8.events
    ]

    payment_id = scen8.ground_truth.payment_id

    # Passed in arrival order (captured first, authorized second)
    reconstructed_arrival_order = StateReconstructor.reconstruct_payment_state(payment_id, events)

    # Passed in reversed order
    reconstructed_reversed_order = StateReconstructor.reconstruct_payment_state(payment_id, list(reversed(events)))

    assert reconstructed_arrival_order.status == PaymentStatus.CAPTURED
    assert reconstructed_reversed_order.status == PaymentStatus.CAPTURED


def test_9_ground_truth_integrity():
    gen = SyntheticDataGenerator(seed=42)
    scenarios = gen.generate_all_scenarios()

    for scen in scenarios:
        gt = scen.ground_truth
        assert len(gt.payment_id) > 0
        assert len(gt.true_root_cause) > 0
        assert isinstance(gt.is_recoverable, bool)
        assert isinstance(gt.organic_recovery_will_occur, bool)
        assert len(gt.optimal_action) > 0
        assert gt.expected_optimal_delay_seconds >= 0


def test_10_export_determinism(tmp_path: Path):
    gen = SyntheticDataGenerator(seed=42)
    dataset_dict = gen.build_dataset_dict()

    path1 = tmp_path / "dataset_export_1.json"
    path2 = tmp_path / "dataset_export_2.json"

    export_dataset(dataset_dict, path1)
    export_dataset(dataset_dict, path2)

    content1 = path1.read_bytes()
    content2 = path2.read_bytes()

    assert content1 == content2
