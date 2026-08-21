# ADR-004: Monetary Representation in Integer Minor Units

## Status
Accepted

## Context
Floating-point representation of monetary amounts (e.g. `10.50`) introduces rounding errors, precision loss, and non-deterministic behavior during mathematical operations, which is unacceptable in financial software.

## Decision
We decide that all monetary values in RAVEN are represented as **integer minor units** (e.g., Indian Rupee `paise`, where `₹100.50` = `10050` paise). Storage types (e.g., 64-bit integer, BigInt, Numeric) will be selected during implementation based on specific database engine choices and domain constraints.

## Alternatives Considered
1. **Floating Point (`float` / `double`)**: Rejected due to rounding errors (e.g., `0.1 + 0.2 != 0.3`).
2. **Fixed Decimal Types (`Decimal`)**: Useful for UI formatting, but integer minor units provide superior performance, portability, and zero-ambiguity storage across APIs and databases.

## Rationale
Integer minor units completely eliminate floating-point rounding errors and ensure exact, deterministic financial arithmetic across all calculation layers.

## Consequences
- **Positive**: Exact monetary arithmetic, zero precision loss.
- **Negative**: Requires explicit conversion to major units (`paise / 100`) for user-facing UI displays.
