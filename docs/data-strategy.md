# RAVEN Synthetic Data Strategy & Simulator Specification

## 1. Purpose & Requirements

To evaluate RAVEN rigorously without risking live production credentials or violating privacy regulations, RAVEN includes a **Deterministic Synthetic Data Simulator (`simulator/`)**.

The simulator generates synthetic financial streams embedded with exact **Ground Truth Labels** (e.g. true underlying root cause, whether customer would organically retry, true payment network state) to enable 100% verifiable evaluation.

---

## 2. Generated Domain Dataset Scope

The synthetic generator produces full relational datasets including:
- **`Merchants`**: Diverse business verticals (E-commerce, SaaS Subscriptions, EdTech).
- **`Customers`**: Demographic variations, communication channel preferences, historical reliability scores.
- **`Orders` & `Payments`**: Amounts across minor units (`paise`), currencies, timestamps.
- **`PaymentAttempts`**: Card networks (Visa, Mastercard, RuPay), UPI handles, Netbanking issuers (HDFC, ICICI, SBI).
- **`Subscriptions`**: Recurring billing schedules, billing cycle states, past dunning histories.
- **`FinancialEvents`**: Raw JSON webhook payloads conforming to standard Razorpay webhook structures.

---

## 3. Simulator Test Scenarios

The simulator injects specific financial failure modes and network anomalies:

### Scenario 1: Transient Gateway / Issuer Timeout
- **Behavior**: Bank gateway experiences a temporary 90-second spike in error rates (`GATEWAY_TIMED_OUT`).
- **Ground Truth**: High recovery probability if retried after a 5-15 minute delay.

### Scenario 2: Hard Card Decline (Insufficient Funds / Expired Card)
- **Behavior**: Issuer returns `BAD_REQUEST_PAYMENT_DECLINED_INSUFFICIENT_FUNDS`.
- **Ground Truth**: Immediate automated retries will fail. Optimal action: Payment link dispatch to customer requesting fallback payment method.

### Scenario 3: Late Authorization Webhook
- **Behavior**: Payment attempt returns gateway timeout at `T+0s`, but issuer captures funds at `T+45s`. `payment.captured` webhook arrives delayed at `T+120s`.
- **Ground Truth**: Payment status is `CAPTURED`. System must recognize late capture and cancel any open recovery actions before execution.

### Scenario 4: Abandoned Checkout Intent
- **Behavior**: Order created (`order.created`), payment attempt initiated (`payment.initiated`), but user drops off at 3DS OTP screen (`AUTHENTICATION_ABANDONED`). No success or explicit failure webhook received.
- **Ground Truth**: Recoverable via targeted notification (WhatsApp/Email link) sent within 30 minutes.

### Scenario 5: Subscription Dunning (Recurring Card/NACH Failure)
- **Behavior**: Monthly recurring charge fails due to expired card token.
- **Ground Truth**: Subscriptions enter `PAST_DUE`. Requires fallback card update workflow.

### Scenario 6: Ambiguous Payment State
- **Behavior**: Gateway responds with HTTP 500 during status query; webhook delayed indefinitely.
- **Ground Truth**: Status is `AMBIGUOUS`. System must halt autonomous side-effects and execute state verification loop.

### Scenario 7: Duplicate Webhook Delivery
- **Behavior**: Gateway dispatches identical `payment.failed` webhook 3 times over a 10-second window.
- **Ground Truth**: System deduplicates events, ingesting only 1 event record.

### Scenario 8: Out-of-Order Webhook Delivery
- **Behavior**: `payment.captured` webhook arrives at `T+1s`, while `payment.authorized` webhook arrives at `T+4s`.
- **Ground Truth**: Reconstructed state derived via timestamp sorting is `CAPTURED`.

### Scenario 9: Organic Customer Recovery
- **Behavior**: Payment fails at `T+0s`. At `T+3m`, customer opens app and manually completes payment independently.
- **Ground Truth**: State becomes `CAPTURED`. Attribution engine must attribute recovery to `ORGANIC_CUSTOMER_RETRY` rather than RAVEN intervention.

---

## 4. Ground Truth Dataset Schema

Simulated datasets are output as structured JSON/NDJSON files in `data/raw/` containing an explicit ground truth metadata block:

```json
{
  "dataset_metadata": {
    "version": "1.0",
    "seed": 42,
    "total_merchants": 5,
    "total_orders": 1000,
    "generated_at": "2026-08-21T22:00:00Z"
  },
  "ground_truth": {
    "opp_1001": {
      "payment_id": "pay_M1001",
      "true_root_cause": "TRANSIENT_ISSUER_DOWNTIME",
      "is_recoverable": true,
      "organic_recovery_will_occur": false,
      "optimal_action": "SMART_RETRY",
      "expected_optimal_delay_seconds": 900
    }
  }
}
```
