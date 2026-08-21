"""
Tests for Phase 9 Distributed Idempotency & Lock Coordination
"""

from persistence.redis_store import LocalIdempotencyStore, RedisIdempotencyStore


def test_local_idempotency_store_claim_release():
    store = LocalIdempotencyStore()

    assert store.claim("key_test_1", ttl_seconds=300) is True
    assert store.claim("key_test_1", ttl_seconds=300) is False
    assert store.exists("key_test_1") is True

    store.release("key_test_1")
    assert store.exists("key_test_1") is False
    assert store.claim("key_test_1", ttl_seconds=300) is True


def test_local_idempotency_store_completion():
    store = LocalIdempotencyStore()

    store.claim("key_comp_1")
    store.mark_completed("key_comp_1", value={"result": "SUCCESS"})

    assert store.get_completed_value("key_comp_1") == {"result": "SUCCESS"}


def test_redis_idempotency_store_fallback():
    # Tests that RedisIdempotencyStore operates seamlessly even without a Redis server
    store = RedisIdempotencyStore(redis_url="redis://localhost:6379/15")

    claimed = store.claim("redis_key_1", ttl_seconds=60)
    assert claimed is True

    assert store.claim("redis_key_1", ttl_seconds=60) is False
    store.mark_completed("redis_key_1", value="OK")
    assert store.get_completed_value("redis_key_1") == "OK"
