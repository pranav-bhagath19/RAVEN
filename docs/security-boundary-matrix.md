# RAVEN Security & Authority Boundary Matrix

## 1. System Components Authority Matrix

The following matrix documents the exact permissions, constraints, and non-bypassable boundaries for every architectural component in RAVEN across Phases 1–15:

| Component | Can Propose Actions? | Can Execute Tools? | Can Issue Tokens? | Can Override PolicyEngine? | Can Modify Monetary State? | Supreme Authority? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **LLM Provider** | YES | **NO** | **NO** | **NO** | **NO** | NO |
| **ML Propensity Scorer** | YES (Advisory) | **NO** | **NO** | **NO** | **NO** | NO |
| **Adaptive Scorer** | YES (Advisory) | **NO** | **NO** | **NO** | **NO** | NO |
| **Contextual Bandit** | YES (Advisory) | **NO** | **NO** | **NO** | **NO** | NO |
| **RecoveryPlanner** | YES | **NO** | **NO** | **NO** | **NO** | NO |
| **PolicyEngine** | **NO** (Evaluates) | **NO** | YES (Implicit) | **N/A** (Is Authority) | **NO** | **YES (VETO AUTHORITY)** |
| **Token Generator** | **NO** | **NO** | **YES (HMAC-SHA256)** | **NO** | **NO** | NO |
| **ToolExecutor** | **NO** | **YES** | **NO** | **NO** | **NO** | **YES (EXECUTION BOUNDARY)** |
| **VerificationAgent** | **NO** | **NO** | **NO** | **NO** | **NO** | NO |
| **Observability Telemetry** | **NO** | **NO** | **NO** | **NO** | **NO** | NO |
| **RecoveryWorker** | **NO** | Indirect | **NO** | **NO** | **NO** | NO |

---

## 2. Security Invariant Definitions

1. **PolicyEngine Non-Bypassability**: `PolicyEngine` is the sole deterministic veto authority. If `PolicyEngine` returns `BLOCKED`, zero tokens can be issued and zero tool executions can take place.
2. **ToolExecutor Boundary Integrity**: `ToolExecutor` is the sole consequential side-effect dispatch boundary. Tool execution requires a cryptographically valid HMAC-SHA256 `PolicyApprovalToken` matching `action_id`, `opportunity_id`, `payment_id`, `action_type`, `policy_version`, and `idempotency_key`.
3. **Monetary State Immutability**: All monetary calculations use integer minor units (paise). Floating-point monetary fields are strictly prohibited.
4. **Tenant Isolation**: Multi-tenant isolation is enforced at the database schema, cache key, and policy version tree levels. Cross-tenant access is strictly rejected.
5. **Fail-Closed Default**: Any network failure, stale replication checkpoint (>300s), ambiguous conflict lineage, or missing approval token results in immediate fail-closed rejection.
