# RAVEN Phase 11 — Multi-Tenant Merchant Intelligence & Dynamic Policy Configuration

## 1. Overview

Phase 11 upgrades RAVEN into a production-grade **Multi-Tenant Merchant Recovery Platform**. It introduces strict tenant isolation across persistence, API gateways, and decision trace lineage while providing dynamic, versioned merchant policy configurations, dry-run policy simulation, transactional activation, lineage-preserving rollback, comprehensive audit logging, merchant intelligence analytics, and fine-grained RBAC.

All non-negotiable security invariants are strictly preserved:
- **ML Propensity Scoring remains 100% Advisory-Only.**
- **`PolicyEngine` remains the non-bypassable absolute veto authority (`POL_001`–`POL_007`).**
- **`ToolExecutor` remains the sole side-effect execution boundary requiring an HMAC-SHA256 `PolicyApprovalToken`.**
- **All monetary calculations remain integer minor units (paise). Zero floating-point monetary operations.**

---

## 2. Multi-Tenant Architecture

```
Tenant API Key / Bearer Authentication
        ↓
TenantContext Resolution (tenant_id, merchant_id, permissions)
        ↓
Razorpay Webhook / Ingestion Boundary (Safe Tenant Mapping)
        ↓
State Reconstruction Engine (Tenant-Scoped Queries)
        ↓
Root Cause Analyst & Recovery Planner
        ↓
Advisory ML Propensity Scoring Layer
        ↓
Deterministic Integer Expected Value Calculation (paise)
        ↓
Dynamic Merchant Policy Engine (Tenant-Active Policy Version & Veto Authority)
        ↓
HMAC-SHA256 Policy Approval Token Issuance
        ↓
Token-Verifying ToolExecutor (Tenant Idempotency Store)
        ↓
DecisionTrace Lineage Snapshot (tenant_id, policy_id, policy_version, policy_hash)
```

---

## 3. Key Components & Data Model

### 3.1 Tenant & Merchant Domain Model (`domain/entities/tenant.py`)
- `Tenant`: Organization wrapper containing `tenant_id`, `merchant_id`, `name`, `status` (`ACTIVE`, `SUSPENDED`, `DISABLED`), `created_at`, `updated_at`.
- Every merchant belongs to exactly one tenant.

### 3.2 Merchant Policy & Versioning (`domain/entities/merchant_policy.py`)
- `MerchantPolicyVersion`: Immutable policy configuration record with `policy_id`, `tenant_id`, `version`, `status` (`DRAFT`, `ACTIVE`, `SUPERSEDED`, `ROLLED_BACK`), `configuration_json`, `configuration_hash` (canonical SHA-256), `created_by`, `created_at`, `activated_at`, `deactivated_at`, `parent_version`, `rollback_source_version`.
- **Historical Policy Versions are STRICTLY IMMUTABLE.**

### 3.3 Database Tenancy (`persistence/models.py`)
- All persistent tables (`payments`, `financial_events`, `webhook_ingestions`, `decision_traces`, `merchant_policies`, `policy_audit_logs`, `tool_executions`, `verifications`, `observability_telemetry`, `background_jobs`) include `tenant_id`.
- Composite Indexes added: `idx_payments_tenant_payment (tenant_id, payment_id)`, `idx_traces_tenant_policy_ver (tenant_id, policy_version)`, `idx_policies_tenant_version (tenant_id, version UNIQUE)`.

### 3.4 Canonical Policy Hashing & Validation (`policies/validation.py`)
- `compute_policy_config_hash(config)`: Deterministic SHA-256 hex digest over `json.dumps(config, sort_keys=True)`.
- `validate_policy_configuration(config)`: Rejects negative retry counts, negative cooldowns, float monetary limits, invalid percentage bounds (0.0–1.0), and attempts to set `captured_payment_retry_allowed = True` (POL_001 violation).

### 3.5 Lineage-Preserving Rollback (`apps/api/policy_service.py`)
- Rollback to historical version `v1` does NOT mutate `v1` or `v2`.
- Instead, it creates a new version `v3` containing `v1` configuration, sets `rollback_source_version = 1`, and transactionally promotes `v3` to `ACTIVE`.

### 3.6 Dry-Run Policy Simulation
- `POST /api/v1/operations/policies/{policy_id}/simulate`: Evaluates candidate policy configuration against historical benchmark cases.
- Computes hypothetical recovery rate, recovery rate delta, affected rules, and hypothetical net recovered value.
- **GUARANTEED ZERO SIDE EFFECTS, ZERO TOKEN ISSUANCE, ZERO DB MUTATIONS.**

---

## 4. Fine-Grained RBAC & Security Boundaries

| Role / Scope Tag | Granted Permissions | Description |
| :--- | :--- | :--- |
| `OPERATIONS_READ` | `OPERATIONS_READ`, `POLICY_READ` | Read-only telemetry, events, payments, and policy history. Cannot mutate state. |
| `OPERATIONS_CONTROL` | `OPERATIONS_READ`, `OPERATIONS_CONTROL`, `POLICY_READ`, `POLICY_WRITE` | Can manage operational jobs and draft policies. Cannot activate or rollback policies. |
| `POLICY_MANAGER` | `OPERATIONS_READ`, `POLICY_READ`, `POLICY_WRITE`, `POLICY_ACTIVATE`, `POLICY_ROLLBACK` | Complete merchant policy lifecycle management authority. |
| `TENANT_ADMIN` | All operational + policy permissions within tenant | Full administrative control over tenant scope. |
| `PLATFORM_ADMIN` | All permissions across all tenants | Global platform administrator context. |

---

## 5. Merchant Intelligence & Operations REST API

### Policy REST Router (`/api/v1/operations/policies`)
- `GET /api/v1/operations/policies`: List tenant policy versions.
- `GET /api/v1/operations/policies/{policy_id}`: Retrieve active policy for tenant.
- `GET /api/v1/operations/policies/{policy_id}/versions`: List version history.
- `POST /api/v1/operations/policies`: Create new DRAFT policy version (Requires `POLICY_WRITE`).
- `POST /api/v1/operations/policies/{policy_id}/validate`: Validate candidate configuration.
- `POST /api/v1/operations/policies/{policy_id}/simulate`: Dry-run policy simulation.
- `POST /api/v1/operations/policies/{policy_id}/activate`: Activate policy version (Requires `POLICY_ACTIVATE`).
- `POST /api/v1/operations/policies/{policy_id}/rollback`: Rollback to historical version (Requires `POLICY_ROLLBACK`).
- `GET /api/v1/operations/policies/{policy_id}/audit`: Query audit log trail.

### Merchant Intelligence Router (`/api/v1/operations/intelligence`)
- `GET /api/v1/operations/intelligence/overview`: Returns tenant-scoped recovery rate, gross recovered paise, average latency, top root causes, top recovery actions, policy veto counts, and ML performance metrics.

---

## 6. Verification & Quality Compliance

- **Pytest Test Suite**: `215 / 215 Passed`
- **Ruff Linter Check**: `0 Errors`
- **MyPy Static Type Checker**: `0 Errors across 190 source files`
- **Interactive Demonstration**: `python scripts/phase11_demo.py` (Exit Code 0)
