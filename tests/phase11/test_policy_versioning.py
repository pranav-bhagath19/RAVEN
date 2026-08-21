"""
Phase 11 Policy Versioning Tests

Verifies immutable version creation, version increments, and historical version immutability.
"""

import uuid
from persistence.database import Base, engine, SessionLocal
from persistence.repositories.policies import MerchantPolicyRepository
from domain.entities.merchant_policy import PolicyVersionStatus

Base.metadata.create_all(bind=engine)


def test_policy_versioning_lifecycle():
    db = SessionLocal()
    try:
        repo = MerchantPolicyRepository(db)
        tenant_id = f"tenant_ver_{uuid.uuid4().hex[:6]}"

        # 1. Create draft v1
        v1 = repo.create_draft_version(tenant_id, "pol_001", {"maximum_retry_attempts": 2})
        assert v1.version == 1
        assert v1.status == PolicyVersionStatus.DRAFT

        # 2. Activate v1
        act_v1 = repo.activate_version(tenant_id, 1)
        assert act_v1.status == PolicyVersionStatus.ACTIVE

        # 3. Create draft v2
        v2 = repo.create_draft_version(tenant_id, "pol_001", {"maximum_retry_attempts": 4})
        assert v2.version == 2
        assert v2.status == PolicyVersionStatus.DRAFT

        # 4. Activate v2
        act_v2 = repo.activate_version(tenant_id, 2)
        assert act_v2.status == PolicyVersionStatus.ACTIVE

        # Historical v1 should now be SUPERSEDED and immutable
        hist_v1 = repo.get_policy_version(tenant_id, 1)
        assert hist_v1 is not None
        assert hist_v1.status == PolicyVersionStatus.SUPERSEDED
        assert hist_v1.configuration_json == {"maximum_retry_attempts": 2}
    finally:
        db.close()
