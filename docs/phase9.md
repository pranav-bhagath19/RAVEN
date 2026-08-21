# RAVEN Phase 9 Architecture & Production Manual

## 1. Overview

Phase 9 transforms RAVEN into a production-shaped, fault-tolerant financial engine supporting:
- **Persistent Storage**: PostgreSQL ORM schema (`payments`, `financial_events`, `decision_traces`, `tool_executions`, `verifications`, `telemetry`, `background_jobs`).
- **Distributed Coordination**: Redis-backed atomic idempotency locks (`RedisIdempotencyStore`) with in-memory thread-safe fallback (`LocalIdempotencyStore`).
- **Asynchronous Background Processing**: Webhook HTTP 202 acknowledgment $\rightarrow$ background worker queue execution (`RecoveryWorker`).
- **Live Gateway Boundary**: `LiveRazorpayClient` communicating via HTTPS REST with fallback to `MockRazorpayClient`.
- **API Authentication & Authorization**: RBAC permissions distinguishing `OPERATIONS_READ` and `OPERATIONS_CONTROL`.
- **Reliability Safeguards**: Token Bucket rate limiting and Circuit Breakers (`CLOSED`, `OPEN`, `HALF_OPEN`) wrapping external dependencies.

---

## 2. Security Architecture Invariants (Preserved 100%)

The central security paradigm remains non-bypassable:

```
        AI Reasoning (Candidate Proposals)
                      │
                      ▼
        Deterministic Expected Value
                      │
                      ▼
        Deterministic Policy Engine (POL_001 - POL_007)
                      │
                      ▼
        HMAC-SHA256 PolicyApprovalToken Issuance
                      │
                      ▼
        ToolExecutor (Cryptographic Signature & Binding Verification)
                      │
                      ▼
        Deterministic Verification Agent (Attribution Precision)
```

---

## 3. Running Services locally / via Docker Compose

### Development Run (SQLite + In-Memory Fallbacks)
```bash
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000
```

### Full Production Run via Docker Compose
```bash
docker-compose up --build -d
```

### Executing Demos
```bash
python scripts/demo.py
python scripts/security_demo.py
python -m apps.api.demo
```
