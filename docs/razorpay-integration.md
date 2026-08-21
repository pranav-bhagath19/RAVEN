# RAVEN Razorpay Integration Boundary Specification

## 1. Overview & Architectural Boundaries

RAVEN is designed to interface with payment ecosystems via standard API and Webhook protocols. To ensure safety, reliability, and ease of testing, RAVEN enforces a clean separation between **Local Simulation** and **Razorpay Gateway Integration**.

```
                           ┌───────────────────────────┐
                           │   Gateway Adapter Layer   │
                           └─────────────┬─────────────┘
                                         │
             ┌───────────────────────────┴───────────────────────────┐
             ▼                                                       ▼
┌───────────────────────────┐                           ┌───────────────────────────┐
│ Local Simulator Adapter   │                           │ Razorpay Gateway Adapter  │
│ (Default Test Environment)│                           │ (Test-Mode / Production)  │
└───────────────────────────┘                           └───────────────────────────┘
```

---

## 2. Supported Razorpay Events

RAVEN maps incoming webhooks against official Razorpay Webhook Event types:

| Razorpay Webhook Event | Mapping in RAVEN | Triggered Action |
| :--- | :--- | :--- |
| `payment.authorized` | `PAYMENT_AUTHORIZED` | Transition payment to `AUTHORIZED`. |
| `payment.captured` | `PAYMENT_CAPTURED` | Reconstruct state to `CAPTURED`. Close open `RecoveryOpportunity`. |
| `payment.failed` | `PAYMENT_FAILED` | Trigger State Reconstructor. Flag `RecoveryOpportunity` if recoverable. |
| `order.paid` | `ORDER_PAID` | Transition order status to `PAID`. |
| `refund.created` | `REFUND_CREATED` | Log refund event in `FinancialEvent` ledger. |

*Note: RAVEN relies strictly on established Razorpay webhook contract specifications and does not invent or assume non-existent API endpoints or properties.*

---

## 3. Webhook Signature Verification

Webhooks received at `POST /api/v1/webhooks/razorpay` are verified deterministically before processing:

1. **Extract Signature Header**: Read `X-Razorpay-Signature` HTTP header.
2. **Compute Expected HMAC**:
   $$\text{Signature} = \text{HMAC-SHA256}(\text{raw\_http\_body}, \text{RAZORPAY\_WEBHOOK\_SECRET})$$
3. **Constant-Time Comparison**: Compare computed signature with header using constant-time string comparison (`hmac.compare_digest`) to prevent timing attacks.

---

## 4. Configuration & Credentials

All integration settings are loaded strictly via environment variables. Hardcoding credentials in source files is strictly prohibited.

```bash
# Razorpay Credentials (Loaded via .env)
RAZORPAY_KEY_ID=YOUR_RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET=YOUR_RAZORPAY_KEY_SECRET
RAZORPAY_WEBHOOK_SECRET=YOUR_RAZORPAY_WEBHOOK_SECRET

# Execution Mode Selector
RAZORPAY_MODE=simulation # Options: 'simulation' | 'test' | 'live'
```

---

## 5. Gateway Adapter Contract

All gateway operations are exposed via a Python Abstract Base Class (`PaymentGatewayAdapter`):

```python
# Conceptual Interface Contract
class PaymentGatewayAdapter(ABC):
    
    @abstractmethod
    def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """Fetch payment details from gateway."""
        pass
        
    @abstractmethod
    def create_payment_link(self, order_id: str, amount_paise: int, description: str, idempotency_key: str) -> Dict[str, Any]:
        """Create payment link with mandatory idempotency key."""
        pass

    @abstractmethod
    def retry_payment(self, subscription_id: str, idempotency_key: str) -> Dict[str, Any]:
        """Trigger payment retry for recurring token."""
        pass
```

- **`SimulatorGatewayAdapter`**: Reads/writes to local memory/database. Used for local testing, evaluation, and CI pipelines.
- **`RazorpayGatewayAdapter`**: Instantiates official `razorpay-python` SDK client using `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`. Used when `RAZORPAY_MODE=test` or `live`.
