# RAVEN Firestore Data Model Reference

## Collections Overview

| Collection Name | Primary Document ID | Description |
|---|---|---|
| `tenants` | `tenant_id` | Multi-tenant organization account metadata |
| `users` | `user_id` | Operator user account records and roles |
| `user_api_keys` | `key_id` | SHA-256 hashed API key metadata |
| `payments` | `payment_id` | Reconstructed payment lifecycle states |
| `financial_events` | `event_id` | Append-only financial event ledger |
| `webhook_ingestions` | `webhook_id` | Gateway webhook audit and deduplication records |
| `decision_traces` | `decision_id` | Immutable DecisionTrace audit lineage |
| `merchant_policies` | `${tenant_id}_v${version}` | Merchant policy configurations & versions |
| `policy_audit_logs` | `audit_id` | Lineage audit logs for policy changes |
| `tool_executions` | `execution_id` | ToolExecutor side-effect execution logs |
| `verifications` | `${payment_id}_${action_id}` | Verification outcome records |
| `observability_telemetry` | `telemetry_id` | LLM observability telemetry records |
| `background_jobs` | `job_id` | Asynchronous background job queue |
| `adaptive_outcomes` | `outcome_id` | Scorer feedback loop outcome records |
| `model_registry` | `model_version` | Machine learning model version registry |
| `idempotency` | `${tenant_id}:${region}:${key}` | Distributed atomic idempotency locks |
