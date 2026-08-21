"""
RAVEN Tool Execution Database Repository
"""

from typing import Any
from sqlalchemy.orm import Session
from persistence.models import ToolExecutionRecord


class ExecutionRepository:
    """SQLAlchemy Repository for Tool Execution audit logs."""

    def __init__(self, db: Session):
        self.db = db

    def save_execution(self, execution_data: dict[str, Any]) -> ToolExecutionRecord:
        """Saves a ToolExecution record."""
        eid = execution_data["execution_id"]
        record = self.db.query(ToolExecutionRecord).filter(ToolExecutionRecord.execution_id == eid).first()
        if not record:
            record = ToolExecutionRecord(**execution_data)
            self.db.add(record)
        else:
            for key, value in execution_data.items():
                if hasattr(record, key):
                    setattr(record, key, value)
        self.db.commit()
        self.db.refresh(record)
        return record

    def list_executions(
        self,
        payment_id: str | None = None,
        tool_name: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ToolExecutionRecord], int]:
        """Returns paginated ToolExecution records."""
        query = self.db.query(ToolExecutionRecord)
        if payment_id:
            query = query.filter(ToolExecutionRecord.payment_id == payment_id)
        if tool_name:
            query = query.filter(ToolExecutionRecord.tool_name == tool_name)
        if status:
            query = query.filter(ToolExecutionRecord.status == status)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(ToolExecutionRecord.executed_at.desc()).offset(offset).limit(page_size).all()
        return items, total
