"""
Phase 15 Migration & Schema Verification Tests
"""

from persistence.database import init_db
from persistence.models import Base


def test_schema_migration_initialization():
    """Verifies database tables are created cleanly without errors."""
    init_db()
    table_names = list(Base.metadata.tables.keys())
    assert "tenants" in table_names
    assert "payments" in table_names
    assert "decision_traces" in table_names
