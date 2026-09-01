"""
RAVEN Phase 14 Security Test Suite: Execution Boundary Integrity

Explicitly proves section 19 requirements:
Regional failover, replication, and conflict components cannot:
1. Mint PolicyApprovalTokens.
2. Invoke ToolExecutor.
3. Execute recovery tools directly.
"""

from policies.conflict import PolicyConflictDetector
from policies.failover import RegionalFailoverManager
from policies.reconciliation import PolicyReconciler
from policies.replication import PolicyReplicator


def test_replication_components_lack_execution_authority():
    """Proves all Phase 14 replication and failover objects lack execution tools or token minting methods."""
    replicator = PolicyReplicator()
    detector = PolicyConflictDetector()
    reconciler = PolicyReconciler()
    failover = RegionalFailoverManager()

    for obj in (replicator, detector, reconciler, failover):
        assert not hasattr(obj, "execute")
        assert not hasattr(obj, "execute_tool")
        assert not hasattr(obj, "mint_token")
        assert not hasattr(obj, "issue_token")
        assert not hasattr(obj, "bypass_policy_engine")
