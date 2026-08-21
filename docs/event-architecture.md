# RAVEN Event Architecture & State Reconstruction Engine

## 1. Core Principles

Payment webhooks and financial event notifications in real-world networks (e.g., Razorpay, banks, card networks) are inherently **asynchronous**, **unreliable**, **duplicated**, and **out-of-order**.

### Fundamental Rule
> **Webhook arrival order must not be treated as financial event order.**  
> **Financial state is deterministically reconstructed from normalized financial events.**

A system that assumes strictly ordered, exactly-once delivery will corrupt entity states—for example, processing an out-of-order `payment.failed` event after a `payment.captured` event could accidentally reopen a successfully paid order.

---

## 2. Robust State Reconstruction Framework

State reconstruction does not rely on arrival timestamps alone. It evaluates a multi-factored resolution chain:

1. **Canonical Event Identity**: Unique identifier (`gateway_event_id` and SHA256 content `event_hash`).
2. **Event Deduplication**: Incoming payloads matching existing identity hashes are rejected at ingestion.
3. **Normalized Event Representation**: Normalizes payloads into canonical schema regardless of gateway origin.
4. **Event Metadata Evaluation**: Extracts gateway occurrence timestamps, event sequence markers, and transaction context.
5. **Deterministic State Transition Rules**: Explicit state machine transition matrix (`CREATED` $\rightarrow$ `AUTHORIZED` $\rightarrow$ `CAPTURED`).
6. **Late Event Handling**: Late arriving authorizations or captures trigger terminal state transitions and close open recovery actions.
7. **Conflicting Event Resolution**: Terminal states (`CAPTURED`, `PAID`) take precedence over transient or out-of-order failure notifications.
8. **Reconciliation Behavior**: Background polling services verify state against gateway APIs when event streams stall or show ambiguity.

---

## 3. Ingestion & Normalization Pipeline

```
Incoming Webhook HTTP POST
          │
          ▼
┌─────────────────────────────────────────┐
│ 1. Signature Verification (HMAC-SHA256) │
└────────────────────┬────────────────────┘
                     │ Valid
                     ▼
┌─────────────────────────────────────────┐
│ 2. Deduplication & Identity Verification│
└────────────────────┬────────────────────┘
                     │ New Event
                     ▼
┌─────────────────────────────────────────┐
│ 3. Canonical Event Normalization        │
└────────────────────┬────────────────────┘
                     │ Normalized Event
                     ▼
┌─────────────────────────────────────────┐
│ 4. Append to Normalized Event Log       │
└────────────────────┬────────────────────┘
                     │ Event Logged
                     ▼
┌─────────────────────────────────────────┐
│ 5. Trigger Deterministic State Replay   │
└─────────────────────────────────────────┘
```
