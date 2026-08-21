# RAVEN Testing Strategy Specification

## 1. Overview & Testing Philosophy

To guarantee financial correctness, reliability, and security, RAVEN enforces a multi-tier testing strategy using `pytest`.

### Golden Rule of Testing
No test may be trivial or meaningless (e.g. `assert True` or simple instantiation checks). Every test must assert specific **domain invariants**, **state machine transitions**, **policy enforcement rules**, or **idempotency bounds**.

---

## 2. Testing Pyramid & Suite Classification

```
                  ┌───────────────────────────────┐
                  │    Evaluation Benchmark Tests │
                  ├───────────────────────────────┤
                  │     End-to-End System Tests   │
                  ├───────────────────────────────┤
                  │ Agent Contract & Tool Tests   │
                  ├───────────────────────────────┤
                  │ Event & Policy Engine Tests   │
                  ├───────────────────────────────┤
                  │   Domain & State Unit Tests   │
                  └───────────────────────────────┘
```

### 2.1 Domain & State Unit Tests (`tests/unit/`)
- Validate entity invariants (e.g., integer minor unit currency validation, `amount_paid + amount_due == amount`).
- Validate State Machine deterministic state transitions (`CREATED` → `AUTHORIZED` → `CAPTURED`).

### 2.2 Event Processing & Deduplication Tests (`tests/events/`)
- **Duplicate Webhook Test**: Submit identical webhook body 5 times concurrently; verify `FinancialEvent` store records exactly 1 event and State Machine evaluates once.
- **Out-of-Order Delivery Test**: Dispatch `payment.captured` at `T+1s` followed by `payment.authorized` at `T+5s`. Verify reconstructed state resolves strictly to `CAPTURED`.
- **Late Event Replay Test**: Dispatch `payment.failed` followed 120 seconds later by late `payment.captured`. Verify status transitions correctly from `FAILED` to `CAPTURED` and open recovery opportunities close.

### 2.3 Policy Engine Enforcement Tests (`tests/policies/`)
- **Captured Payment Guard (`POL_001`)**: Attempt to dispatch retry action for an already `CAPTURED` payment. Assert Policy Engine decision is `BLOCKED` with rule code `POL_001`.
- **Ambiguous State Isolation (`POL_002`)**: Attempt recovery action on payment with status `AMBIGUOUS`. Assert decision is `ESCALATE_TO_HUMAN`.
- **Max Attempt Limit Cap (`POL_003`)**: Execute 3 retries, then attempt 4th. Assert 4th action is `BLOCKED`.
- **High-Value Cap (`POL_004`)**: Submit candidate action for ₹50,000 payment. Assert decision is `ESCALATE_TO_HUMAN`.
- **Unsigned Tool Call Protection**: Call `retry_payment` tool directly without supplying a valid `PolicyApprovalToken`. Assert tool throws `PolicyViolationError`.

### 2.4 Agent Contract Tests (`tests/agents/`)
- Validate structured output format (Pydantic schema compliance) for Root Cause Analyst, Recovery Planner, and Verification Agent outputs.
- Assert that Recovery Planner agent strictly outputs candidate proposals and does not call side-effect tools directly.

### 2.5 Tool Contract & Idempotency Tests (`tests/tools/`)
- Execute `create_payment_link` tool twice with identical `idempotency_key`. Assert second call returns cached payment link object without making duplicate external API calls.

### 2.6 End-to-End & Failure Injection Tests (`tests/e2e/`)
- **Gateway Timeout Injection**: Simulate gateway 504 Gateway Timeout during payment link creation. Verify system catches exception, logs audit event, and flags opportunity as `FAILED_RETRY_SCHEDULED`.

---

## 3. Test Execution Command

All tests are executed via `pytest`:
```bash
pytest tests/ -v --cov=domain --cov=events --cov=policies --cov=agents --cov=tools
```
