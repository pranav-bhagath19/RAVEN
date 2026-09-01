# RAVEN Phase 14 — Multi-Region Reliability & Distributed Policy Synchronization

## 1. Overview

RAVEN Phase 14 introduces **Multi-Region Operational Reliability and Distributed Policy Synchronization**. It enables RAVEN to operate seamlessly across geographically distributed regions while maintaining strict deterministic policy enforcement, tenant isolation, canonical SHA-256 policy hash verification, immutable version lineage, distributed idempotency, and fail-closed security.

---

## 2. Non-Negotiable Security Invariants

1. **PolicyEngine Absolute Veto**: `PolicyEngine` remains the sole deterministic veto authority across all regions. No replication worker, cache, or failover mechanism may bypass `PolicyEngine` rules (`POL_001`–`POL_007`).
2. **ToolExecutor Boundary**: `ToolExecutor` is the sole consequential tool execution boundary. Every execution requires a valid HMAC-SHA256 `PolicyApprovalToken`. Regional infrastructure cannot execute tools or mint tokens.
3. **Fail-Closed Security**: Any ambiguous, unverified, corrupted, or stale policy state triggers immediate `FAIL_CLOSED` behavior (0 tokens issued, 0 tool executions).
4. **Tenant Isolation**: Replication states, checkpoints, and conflict records are strictly isolated by `tenant_id`. Cross-tenant reading or synchronization is strictly prohibited.
5. **Immutable Policy History**: Replicated policy updates create append-only version nodes without mutating prior history.
6. **Canonical SHA-256 Hash Integrity**: Every policy configuration payload must match its canonical SHA-256 hash. Hash mismatches result in immediate rejection.
7. **Integer Minor Units**: All monetary values remain integer minor units (paise).

---

## 3. Architecture & Region Model

```
                    Global / Regional API
                            │
                            ↓
                     TenantContext
                            │
             ┌──────────────┴──────────────┐
             ↓                             ↓
        Region A                       Region B
             │                             │
       PostgreSQL                       PostgreSQL
             │                             │
          Redis                          Redis
             │                             │
             └──────────────┬──────────────┘
                            ↓
                  Policy Synchronization
                            ↓
                 Policy Version Validation
                            ↓
                  SHA-256 Hash Validation
                            ↓
                 Replication State Tracking
                            ↓
                    PolicyEngine
                            ↓
              HMAC PolicyApprovalToken
                            ↓
                      ToolExecutor
                            ↓
                     Verification
                            ↓
                    DecisionTrace
```

### Region Domain Model
- `region_id`: Unique region identifier (e.g. `ap-south-1`, `us-east-1`, `eu-west-1`).
- `status`: `ACTIVE`, `DEGRADED`, `OFFLINE`, `RECOVERING`.
- `is_primary`: Flag indicating primary coordinator region.
- `health_score`: Real-time health score from `0.0` to `1.0`.

---

## 4. Policy Replication & Integrity Subsystem

- `compute_policy_hash`: Calculates canonical SHA-256 hash over sorted JSON keys of policy configuration.
- `PolicyReplicator`: Idempotently replicates policy versions across regions, verifying hashes and recording checkpoints.
- `PolicyConflictDetector`: Detects hash mismatches on identical version strings or divergent lineage branches.
- `PolicyReconciler`: Resolves conflicts using version lineage trees; fails closed on unverified lineage.
- `RegionalFailoverManager`: Manages health, stale policy read protection (max sync age 300s), and safe regional failover.

---

## 5. Operations REST API Endpoints

- `GET /api/v1/operations/regions`: List registered regions.
- `GET /api/v1/operations/regions/{region_id}`: Retrieve region details.
- `GET /api/v1/operations/regions/{region_id}/health`: Retrieve real-time health.
- `POST /api/v1/operations/regions/{region_id}/status`: Update region status/health.
- `GET /api/v1/operations/replication/status`: Multi-region sync health summary.
- `GET /api/v1/operations/replication/checkpoints`: List tenant replication checkpoints.
- `GET /api/v1/operations/policies/{policy_id}/replication`: List policy replication history.
- `GET /api/v1/operations/policies/{policy_id}/conflicts`: List policy conflicts.
- `POST /api/v1/operations/policies/{policy_id}/reconcile`: Execute deterministic conflict reconciliation.

---

## 6. Verification & Quality Gates

- `tests/phase14/`: 8 dedicated security, tenant isolation, hash integrity, conflict safety, failover chaos, idempotency, boundary, and API tests.
- `scripts/phase14_demo.py`: Interactive 22-step lifecycle demonstration script exiting with Code `0`.
