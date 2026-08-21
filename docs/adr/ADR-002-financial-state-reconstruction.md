# ADR-002: Financial State Reconstruction from Normalized Event Log

## Status
Accepted

## Context
Payment webhooks and API events in real-world payment ecosystems (e.g. Razorpay, issuing banks) are inherently asynchronous, duplicated, and delivered out-of-order. Webhook arrival order cannot be assumed to match actual financial event sequence order. Relying on mutable state tables updated on naive webhook arrival corrupts payment states.

## Decision
We decide to derive entity status via deterministic state reconstruction from an append-oriented normalized financial event log. Event ordering and state transition decisions depend on canonical event identity, deduplication, metadata, state transition rules, and explicit reconciliation logic—not timestamps alone or arrival order.

## Alternatives Considered
1. **Full Heavyweight Event Sourcing Framework**: Adopting an external event sourcing framework with CQRS and event brokers. Rejected as overly complex for current architecture scope.
2. **Naive In-Place Database Mutations**: Updating payment state directly on webhook receipt. Rejected because out-of-order webhooks corrupt terminal states.

## Rationale
Decoupling state computation from event arrival order guarantees state correctness while keeping implementation lightweight and maintainable without heavyweight framework dependencies.

## Consequences
- **Positive**: Resilient against duplicate, out-of-order, and delayed webhooks.
- **Negative**: Requires state reconstruction logic during event processing cycles.
