"""
RAVEN Live Firebase Cloud Firestore Initial Seeding Script

Populates live GCP Firebase Cloud Firestore project `raven--ai` with initial system records across key collections: `tenants`, `users`, `user_api_keys`, `merchant_policies`, `model_registry`, and `idempotency`.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from persistence.firebase import get_firestore_client


def seed_live_firebase() -> None:
    print("==========================================================================")
    print("      RAVEN INITIAL LIVE FIREBASE CLOUD FIRESTORE SEEDING                ")
    print("==========================================================================")

    db = get_firestore_client()

    # 1. Tenants Collection
    print("Seeding 'tenants' collection...")
    db.collection("tenants").document("tenant_raven_default").set({
        "tenant_id": "tenant_raven_default",
        "merchant_id": "merchant_raven_001",
        "name": "RAVEN Enterprise Default Merchant",
        "status": "ACTIVE",
        "created_at": "2026-09-01T00:00:00Z",
        "updated_at": "2026-09-01T00:00:00Z"
    })

    # 2. Users Collection
    print("Seeding 'users' collection...")
    db.collection("users").document("user_admin_001").set({
        "user_id": "user_admin_001",
        "tenant_id": "tenant_raven_default",
        "email": "admin@raven-recovery.ai",
        "role": "POLICY_ADMIN",
        "is_active": True,
        "created_at": "2026-09-01T00:00:00Z"
    })

    # 3. User API Keys Collection
    print("Seeding 'user_api_keys' collection...")
    db.collection("user_api_keys").document("key_raven_admin_live").set({
        "key_id": "key_raven_admin_live",
        "user_id": "user_admin_001",
        "tenant_id": "tenant_raven_default",
        "name": "Production Control Key",
        "key_prefix": "rvn_live",
        "key_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "role": "POLICY_ADMIN",
        "revoked": False,
        "created_at": "2026-09-01T00:00:00Z"
    })

    # 4. Merchant Policies Collection
    print("Seeding 'merchant_policies' collection...")
    db.collection("merchant_policies").document("tenant_raven_default_v1").set({
        "policy_id": "pol_default_v1",
        "tenant_id": "tenant_raven_default",
        "version": 1,
        "status": "ACTIVE",
        "configuration_json": {
            "max_retry_attempts": 3,
            "min_recovery_amount_minor": 10000,
            "blocked_error_codes": ["CARD_EXPIRED", "ACCOUNT_CLOSED"],
            "allow_discount_incentive": True,
            "max_discount_percentage": 10
        },
        "configuration_hash": "hash_pol_v1_default",
        "created_by": "user_admin_001",
        "created_at": "2026-09-01T00:00:00Z",
        "activated_at": "2026-09-01T00:00:00Z"
    })

    # 5. Model Registry Collection
    print("Seeding 'model_registry' collection...")
    db.collection("model_registry").document("v1.0").set({
        "model_version": "v1.0",
        "model_type": "LogisticRegressionPropensityScorer",
        "feature_schema_version": "v1",
        "training_dataset_hash": "ds_hash_2026_09",
        "artifact_hash": "art_hash_v1_0",
        "status": "CHAMPION",
        "metrics_json": {
            "accuracy": 0.942,
            "precision": 0.931,
            "recall": 0.955,
            "f1_score": 0.943,
            "auc_roc": 0.978
        },
        "created_at": "2026-09-01T00:00:00Z"
    })

    # 6. Sample Initial Payment & Decision Trace
    print("Seeding sample initial records...")
    db.collection("payments").document("pay_initial_001").set({
        "payment_id": "pay_initial_001",
        "tenant_id": "tenant_raven_default",
        "order_id": "order_initial_001",
        "merchant_id": "merchant_raven_001",
        "customer_id": "cust_initial_001",
        "amount_minor": 499900,
        "currency": "INR",
        "status": "RECOVERED",
        "attempts_count": 1,
        "error_code": "INSUFFICIENT_FUNDS",
        "error_description": "Insufficient funds in customer account",
        "created_at": "2026-09-01T12:00:00Z",
        "updated_at": "2026-09-01T12:05:00Z"
    })

    db.collection("decision_traces").document("trace_initial_001").set({
        "decision_id": "trace_initial_001",
        "tenant_id": "tenant_raven_default",
        "policy_id": "pol_default_v1",
        "policy_version": 1,
        "opportunity_id": "opp_initial_001",
        "merchant_id": "merchant_raven_001",
        "customer_id": "cust_initial_001",
        "payment_id": "pay_initial_001",
        "status": "EXECUTED",
        "root_cause": "INSUFFICIENT_FUNDS",
        "selected_action_type": "SMART_RETRY",
        "policy_decision": "APPROVED",
        "policy_token_id": "tok_initial_001",
        "created_at": "2026-09-01T12:01:00Z"
    })

    print("==========================================================================")
    print("      SUCCESS: LIVE FIREBASE CLOUD FIRESTORE SEEDING COMPLETE!           ")
    print("==========================================================================")


if __name__ == "__main__":
    seed_live_firebase()
