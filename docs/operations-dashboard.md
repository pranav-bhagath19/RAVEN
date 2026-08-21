# RAVEN Operations Control Plane & REST Management API Specification

## 1. Overview

The **RAVEN Operations Control Plane** exposes observational metrics, lineage inspection, telemetry, and controlled reprocessing commands over the RAVEN domain engine.

### Critical Security Invariant
The Operations Control Plane is **OBSERVATIONAL and MANAGEMENT-ORIENTED**. It is **NOT** a second decision engine.

It **NEVER**:
- Bypasses the deterministic `PolicyEngine`.
- Issues `PolicyApprovalToken` tokens directly from API handlers.
- Directly executes side-effect tools outside `ToolExecutor`.
- Overrides deterministic verification outcomes.
- Modifies financial event ledger history.

---

## 2. System Architecture

```
                 ┌─────────────────────────┐
                 │     Operations UI       │
                 └────────────┬────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │   REST Management API   │
                 │  /api/v1/operations/... │
                 └────────────┬────────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          Read-only queries          Controlled commands
                 │                         │
                 ▼                         ▼
          Domain repositories       Existing domain services
                                           │
                                           ▼
                                   PolicyEngine
                                           │
                                           ▼
                                     ToolExecutor
                                           │
                                           ▼
                                      Verification
```

---

## 3. API Catalog (/api/v1/operations/)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/operations/overview` | Aggregate operational metrics summary |
| `GET` | `/api/v1/operations/payments` | Paginated payment list with filtering |
| `GET` | `/api/v1/operations/payments/{payment_id}` | Detailed payment state & trace reference |
| `GET` | `/api/v1/operations/events` | Paginated financial events log |
| `GET` | `/api/v1/operations/decisions` | Paginated DecisionTrace summaries |
| `GET` | `/api/v1/operations/traces/{trace_id}` | Complete chronological DecisionTrace lineage |
| `GET` | `/api/v1/operations/actions` | Catalog of candidate recovery action types |
| `GET` | `/api/v1/operations/policies` | PolicyEngine rule metadata & statistics |
| `GET` | `/api/v1/operations/tool-executions` | ToolExecutor side-effect audit logs |
| `GET` | `/api/v1/operations/verifications` | Verification Agent outcome logs |
| `GET` | `/api/v1/operations/agents/telemetry` | PII-sanitized LLM Observability telemetry |
| `GET` | `/api/v1/operations/benchmarks` | Comparative evaluation benchmark report |
| `GET` | `/api/v1/operations/health` | Control plane health & subsystem status |
| `GET` | `/api/v1/operations/ready` | Webhook ingestion readiness status |
| `POST` | `/api/v1/operations/payments/{payment_id}/reprocess` | Controlled reprocess routing via PolicyEngine |
| `POST` | `/api/v1/operations/payments/{payment_id}/escalate` | Escalate payment to human operations queue |

---

## 4. DecisionTrace Chronological Lineage Timeline

The `GET /api/v1/operations/traces/{trace_id}` endpoint returns a complete chronological milestone timeline:

```
EVENT_RECEIVED (Ingested)
       │
       ▼
STATE_RECONSTRUCTED (Reconstructed State)
       │
       ▼
ROOT_CAUSE_ANALYZED (Identified Root Cause)
       │
       ▼
RECOVERY_PLAN_GENERATED (Candidate Proposals & Expected Value)
       │
       ▼
POLICY_EVALUATED (PolicyEngine Decision)
       │
       ▼
APPROVAL_TOKEN_ISSUED (HMAC PolicyApprovalToken)
       │
       ▼
TOOL_EXECUTED (ToolExecutor Result)
       │
       ▼
OUTCOME_VERIFIED (Verification Attribution)
```

---

## 5. Security & Privacy Controls
1. **PII Sanitization**: Customer emails and phone numbers in telemetry are automatically masked using `sanitize_pii`.
2. **Secret Redaction**: Webhook secrets, HMAC keys, API tokens, and authorization headers are never exposed in API outputs or logs.
3. **Strict Pagination**: Default page size is 50; maximum page size is enforced at 100 via Pydantic validation.
4. **Error Masking**: 404/400 errors return structured error JSON without leaking internal stack traces.
