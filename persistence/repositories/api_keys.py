"""
RAVEN Database-Backed API Key Repository Module

Firestore-backed repository implementation for API keys and user accounts.
"""

from datetime import datetime
from typing import Any
from persistence.firestore_store import FirestoreAPIKeyRepository
from persistence.models import UserAPIKeyRecord, UserRecord


class APIKeyRepository:
    """Repository managing API keys and user identities backed by Firestore."""

    def __init__(self, db: Any = None) -> None:
        self._store = FirestoreAPIKeyRepository()

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return FirestoreAPIKeyRepository.hash_key(raw_key)

    def generate_api_key(
        self,
        tenant_id: str,
        user_id: str,
        name: str,
        role: str = "OPERATIONS_READ",
        expires_at: datetime | None = None,
    ) -> tuple[str, UserAPIKeyRecord]:
        return self._store.generate_api_key(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            role=role,
            expires_at=expires_at,
        )

    def validate_api_key(self, raw_key: str) -> UserAPIKeyRecord | None:
        return self._store.validate_api_key(raw_key)

    def revoke_api_key(self, key_id: str) -> bool:
        return self._store.revoke_api_key(key_id)

    def create_user(
        self,
        tenant_id: str,
        email: str,
        password: str,
        role: str = "OPERATIONS_READ",
    ) -> UserRecord:
        return self._store.create_user(
            tenant_id=tenant_id,
            email=email,
            password=password,
            role=role,
        )
