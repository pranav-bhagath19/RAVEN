"""
RAVEN Database-Backed API Key Repository Module

Provides persistent storage, SHA-256 hashing, validation, generation, and revocation for API keys.
"""

import hashlib
import secrets
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from persistence.models import UserAPIKeyRecord, UserRecord, utc_now


class APIKeyRepository:
    """Repository managing database-backed API keys and user identities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """Returns SHA-256 hash of a raw API key string."""
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def generate_api_key(
        self,
        tenant_id: str,
        user_id: str,
        name: str,
        role: str = "OPERATIONS_READ",
        expires_at: datetime | None = None,
    ) -> tuple[str, UserAPIKeyRecord]:
        """
        Generates a new secure random API key, hashes it, and saves the record in DB.
        Returns tuple of (raw_api_key, UserAPIKeyRecord).
        The raw_api_key is returned ONLY ONCE upon creation.
        """
        prefix = f"rvn_{role.lower()[:4]}_"
        random_part = secrets.token_urlsafe(24)
        raw_key = f"{prefix}{random_part}"
        key_hash = self.hash_key(raw_key)
        key_id = f"key_{secrets.token_hex(8)}"

        record = UserAPIKeyRecord(
            key_id=key_id,
            user_id=user_id,
            tenant_id=tenant_id,
            name=name,
            key_prefix=prefix[:16],
            key_hash=key_hash,
            role=role,
            revoked=False,
            expires_at=expires_at,
            created_at=utc_now(),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        return raw_key, record

    def validate_api_key(self, raw_key: str) -> UserAPIKeyRecord | None:
        """
        Validates raw API key string against stored SHA-256 hashes.
        Returns UserAPIKeyRecord if valid, non-revoked, and unexpired; else None.
        """
        if not raw_key:
            return None

        target_hash = self.hash_key(raw_key)
        record = (
            self.db.query(UserAPIKeyRecord)
            .filter(UserAPIKeyRecord.key_hash == target_hash, UserAPIKeyRecord.revoked == False)  # noqa: E712
            .first()
        )

        if not record:
            return None

        if record.expires_at:
            now = datetime.now(timezone.utc)
            if record.expires_at < now:
                return None

        return record

    def revoke_api_key(self, key_id: str) -> bool:
        """Revokes an active API key by ID."""
        record = self.db.query(UserAPIKeyRecord).filter(UserAPIKeyRecord.key_id == key_id).first()
        if not record:
            return False
        setattr(record, "revoked", True)
        self.db.commit()
        return True

    def create_user(
        self,
        tenant_id: str,
        email: str,
        password: str,
        role: str = "OPERATIONS_READ",
    ) -> UserRecord:
        """Creates a new persistent User account record."""
        user_id = f"usr_{secrets.token_hex(8)}"
        pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        user = UserRecord(
            user_id=user_id,
            tenant_id=tenant_id,
            email=email,
            hashed_password=pwd_hash,
            role=role,
            is_active=True,
            created_at=utc_now(),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
