# ADR-005: LLM Provider Abstraction Layer

## Status
Accepted

## Context
Coupling the system directly to a specific LLM vendor API (OpenAI, Anthropic, Gemini, or local models) introduces vendor lock-in, increases vulnerability to model outages, and complicates benchmark comparison across different models.

## Decision
We decide to implement a unified LLM Provider Adapter interface (`LLMProviderAdapter`) that abstracts model completion calls, structured JSON schema parsing, and prompt invocation.

## Alternatives Considered
1. **Direct OpenAI/Anthropic SDK Calls**: Scattering vendor-specific SDK calls across agent modules. Rejected due to high coupling and vendor lock-in.
2. **Heavyweight Orchestration Frameworks (LangChain/CrewAI)**: Adopting heavy third-party framework abstractions. Rejected as unnecessary dependency bloat.

## Rationale
A lightweight, custom vendor adapter provides clean model swapping (e.g. OpenAI vs Gemini vs local Ollama) without introducing complex third-party dependencies.

## Consequences
- **Positive**: Easy provider switching, consistent structured output validation, zero framework bloat.
- **Negative**: Requires maintaining lightweight internal adapter code for supported model APIs.
