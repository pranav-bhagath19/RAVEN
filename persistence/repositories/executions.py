"""
RAVEN Tool Execution Database Repository

Firestore-backed repository implementation for Tool Execution audit logs.
"""

from typing import Any
from persistence.firestore_store import FirestoreToolExecutionRepository
from persistence.models import ToolExecutionRecord


class ExecutionRepository:
    """Repository for Tool Execution audit logs backed by Firestore."""

    def __init__(self, db: Any = None) -> None:
        self._store = FirestoreToolExecutionRepository()

    def save_execution(self, execution_data: dict[str, Any]) -> ToolExecutionRecord:
        return self._store.save_execution(execution_data)

    def list_executions(
        self,
        payment_id: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ToolExecutionRecord], int]:
        return self._store.list_executions(
            payment_id=payment_id,
            tool_name=tool_name,
            status=status,
            page=page,
            page_size=page_size,
        )
