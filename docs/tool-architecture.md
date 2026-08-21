# RAVEN Tool Architecture Specification

## 1. Overview & Security Principles

Tools in RAVEN provide standard interfaces for agents and system components to query system state, execute policy-checked actions, and record audit records.

### Permission & Idempotency Classification
- **READ_ONLY Tools**: Side-effect free queries. No idempotency keys required.
- **DETERMINISTIC_CALCULATION Tools**: Mathematical or statistical functions.
- **SIDE_EFFECT Tools**: Modify state or dispatch external communications (e.g. gateway API, SMS, payment links). **MUST** require a valid `PolicyApprovalToken` and an explicit `idempotency_key`.

---

## 2. Tool Specifications

### 2.1 `get_payment`
- **Purpose**: Retrieves payment details and current status.
- **Permission**: `READ_ONLY`
- **Input**: `payment_id`: `String`
- **Output**: `Payment` domain entity payload.
- **Error Behavior**: Returns `PaymentNotFoundError` if ID does not exist.

### 2.2 `get_order`
- **Purpose**: Retrieves order details and financial status.
- **Permission**: `READ_ONLY`
- **Input**: `order_id`: `String`
- **Output**: `Order` domain entity payload.
- **Error Behavior**: Returns `OrderNotFoundError`.

### 2.3 `get_customer`
- **Purpose**: Retrieves customer profile and communication preferences.
- **Permission**: `READ_ONLY`
- **Input**: `customer_id`: `String`
- **Output**: `Customer` domain entity payload (PII masked for non-authorized contexts).
- **Error Behavior**: Returns `CustomerNotFoundError`.

### 2.4 `get_payment_history`
- **Purpose**: Fetches past payment attempts and success rates for a given customer.
- **Permission**: `READ_ONLY`
- **Input**: `customer_id`: `String`, `limit`: `Integer` (Default 10)
- **Output**: `List[PaymentAttempt]`
- **Error Behavior**: Returns empty list if no history exists.

### 2.5 `get_subscription`
- **Purpose**: Retrieves subscription plan state and failure history.
- **Permission**: `READ_ONLY`
- **Input**: `subscription_id`: `String`
- **Output**: `Subscription` domain entity.
- **Error Behavior**: Returns `SubscriptionNotFoundError`.

### 2.6 `get_event_history`
- **Purpose**: Retrieves all ingested `FinancialEvent` records for a transaction.
- **Permission**: `READ_ONLY`
- **Input**: `entity_id`: `String` (Payment ID or Order ID)
- **Output**: `List[FinancialEvent]` sorted by `occurred_at` ASC.
- **Error Behavior**: Returns empty list if no events ingested.

### 2.7 `get_revenue_risk`
- **Purpose**: Calculates current unrecovered revenue at risk for a merchant or transaction.
- **Permission**: `READ_ONLY`
- **Input**: `merchant_id`: `String`, `opportunity_id`: `Optional[String]`
- **Output**: `amount_at_risk_paise`: `Integer`, `risk_level`: `Enum` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- **Error Behavior**: Returns 0 if no risk flagged.

### 2.8 `get_failure_patterns`
- **Purpose**: Aggregates issuer/bank error rates over the last 15-60 minutes to detect systemic bank downtimes.
- **Permission**: `READ_ONLY`
- **Input**: `issuer_bank`: `Optional[String]`, `payment_method_type`: `Optional[String]`
- **Output**: `failure_rate_percent`: `Float`, `is_known_downtime`: `Boolean`
- **Error Behavior**: Returns default baseline metrics if insufficient data window.

### 2.9 `calculate_expected_recovery`
- **Purpose**: Deterministically computes Expected Recovery Value (\(EV\)) in paise.
- **Permission**: `DETERMINISTIC_CALCULATION`
- **Input**: `amount_paise`: `Integer`, `success_probability`: `Float`, `intervention_cost_paise`: `Integer`
- **Output**: `expected_value_paise`: `Integer`
- **Formula**: \(\text{round}(\text{amount\_paise} \times \text{success\_probability}) - \text{intervention\_cost\_paise}\)

### 2.10 `get_allowed_interventions`
- **Purpose**: Queries Policy Engine for permitted recovery action types for a transaction.
- **Permission**: `READ_ONLY`
- **Input**: `merchant_id`: `String`, `payment_id`: `String`
- **Output**: `allowed_actions`: `List[Enum]`, `restricted_actions`: `List[Enum]`
- **Error Behavior**: Safe default returns empty list of allowed actions.

### 2.11 `create_payment_link`
- **Purpose**: Generates a Razorpay payment link for an abandoned or failed order.
- **Permission**: `SIDE_EFFECT` (Requires `PolicyApprovalToken`)
- **Idempotency**: Mandatory `idempotency_key` (derived from `opportunity_id + attempt_count`).
- **Input**: `order_id`: `String`, `expiry_seconds`: `Integer`, `idempotency_key`: `String`, `policy_token`: `String`
- **Output**: `payment_link_id`: `String`, `short_url`: `String`, `expires_at`: `Timestamp`
- **Audit Requirement**: Logs `create_payment_link.dispatch` to `AuditEvent`.

### 2.12 `retry_payment`
- **Purpose**: Triggers a backend payment retry for recurring/subscription tokens.
- **Permission**: `SIDE_EFFECT` (Requires `PolicyApprovalToken`)
- **Idempotency**: Mandatory `idempotency_key`.
- **Input**: `subscription_id`: `String`, `payment_method_id`: `String`, `idempotency_key`: `String`, `policy_token`: `String`
- **Output**: `new_attempt_id`: `String`, `status`: `Enum` (`INITIATED`, `FAILED`)
- **Error Behavior**: Returns `MaxRetryLimitExceededError` if retry limit hit.

### 2.13 `send_recovery_message`
- **Purpose**: Sends a recovery notification (WhatsApp/Email/SMS) containing payment link.
- **Permission**: `SIDE_EFFECT` (Requires `PolicyApprovalToken`)
- **Idempotency**: Mandatory `idempotency_key`.
- **Input**: `customer_id`: `String`, `channel`: `Enum`, `message_template_id`: `String`, `payment_link_url`: `String`, `idempotency_key`: `String`, `policy_token`: `String`
- **Output**: `message_id`: `String`, `status`: `Enum` (`QUEUED`, `SENT`, `FAILED`)
- **Error Behavior**: Aborts if customer opt-out preference is set.

### 2.14 `verify_payment_state`
- **Purpose**: Queries state reconstructor and underlying gateway to confirm payment state.
- **Permission**: `READ_ONLY`
- **Input**: `payment_id`: `String`
- **Output**: `reconstructed_status`: `Enum`, `gateway_status`: `Enum`, `is_consistent`: `Boolean`

### 2.15 `verify_recovery`
- **Purpose**: Performs formal verification of whether an intervention recovered revenue.
- **Permission**: `READ_ONLY`
- **Input**: `opportunity_id`: `String`, `action_id`: `String`
- **Output**: `RecoveryOutcome` entity payload.

### 2.16 `escalate_to_human`
- **Purpose**: Routes high-value, ambiguous, or policy-blocked cases to human operator dashboard.
- **Permission**: `SIDE_EFFECT`
- **Input**: `opportunity_id`: `String`, `reason`: `String`, `suggested_action`: `Optional[String]`
- **Output**: `ticket_id`: `String`, `escalated_at`: `Timestamp`

### 2.17 `record_audit_event`
- **Purpose**: Writes an immutable entry to the central audit log.
- **Permission**: `INTERNAL_SYSTEM`
- **Input**: `trace_id`: `String`, `actor_type`: `Enum`, `action`: `String`, `payload_snapshot`: `JSON`
- **Output**: `audit_event_id`: `String`
