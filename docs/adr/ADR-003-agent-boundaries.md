# ADR-003: Agent Boundaries and Trio Isolation

## Status
Accepted

## Context
Adding numerous specialized agents or arbitrary multi-agent hierarchies increases system complexity, latency, non-determinism, and token costs without necessarily improving revenue recovery outcomes.

## Decision
We decide to limit the agent architecture to **exactly three specialized agents**:
1. **Root Cause Analyst**: Synthesizes failure context and issuer error telemetry.
2. **Recovery Planner**: Ranks candidate interventions and estimates expected recovery value.
3. **Verification Agent**: Verifies post-execution financial state against event logs.

Capabilities that do not require semantic reasoning remain internal deterministic services rather than agent tools.

## Alternatives Considered
1. **Single Monolithic Agent**: Combining diagnosis, planning, and verification into a single prompt. Rejected due to prompt complexity and lack of modular reasoning boundaries.
2. **Complex Multi-Agent Swarm (5+ Agents)**: Adding separate agents for communication, routing, and risk scoring. Rejected as unnecessary architectural bloat.

## Rationale
Three agents provide clean separation of concerns (Diagnosis vs Planning vs Verification) while keeping latency and operational complexity minimal.

## Consequences
- **Positive**: Focused prompt design, clear evaluation boundaries, predictable latency.
- **Negative**: Requires strict schema contracts between agent steps.
