# RAVEN Security & Compliance Model Specification

## 1. Core Security Principles

Security in RAVEN is built around **Defense in Depth**, **Zero Trust in AI Outputs**, **Strict Least Privilege**, and **Complete Auditability**.

---

## 2. Threat Modeling & Safeguards

| Threat Vector | Potential Impact | RAVEN Safeguard |
| :--- | :--- | :--- |
| **Prompt Injection Attack** | Malicious user attempts to force AI Agent to execute unauthorized retries or issue bogus payment links. | **Deterministic Policy Engine Veto**: AI output cannot execute side-effects directly. Policy engine validates rules independently before issuing ephemeral `PolicyApprovalToken`. |
| **Webhook Spoofing** | Attacker posts fake `payment.captured` webhooks to mark unpaid orders as paid. | **HMAC-SHA256 Signature Verification**: Requests without valid `X-Razorpay-Signature` matching `RAZORPAY_WEBHOOK_SECRET` are rejected at ingestion boundary. |
| **Double Charging / Race Condition** | Concurrent webhooks trigger multiple retries for the same payment. | **Idempotency Key Enforcement**: Side-effect tools require deterministic idempotency keys (`opportunity_id + attempt_count`). Concurrent calls are rejected or deduplicated. |
| **Credential Leakage** | API keys or secrets committed to repository. | **Zero-Secret Codebase Guarantee**: Secrets injected strictly via environment variables (`.env`). Automated CI scans block commits containing secret signatures. |
| **PII Exposure** | Customer phone numbers, emails, or card last4 leaked in application logs or AI prompts. | **Automatic PII Redaction/Masking**: Logging middleware and LLM prompt context builders mask emails (`j***@domain.com`) and phones (`+91******1234`). |

---

## 3. Webhook Signature Verification

Signature check uses `hmac.compare_digest` to prevent side-channel timing analysis:

```python
def verify_webhook_signature(raw_payload: bytes, signature_header: str, secret: str) -> bool:
    if not signature_header or not secret:
        return False
    expected_sig = hmac.new(
        secret.encode('utf-8'),
        raw_payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, signature_header)
```

---

## 4. Policy Approval Token Mechanics

To enforce that side-effect tools (`create_payment_link`, `retry_payment`, `send_recovery_message`) cannot be executed without Policy Engine authorization:

1. **Policy Engine Evaluation**: Checks rules (`POL_001` through `POL_007`).
2. **Token Generation**: If approved, engine signs a cryptographically bound token:
   $$\text{Token} = \text{HMAC-SHA256}(\text{action\_type} \parallel \text{opportunity\_id} \parallel \text{idempotency\_key} \parallel \text{timestamp}, \text{POLICY\_SECRET})$$
3. **Tool Boundary Validation**: The target tool verifies `Token` signature, expiry (\(\le 300\text{ seconds}\)), and idempotency key before dispatching external API requests.

---

## 5. Least Privilege & Tool RBAC

Agents are strictly restricted to role-specific tool permissions:

| Role | Allowed Tool Types | Prohibited Tool Types |
| :--- | :--- | :--- |
| **Root Cause Analyst** | `READ_ONLY` (`get_payment`, `get_payment_history`, `get_failure_patterns`) | `SIDE_EFFECT` (`create_payment_link`, `retry_payment`) |
| **Recovery Planner** | `READ_ONLY`, `DETERMINISTIC_CALCULATION` (`calculate_expected_recovery`, `get_allowed_interventions`) | `SIDE_EFFECT` (Direct tool calls prohibited; outputs candidate proposals only) |
| **Verification Agent** | `READ_ONLY`, `INTERNAL_SYSTEM` (`verify_payment_state`, `verify_recovery`, `record_audit_event`) | `SIDE_EFFECT` |
| **System Dispatcher** | `SIDE_EFFECT` (Executes only when supplied valid `PolicyApprovalToken`) | None |

---

## 6. Immutable Audit Logging

Every operation logs a JSON-structured `AuditEvent` record containing a global correlation `trace_id`. Audit records are append-only. Modification or deletion of audit logs is programmatically disabled.
