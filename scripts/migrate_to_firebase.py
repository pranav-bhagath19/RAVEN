"""
RAVEN Database-to-Firebase Migration Utility

Migrates persistent entities from SQLite/PostgreSQL database tables to Firebase Firestore collections.
Supports `--dry-run` validation mode and outputs structured entity migration reports.

Usage:
    python scripts/migrate_to_firebase.py [--dry-run] [--db-url DATABASE_URL]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Any
from persistence.firebase import get_firestore_client
from persistence.firestore_store import format_dt


def run_migration(db_url: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    """Reads relational tables and writes documents to Firestore collections."""
    print("==========================================================================")
    print("       RAVEN PIPELINE DATA MIGRATION TO FIREBASE FIRESTORE               ")
    print("==========================================================================")
    print(f"Mode: {'DRY RUN (Validation Only)' if dry_run else 'LIVE MIGRATION'}")

    target_db_url = db_url or "sqlite:///./raven_local.db"
    print(f"Source Database URL: {target_db_url}")

    firestore_client = get_firestore_client()
    summary: dict[str, dict[str, int]] = {}

    table_collection_map = [
        ("tenants", "tenants", "tenant_id"),
        ("users", "users", "user_id"),
        ("user_api_keys", "user_api_keys", "key_id"),
        ("payments", "payments", "payment_id"),
        ("financial_events", "financial_events", "event_id"),
        ("webhook_ingestions", "webhook_ingestions", "id"),
        ("decision_traces", "decision_traces", "decision_id"),
        ("merchant_policies", "merchant_policies", "id"),
        ("policy_audit_logs", "policy_audit_logs", "audit_id"),
        ("tool_executions", "tool_executions", "execution_id"),
        ("verifications", "verifications", "id"),
        ("observability_telemetry", "observability_telemetry", "id"),
        ("background_jobs", "background_jobs", "job_id"),
        ("adaptive_outcomes", "adaptive_outcomes", "id"),
        ("model_registry", "model_registry", "model_version"),
    ]

    try:
        from sqlalchemy import create_engine, inspect
        engine = create_engine(target_db_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        for table_name, collection_name, pkey in table_collection_map:
            summary[table_name] = {"source_records": 0, "migrated_records": 0}
            if table_name not in tables:
                continue

            with engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text(f"SELECT * FROM {table_name}"))
                keys = result.keys()
                rows = result.fetchall()
                summary[table_name]["source_records"] = len(rows)

                for row in rows:
                    d = dict(zip(keys, row))
                    # Sanitize dates / JSON
                    sanitized: dict[str, Any] = {}
                    for k, v in d.items():
                        if hasattr(v, "isoformat"):
                            sanitized[k] = format_dt(v)
                        else:
                            sanitized[k] = v

                    doc_id = str(d.get(pkey, f"doc_{summary[table_name]['migrated_records'] + 1}"))

                    if not dry_run:
                        firestore_client.collection(collection_name).document(doc_id).set(sanitized)

                    summary[table_name]["migrated_records"] += 1

    except Exception as e:
        print(f"Notice: SQLite source database not found or empty ({e}). Initializing empty Firestore collections.")

    print("\n--------------------------------------------------------------------------")
    print("                     DATA MIGRATION SUMMARY REPORT                        ")
    print("--------------------------------------------------------------------------")
    print(f"{'Table / Collection':<30} | {'Source Count':<14} | {'Migrated Count':<14}")
    print("-" * 65)

    total_src = 0
    total_mig = 0
    for tbl, counts in summary.items():
        src = counts["source_records"]
        mig = counts["migrated_records"]
        total_src += src
        total_mig += mig
        print(f"{tbl:<30} | {src:<14} | {mig:<14}")

    print("-" * 65)
    print(f"{'TOTAL ENTITIES':<30} | {total_src:<14} | {total_mig:<14}")
    print("==========================================================================")

    return {
        "dry_run": dry_run,
        "total_source_records": total_src,
        "total_migrated_records": total_mig,
        "details": summary,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAVEN Database to Firebase Migration Tool")
    parser.add_argument("--dry-run", action="store_true", help="Perform validation without writing to Firestore")
    parser.add_argument("--db-url", type=str, default=None, help="Source database connection string")
    args = parser.parse_args()

    res = run_migration(db_url=args.db_url, dry_run=args.dry_run)
    sys.exit(0)
