# RAVEN Tool Architecture & Candidate Contracts

## 1. Overview & Tool Framing

This document defines the **initial tool candidates and contracts** for RAVEN.

### Implementation Framing Note
The 17 tools listed below represent candidate capabilities. During backend implementation, capabilities will be evaluated to determine which genuinely require exposure as LLM-facing agent tools versus remaining internal domain services. Capabilities that do not require non-deterministic reasoning will remain internal domain services.

---

## 2. Capability Classification

Capabilities fall into three distinct implementation categories:

1. **READ_ONLY Queries**: Query system state, payment histories, failure patterns, or event logs.
2. **DETERMINISTIC_CALCULATION Services**: Mathematical or statistical calculations (e.g. Expected Recovery Value).
3. **SIDE_EFFECT Tools**: Execute external API calls (e.g. create payment link, trigger payment retry, dispatch message). **MUST** require a valid `PolicyApprovalToken` and explicit `idempotency_key`.

---

## 3. Initial Tool Candidates List

| Candidate Tool | Target Category | LLM Exposure Status |
| :--- | :--- | :--- |
| `get_payment` | READ_ONLY | Candidate Agent Tool |
| `get_order` | READ_ONLY | Candidate Agent Tool |
| `get_customer` | READ_ONLY | Candidate Agent Tool |
| `get_payment_history` | READ_ONLY | Candidate Agent Tool |
| `get_subscription` | READ_ONLY | Candidate Agent Tool |
| `get_event_history` | READ_ONLY | Candidate Agent Tool |
| `get_revenue_risk` | READ_ONLY | Internal Domain Service / Agent Tool |
| `get_failure_patterns` | READ_ONLY | Candidate Agent Tool |
| `calculate_expected_recovery` | DETERMINISTIC_CALCULATION | Internal Domain Service / Agent Tool |
| `get_allowed_interventions` | READ_ONLY | Candidate Agent Tool |
| `create_payment_link` | SIDE_EFFECT | Executable Side-Effect Tool (Policy Token Required) |
| `retry_payment` | SIDE_EFFECT | Executable Side-Effect Tool (Policy Token Required) |
| `send_recovery_message` | SIDE_EFFECT | Executable Side-Effect Tool (Policy Token Required) |
| `verify_payment_state` | READ_ONLY | Internal Domain Service / Verifier Tool |
| `verify_recovery` | READ_ONLY | Internal Domain Service / Verifier Tool |
| `escalate_to_human` | SIDE_EFFECT | Executable Side-Effect Tool |
| `record_audit_event` | INTERNAL_SYSTEM | Internal System Service |

---

## 4. Contract Specifications for Core Side-Effect Tools

### 4.1 `create_payment_link`
- **Purpose**: Generates a Razorpay payment link for an abandoned or failed order.
- **Permission**: `SIDE_EFFECT` (Requires `PolicyApprovalToken`)
- **Idempotency**: Mandatory `idempotency_key`.
- **Input**: `order_id`: `String`, `expiry_seconds`: `Integer`, `idempotency_key`: `String`, `policy_token`: `String`
- **Output**: `payment_link_id`: `String`, `short_url`: `String`, `expires_at`: `Timestamp`

### 4.2 `retry_payment`
- **Purpose**: Triggers a backend payment retry for recurring/subscription tokens.
- **Permission**: `SIDE_EFFECT` (Requires `PolicyApprovalToken`)
- **Idempotency**: Mandatory `idempotency_key`.
- **Input**: `subscription_id`: `String`, `payment_method_id`: `String`, `idempotency_key`: `String`, `policy_token`: `String`
- **Output**: `new_attempt_id`: `String`, `status`: `Enum`

### 4.3 `send_recovery_message`
- **Purpose**: Dispatches recovery outreach containing payment link.
- **Permission**: `SIDE_EFFECT` (Requires `PolicyApprovalToken`)
- **Idempotency**: Mandatory `idempotency_key`.
- **Input**: `customer_id`: `String`, `channel`: `Enum`, `message_template_id`: `String`, `payment_link_url`: `String`, `idempotency_key`: `String`, `policy_token`: `String`
- **Output**: `message_id`: `String`, `status`: `Enum`
