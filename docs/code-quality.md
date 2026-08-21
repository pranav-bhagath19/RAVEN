# RAVEN Engineering Quality Standards

## 1. Core Engineering Principles

RAVEN adheres to rigorous production-grade engineering standards. Code quality, maintainability, type safety, test validity, and domain clarity are first-class requirements.

---

## 2. Standards & Tooling Compatibility

### 2.1 Python Typing & Static Analysis
- **100% Type Annotation**: All backend Python code must include explicit type hints for parameters, return values, and class attributes.
- **Type Checking Compatibility**: Compatible with **MyPy** (`--strict` mode target) or **Pyright**.
- **No Blanket `Any`**: Using `typing.Any` as a substitute for proper domain modeling or generic types is prohibited unless interfacing with un-typed third-party SDKs.

### 2.2 Formatting & Linting
- **Ruff Compliance**: Code must pass **Ruff** linter checks (PEP 8, pyflakes, pycodestyle, isort rules).
- **Line Length**: Standard 100-character line length limit.

### 2.3 Error Handling
- **No Broad Swallowing**: Broad `try...except Exception:` blocks with silent `return None` or empty `pass` statements are strictly forbidden.
- **Domain Exceptions**: All expected failures must raise explicit, typed domain exceptions:
  - `DuplicateEventError`
  - `PaymentStateConflictError`
  - `PolicyViolationError`
  - `RecoveryActionError`
  - `WebhookSignatureError`
  - `ExternalServiceError`

---

## 3. Test Quality & Verification Criteria

- **Behavioral Tests Over Coverage Percentage**: Test suites must prioritize verifying domain invariants, state machine state transitions, out-of-order event resolution, policy blocks, and idempotency guarantees.
- **No Superficial Assertions**: Meaningless tests such as `assert True` or simple object instantiation checks are forbidden.
- **Pytest Suite**: Fully compatible with `pytest` execution.

---

## 4. Module Boundaries & Anti-Patterns

- **No Dumping Grounds**: Creating generic dumping ground files such as `utils.py`, `helpers.py`, `common.py`, or `misc.py` is forbidden. Helpers must belong to cohesive domain modules (e.g. `domain/payments/validators.py`).
- **No Invented Abstractions**: Speculative design patterns, unnecessary inheritance hierarchies, or premature microservices are forbidden.
