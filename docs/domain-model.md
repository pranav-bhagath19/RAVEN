# RAVEN Domain Model Specification

## 1. Overview

This document specifies the core domain entities of **RAVEN**.

### Fundamental Monetary Rule
All monetary values across all entities are represented as **64-bit signed integers in minor units** (e.g., Indian Rupee `paise`, where `₹100.50` = `10050` paise). Floating-point values for currency calculations are strictly prohibited.

---

## 2. Conceptual Entities

### 2.1 Merchant
- **Purpose**: Represents the business entity using RAVEN for revenue recovery.
- **Key Fields**:
  - `id`: `String` (UUID / Merchant Key ID, e.g., `mer_01H...`)
  - `name`: `String`
  - `currency`: `String` (ISO 4217, e.g., `"INR"`)
  - `created_at`: `Timestamp` (ISO 8601 UTC)
  - `status`: `Enum` (`ACTIVE`, `SUSPENDED`, `ONBOARDING`)
  - `policy_config`: `JSON` (Merchant-specific rules, maximum recovery attempt caps, channel preferences)
- **Relationships**: Has many `Customer`s, `Order`s, `Subscription`s, `RecoveryOpportunity`s.
- **Invariants**: `currency` must strictly conform to ISO 4217 format.

---

### 2.2 Customer
- **Purpose**: Represents the paying customer purchasing goods/services from a Merchant.
- **Key Fields**:
  - `id`: `String` (`cust_...`)
  - `merchant_id`: `String`
  - `email`: `String`
  - `phone`: `String`
  - `name`: `String`
  - `created_at`: `Timestamp`
  - `communication_preferences`: `JSON` (Opt-out status for SMS/Email/WhatsApp recovery outreach)
- **Relationships**: Belongs to `Merchant`. Has many `Order`s, `Payment`s, `Subscription`s.
- **Invariants**: Phone and email must be normalized to standard E.164 and RFC 5322 formats.

---

### 2.3 Order
- **Purpose**: Represents a commercial intent to purchase.
- **Key Fields**:
  - `id`: `String` (`order_...`)
  - `merchant_id`: `String`
  - `customer_id`: `String`
  - `amount`: `Integer` (Minor unit, e.g., paise)
  - `amount_paid`: `Integer` (Minor unit)
  - `amount_due`: `Integer` (Minor unit)
  - `currency`: `String`
  - `status`: `Enum` (`CREATED`, `ATTEMPTED`, `PAID`, `EXPIRED`, `CANCELLED`)
  - `created_at`: `Timestamp`
  - `updated_at`: `Timestamp`
- **Relationships**: Belongs to `Merchant` and `Customer`. Has many `Payment`s.
- **Invariants**:
  - `amount_paid + amount_due == amount`
  - `amount > 0`
  - `amount_paid >= 0`

---

### 2.4 Payment
- **Purpose**: Represents a payment lifecycle entity associated with an Order.
- **Key Fields**:
  - `id`: `String` (`pay_...`)
  - `order_id`: `String`
  - `merchant_id`: `String`
  - `customer_id`: `String`
  - `amount`: `Integer` (Minor unit)
  - `currency`: `String`
  - `status`: `Enum` (`CREATED`, `AUTHORIZED`, `CAPTURED`, `REFUNDED`, `FAILED`, `AMBIGUOUS`)
  - `created_at`: `Timestamp`
  - `updated_at`: `Timestamp`
- **Relationships**: Belongs to `Order`. Has many `PaymentAttempt`s.
- **Invariants**:
  - A payment cannot transition to `CAPTURED` without prior `AUTHORIZED` or direct atomic capture event.
  - A payment in `CAPTURED` state cannot be targeted for retry actions.

---

### 2.5 PaymentAttempt
- **Purpose**: Represents a specific execution attempt for a payment across a gateway/network.
- **Key Fields**:
  - `id`: `String` (`att_...`)
  - `payment_id`: `String`
  - `attempt_sequence`: `Integer` (1, 2, 3...)
  - `payment_method_type`: `Enum` (`CARD`, `UPI`, `NETBANKING`, `WALLET`, `NACH`)
  - `status`: `Enum` (`INITIATED`, `PENDING`, `SUCCESS`, `FAILED`)
  - `error_code`: `String` (Gateway error code, e.g., `BAD_REQUEST_PAYMENT_TIMED_OUT`, `GATEWAY_DOWNTIME`)
  - `error_description`: `String`
  - `gateway_reference`: `String`
  - `initiated_at`: `Timestamp`
  - `completed_at`: `Optional[Timestamp]`
- **Relationships**: Belongs to `Payment`. Associated with a `PaymentMethod`.
- **Invariants**: `attempt_sequence` strictly increments starting at 1.

---

### 2.6 PaymentMethod
- **Purpose**: Abstracted payment instrument used in an attempt.
- **Key Fields**:
  - `id`: `String` (`pm_...`)
  - `customer_id`: `String`
  - `type`: `Enum` (`CARD`, `UPI`, `NETBANKING`, `WALLET`, `NACH`)
  - `network`: `Optional[String]` (`VISA`, `MASTERCARD`, `RUPAY`)
  - `issuer_bank`: `Optional[String]` (`HDFC`, `ICICI`, `SBI`)
  - `last4`: `Optional[String]`
  - `is_recurring_token`: `Boolean`
- **Relationships**: Belongs to `Customer`.

---

### 2.7 Subscription
- **Purpose**: Recurring payment schedule for ongoing service billing.
- **Key Fields**:
  - `id`: `String` (`sub_...`)
  - `merchant_id`: `String`
  - `customer_id`: `String`
  - `plan_id`: `String`
  - `amount`: `Integer` (Minor unit)
  - `billing_interval`: `Enum` (`WEEKLY`, `MONTHLY`, `YEARLY`)
  - `status`: `Enum` (`ACTIVE`, `PAST_DUE`, `HALTED`, `CANCELLED`)
  - `current_period_start`: `Timestamp`
  - `current_period_end`: `Timestamp`
  - `consecutive_failures`: `Integer`
- **Relationships**: Belongs to `Merchant` and `Customer`.
- **Invariants**: `consecutive_failures >= 0`.

---

### 2.8 FinancialEvent
- **Purpose**: Immutable raw input event (webhook payload, API event log) ingested by RAVEN.
- **Key Fields**:
  - `id`: `String` (`evt_...`)
  - `event_hash`: `String` (SHA256 signature of raw body)
  - `event_type`: `String` (e.g., `payment.failed`, `payment.captured`, `order.paid`)
  - `gateway_event_id`: `String`
  - `payload`: `JSON`
  - `occurred_at`: `Timestamp`
  - `received_at`: `Timestamp`
  - `sequence_number`: `Integer`
- **Relationships**: Maps to zero or one `Payment`, `Order`, or `Subscription`.
- **Invariants**: Immutable append-only record. Duplicate `event_hash` or `gateway_event_id` is rejected or marked duplicate during ingestion.

---

### 2.9 RecoveryOpportunity
- **Purpose**: Identified revenue risk case flagged by RAVEN for analysis and recovery planning.
- **Key Fields**:
  - `id`: `String` (`opp_...`)
  - `merchant_id`: `String`
  - `payment_id`: `String`
  - `amount_at_risk`: `Integer` (Minor unit)
  - `risk_category`: `Enum` (`TRANSIENT_GATEWAY_FAILURE`, `ABANDONED_CHECKOUT`, `SUBSCRIPTION_DUNNING`, `ISSUER_DOWNTIME`)
  - `status`: `Enum` (`OPEN`, `ANALYZING`, `ACTION_PROPOSED`, `EXECUTING`, `VERIFYING`, `RECOVERED`, `FAILED`, `ESCALATED`)
  - `created_at`: `Timestamp`
- **Relationships**: Links `Payment` to `RecoveryAction` and `RecoveryOutcome`.
- **Invariants**: `amount_at_risk` equals the unrecovered value of the associated payment.

---

### 2.10 RecoveryAction
- **Purpose**: Candidate or executed recovery intervention generated by Recovery Planner agent.
- **Key Fields**:
  - `id`: `String` (`act_...`)
  - `opportunity_id`: `String`
  - `action_type`: `Enum` (`SMART_RETRY`, `PAYMENT_LINK_DISPATCH`, `FALLBACK_CHANNEL_NOTIFY`, `ESCALATE_TO_HUMAN`)
  - `parameters`: `JSON` (e.g., retry delay, channel info, link expiry)
  - `expected_recovery_value`: `Integer` (Minor unit calculation of \(EV\))
  - `agent_confidence`: `Float` (Range `0.0` to `1.0`)
  - `policy_decision`: `Enum` (`APPROVED`, `BLOCKED`, `PENDING_HUMAN_REVIEW`)
  - `execution_status`: `Enum` (`SCHEDULED`, `EXECUTED`, `FAILED`, `SKIPPED`)
  - `executed_at`: `Optional[Timestamp]`
- **Relationships**: Belongs to `RecoveryOpportunity`.

---

### 2.11 RecoveryOutcome
- **Purpose**: Formal financial verification outcome recorded by Verification Agent.
- **Key Fields**:
  - `id`: `String` (`out_...`)
  - `opportunity_id`: `String`
  - `action_id`: `String`
  - `is_recovered`: `Boolean`
  - `recovered_amount`: `Integer` (Minor unit)
  - `verification_method`: `Enum` (`GATEWAY_CAPTURED_EVENT`, `RECONCILED_ORDER_STATE`, `MANUAL_AUDIT`)
  - `verified_at`: `Timestamp`
- **Relationships**: Belongs to `RecoveryOpportunity` and `RecoveryAction`.
- **Invariants**: If `is_recovered` is True, `recovered_amount > 0`. If `is_recovered` is False, `recovered_amount == 0`.

---

### 2.12 AuditEvent
- **Purpose**: Append-only tamper-evident audit record capturing all operations across RAVEN.
- **Key Fields**:
  - `id`: `String` (`aud_...`)
  - `trace_id`: `String` (Global correlation UUID tracing event → agent → policy → tool → verification)
  - `entity_type`: `String`
  - `entity_id`: `String`
  - `actor_type`: `Enum` (`SYSTEM`, `AGENT_ROOT_CAUSE`, `AGENT_RECOVERY_PLANNER`, `AGENT_VERIFIER`, `POLICY_ENGINE`, `HUMAN_OPERATOR`)
  - `action`: `String`
  - `payload_snapshot`: `JSON`
  - `created_at`: `Timestamp`
- **Invariants**: Read-only, append-only ledger.
