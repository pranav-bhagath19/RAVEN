# RAVEN AI Observability & Telemetry Specification

## 1. Overview & Objectives

AI Observability in RAVEN provides real-time visibility into the behavior, performance, cost, and safety of LLM agent invocations. Because AI recommendations directly influence financial workflows, every agent execution produces structured telemetry.

---

## 2. Observable Telemetry Fields

For every agent decision cycle, the system records an **`AgentExecutionTelemetry`** record:

```text
AgentExecutionTelemetry
├── decision_id                             : String (Trace correlation ID)
├── agent_role                              : Enum (ROOT_CAUSE_ANALYST, RECOVERY_PLANNER, VERIFIER)
├── model_provider                          : String (e.g., "openai", "anthropic", "gemini")
├── model_version                           : String (e.g., "gpt-4o-mini-2024-07-18")
├── prompt_template_version                 : String (e.g., "root_cause_v1.2")
├── structured_output_validation_status     : Enum (VALID, RETRY_SUCCESS, VALIDATION_FAILED)
├── tool_calls                              : List[JSON] (Tool names, arguments sanitized)
├── tool_results                            : List[JSON] (Tool output status, sanitized)
├── latency_ms                              : Integer (Total agent invocation latency)
├── token_usage                             : JSON (prompt_tokens, completion_tokens, total_tokens)
├── policy_result                           : Enum (APPROVED, BLOCKED, ESCALATED, NOT_APPLICABLE)
├── final_decision                          : String (Action type or escalation code)
└── outcome                                 : Enum (EXECUTED, SKIPPED, FAILED)
```

---

## 3. Telemetry Processing Pipeline

```
┌───────────────────────────┐
│     Agent Execution       │
└─────────────┬─────────────┘
              │ Structured Output + Metrics
              ▼
┌───────────────────────────┐
│   PII Masking & Sanitizer │  <-- Masks emails, phones, card last4
└─────────────┬─────────────┘
              │ Clean Telemetry Payload
              ▼
┌───────────────────────────┐
│ Append-Only Audit Stream  │  <-- Linked via decision_id
└───────────────────────────┘
```

---

## 4. PII Redaction & Data Protection Rules

To prevent sensitive customer or financial data from leaking into observability logs or third-party telemetry services:

1. **Email Masking**: `john.doe@example.com` $\rightarrow$ `j***e@example.com`
2. **Phone Number Masking**: `+919876543210` $\rightarrow$ `+91******3210`
3. **Card Instrument Masking**: Card numbers are never stored or logged. Instrument references display only card network and last 4 digits (`Visa ending in 4321`).
4. **Token & Key Sanitization**: API keys, webhook secrets, and `PolicyApprovalToken` strings are stripped or replaced with SHA256 hashes (`token_hash`) before logging.
