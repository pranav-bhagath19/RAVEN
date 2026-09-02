"""
Unit Tests for Firestore-Backed Idempotency & Locking Store
"""

import uuid
import pytest
from persistence.firebase import reset_firestore_emulator
from persistence.redis_store import RedisIdempotencyStore


@pytest.fixture(autouse=True)
def setup_firestore():
    reset_firestore_emulator()


def test_firestore_idempotency_store_locking():
    store = RedisIdempotencyStore()
    unique_id = uuid.uuid4().hex[:8]
    key = f"tenant_test:global:event_key_{unique_id}"

    # 1. Claim lock
    claimed = store.claim(key, ttl_seconds=300)
    assert claimed is True

    # 2. Duplicate claim should fail
    claimed_again = store.claim(key, ttl_seconds=300)
    assert claimed_again is False

    # 3. Exists check
    assert store.exists(key) is True

    # 4. Mark completed with payload
    store.mark_completed(key, value={"status": "RECOVERED", "recovered_minor": 50000})

    # 5. Retrieve completed value
    val = store.get_completed_value(key)
    assert val == {"status": "RECOVERED", "recovered_minor": 50000}


def test_firestore_regional_idempotency_key_scoping():
    tenant_id = "tenant_global_corp"
    unique_tx = f"tx_{uuid.uuid4().hex[:8]}"
    key_a = RedisIdempotencyStore.make_regional_key(tenant_id, unique_tx, "ap-south-1")
    key_b = RedisIdempotencyStore.make_regional_key(tenant_id, unique_tx, "us-east-1")

    assert key_a != key_b
    assert "ap-south-1" in key_a
    assert "us-east-1" in key_b

    store = RedisIdempotencyStore()
    assert store.claim(key_a) is True
    assert store.claim(key_b) is True
