"""
RAVEN Money Value Object

Represents monetary amounts in integer minor units (e.g. paise).
Enforces strict immutability, zero floating-point arithmetic,
and explicit currency matching.
"""

from dataclasses import dataclass
from typing import Any
from domain.exceptions import CurrencyMismatchError, InvalidMoneyError


@dataclass(frozen=True)
class Money:
    """
    Immutable Money Value Object storing integer minor units (e.g., 10000 = ₹100.00).
    """

    amount_minor: int
    currency: str = "INR"

    def __post_init__(self) -> None:
        # Strict integer check: reject floats or boolean types
        if not isinstance(self.amount_minor, int) or isinstance(self.amount_minor, bool):
            raise InvalidMoneyError(
                f"Monetary amount_minor must be an exact integer, got {type(self.amount_minor).__name__}"
            )
        if not isinstance(self.currency, str) or not self.currency:
            raise InvalidMoneyError("Currency must be a non-empty string ISO code")

        normalized_currency = self.currency.strip().upper()
        if len(normalized_currency) != 3 or not normalized_currency.isalpha():
            raise InvalidMoneyError(f"Currency must be a valid 3-letter ISO 4217 code, got '{self.currency}'")

        # Object.__setattr__ required for frozen dataclass post-init attribute normalization
        object.__setattr__(self, "currency", normalized_currency)

    @classmethod
    def from_minor(cls, amount_minor: int, currency: str = "INR") -> "Money":
        """Factory method to construct Money from integer minor units."""
        return cls(amount_minor=amount_minor, currency=currency)

    @classmethod
    def zero(cls, currency: str = "INR") -> "Money":
        """Factory method to construct zero Money in given currency."""
        return cls(amount_minor=0, currency=currency)

    def _check_currency_match(self, other: "Money") -> None:
        if not isinstance(other, Money):
            raise InvalidMoneyError(f"Cannot operate between Money and {type(other).__name__}")
        if self.currency != other.currency:
            raise CurrencyMismatchError(self.currency, other.currency)

    def __add__(self, other: "Money") -> "Money":
        self._check_currency_match(other)
        return Money(amount_minor=self.amount_minor + other.amount_minor, currency=self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check_currency_match(other)
        return Money(amount_minor=self.amount_minor - other.amount_minor, currency=self.currency)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Money):
            return False
        return self.amount_minor == other.amount_minor and self.currency == other.currency

    def __lt__(self, other: "Money") -> bool:
        self._check_currency_match(other)
        return self.amount_minor < other.amount_minor

    def __le__(self, other: "Money") -> bool:
        self._check_currency_match(other)
        return self.amount_minor <= other.amount_minor

    def __gt__(self, other: "Money") -> bool:
        self._check_currency_match(other)
        return self.amount_minor > other.amount_minor

    def __ge__(self, other: "Money") -> bool:
        self._check_currency_match(other)
        return self.amount_minor >= other.amount_minor

    def to_dict(self) -> dict[str, Any]:
        """Returns JSON-serializable dictionary representation."""
        return {"amount_minor": self.amount_minor, "currency": self.currency}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Money":
        """Reconstructs Money from dictionary representation."""
        return cls(amount_minor=data["amount_minor"], currency=data.get("currency", "INR"))
