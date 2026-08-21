# ADR-001: Deterministic Policy Engine Boundary

## Status
Accepted

## Context
RAVEN uses LLMs for contextual reasoning, root-cause diagnosis, and candidate recovery action generation. However, LLMs are probabilistic models subject to non-deterministic behavior, prompt injection, and potential hallucinations. Allowing an LLM to trigger external side-effects (e.g. retrying payments, sending payment links) without deterministic governance introduces severe commercial and compliance risks, such as double-charging customers or violating communication regulations.

## Decision
We decide that the **Deterministic Policy Engine** holds absolute, non-bypassable veto authority over all AI agent recommendations. Agents generate candidate actions, but cannot execute side-effects directly. Side-effect tools strictly require a cryptographically signed `PolicyApprovalToken` issued by the Policy Engine.

## Alternatives Considered
1. **Direct Agent Side-Effect Execution**: Allowing agents to call external API tools directly based on internal prompt instructions. Rejected due to high risk of hallucinated parameters or prompt injection exploits.
2. **Post-Action Audit Only**: Executing agent actions immediately and auditing them afterwards. Rejected because financial side-effects (double charging) cannot be cleanly undone post-execution.

## Rationale
Separating non-deterministic candidate generation from deterministic policy verification guarantees safety while preserving the cognitive reasoning power of LLMs.

## Consequences
- **Positive**: Eliminates risk of prompt injection or AI hallucination causing unauthorized side-effects.
- **Negative**: Requires explicit policy rule definitions and token verification overhead at tool boundaries.
