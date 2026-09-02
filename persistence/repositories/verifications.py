"""
RAVEN Verification Database Repository

Firestore-backed repository implementation for Verification outcomes.
"""

from typing import Any
from persistence.firestore_store import FirestoreVerificationRepository
from persistence.models import VerificationRecord


class VerificationRepository:
    """Repository for Verification outcomes backed by Firestore."""

    def __init__(self, db: Any = None) -> None:
        self._store = FirestoreVerificationRepository()

    def save_verification(self, verification_data: dict[str, Any]) -> VerificationRecord:
        return self._store.save_verification(verification_data)

    def list_verifications(
        self,
        payment_id: str | None = None,
        recovery_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[VerificationRecord], int]:
        return self._store.list_verifications(
            payment_id=payment_id,
            recovery_type=recovery_type,
            page=page,
            page_size=page_size,
        )
