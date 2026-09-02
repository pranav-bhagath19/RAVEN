"""
RAVEN API Gateway Dependencies Injector

Provides FastAPI dependency providers for WebhookService, OperationsService, PolicyService, AgentOrchestrator, and PolicyEngine.
"""

import os
from functools import lru_cache
from dotenv import load_dotenv
load_dotenv()

from apps.api.operations_service import OperationsService
from apps.api.policy_service import PolicyService
from apps.api.repository import OperationsRepository
from apps.api.webhook_service import WebhookService
from persistence.database import SessionLocal

_shared_repository = OperationsRepository()


@lru_cache()
def get_webhook_service() -> WebhookService:
    """Provides cached singleton WebhookService dependency."""
    svc = WebhookService(ingestion_service=_shared_repository.ingestion_service)
    svc.repository = _shared_repository
    return svc


@lru_cache()
def get_operations_service() -> OperationsService:
    """Provides cached singleton OperationsService dependency."""
    webhook_svc = get_webhook_service()
    return OperationsService(
        repository=_shared_repository,
        ingestion_service=_shared_repository.ingestion_service,
        orchestrator=webhook_svc.orchestrator,
        provider=webhook_svc.provider,
    )


def get_policy_service() -> PolicyService:
    """Provides PolicyService dependency with a database session."""
    db = SessionLocal()
    try:
        return PolicyService(db=db)
    finally:
        db.close()
